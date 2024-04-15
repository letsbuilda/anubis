import contextlib
import re
from functools import partial
from operator import attrgetter
from textwrap import dedent
from typing import Literal, NamedTuple, Self

from aiohttp import ClientSession
from discord import (
    AllowedMentions,
    HTTPException,
    Interaction,
    Message,
    NotFound,
    Reaction,
    User,
    enums,
    ui,
)
from discord.ext.commands import Cog, Command, Context, Converter, command, guild_only
from pydis_core.utils import interactions
from pydis_core.utils.regex import FORMATTED_CODE_REGEX, RAW_CODE_REGEX

from bot.bot import Bot
from bot.constants import MODERATION_ROLES, TXT_LIKE_FILES, BaseURLs, Emojis, URLs
from bot.log import get_logger
from bot.utils import send_to_paste_service
from bot.utils.lock import LockedResourceError, lock_arg
from pydis_core.utils.paste_service import PasteFile, send_to_paste_service
from pydis_core.utils import interactions, paste_service

from ._eval import EvalJob, EvalResult
from ._io import FileAttachment

log = get_logger(__name__)

ESCAPE_REGEX = re.compile("[`\u202e\u200b]{3,}")

# The timeit command should only output the very last line, so all other output should be suppressed.
# This will be used as the setup code along with any setup code provided.
TIMEIT_SETUP_WRAPPER = """
import atexit
import sys
from collections import deque

if not hasattr(sys, "_setup_finished"):
    class Writer(deque):
        '''A single-item deque wrapper for sys.stdout that will return the last line when read() is called.'''

        def __init__(self:Self):
            super().__init__(maxlen=1)

        def write(self:Self, string):
            '''Append the line to the queue if it is not empty.'''
            if string.strip():
                self.append(string)

        def read(self:Self):
            '''This method will be called when print() is called.

            The queue is emptied as we don't need the output later.
            '''
            return self.pop()

        def flush(self:Self):
            '''This method will be called eventually, but we don't need to do anything here.'''
            pass

    sys.stdout = Writer()

    def print_last_line():
        if sys.stdout: # If the deque is empty (i.e. an error happened), calling read() will raise an error
            # Use sys.__stdout__ here because sys.stdout is set to a Writer() instance
            print(sys.stdout.read(), file=sys.__stdout__)

    atexit.register(print_last_line) # When exiting, print the last line (hopefully it will be the timeit output)
    sys._setup_finished = None
{setup}
"""

MAX_PASTE_LENGTH = 10_000
# Max to display in a codeblock before sending to a paste service
# This also applies to text files
MAX_OUTPUT_BLOCK_LINES = 10
MAX_OUTPUT_BLOCK_CHARS = 1000

# The Snekbox commands' whitelists and blacklists.
NO_SNEKBOX_CHANNELS = ()
NO_SNEKBOX_CATEGORIES = ()
SNEKBOX_ROLES = ()

REDO_EMOJI = "\U0001f501"  # :repeat:
REDO_TIMEOUT = 30

SupportedPythonVersions = Literal["3.11"]


class FilteredFiles(NamedTuple):
    allowed: list[FileAttachment]
    blocked: list[FileAttachment]


class CodeblockConverter(Converter):
    """Attempts to extract code from a codeblock, if provided."""

    @classmethod
    async def convert(
        cls: type[Self],
        ctx: Context,  # noqa: ARG003 - arguments are passed in by library
        code: str,
    ) -> list[str]:
        """
        Extract code from the Markdown, format it, and insert it into the code template.

        If there is any code block, ignore text outside the code block.
        Use the first code block, but prefer a fenced code block.
        If there are several fenced code blocks, concatenate only the fenced code blocks.

        Return a list of code blocks if any, otherwise return a list with a single string of code.
        """
        if match := list(FORMATTED_CODE_REGEX.finditer(code)):
            blocks = [block for block in match if block.group("block")]

            if len(blocks) > 1:
                codeblocks = [block.group("code") for block in blocks]
                info = "several code blocks"
            else:
                match = match[0] if len(blocks) == 0 else blocks[0]
                code, block, lang, delim = match.group("code", "block", "lang", "delim")
                codeblocks = [dedent(code)]
                if block:
                    info = (f"'{lang}' highlighted" if lang else "plain") + " code block"
                else:
                    info = f"{delim}-enclosed inline code"
        else:
            codeblocks = [dedent(RAW_CODE_REGEX.fullmatch(code).group("code"))]
            info = "unformatted or badly formatted code"

        code = "\n".join(codeblocks)
        log.trace(f"Extracted {info} for evaluation:\n{code}")
        return codeblocks


class PythonVersionSwitcherButton(ui.Button):
    """A button that allows users to re-run their eval command in a different Python version."""

    def __init__(
        self: Self,
        version_to_switch_to: SupportedPythonVersions,
        snekbox_cog: Self,
        ctx: Context,
        job: EvalJob,
    ) -> None:
        self.version_to_switch_to = version_to_switch_to
        super().__init__(
            label=f"Run in {self.version_to_switch_to}",
            style=enums.ButtonStyle.primary,
        )

        self.snekbox_cog = snekbox_cog
        self.ctx = ctx
        self.job = job

    async def callback(self: Self, interaction: Interaction) -> None:
        """
        Tell snekbox to re-run the user's code in the alternative Python version.

        Use a task calling snekbox, as run_job is blocking while it waits for edit/reaction on the message.
        """
        # Defer response here so that the Discord UI doesn't mark this interaction as failed if the job
        # takes too long to run.
        await interaction.response.defer()

        with contextlib.suppress(NotFound):
            # Suppress delete to cover the case where a user re-runs code and very quickly clicks the button.
            # The log arg on send_job will stop the actual job from running.
            await interaction.message.delete()

        await self.snekbox_cog.run_job(
            self.ctx,
            self.job.as_version(self.version_to_switch_to),
        )


class Snekbox(Cog):
    """Safe evaluation of Python code using Snekbox."""

    def __init__(self: Self, bot: Bot) -> None:
        self.bot = bot
        self.jobs = {}

    def build_python_version_switcher_view(
        self: Self,
        current_python_version: SupportedPythonVersions,
        ctx: Context,
        job: EvalJob,  # noqa: ARG002 - temporary
    ) -> interactions.ViewWithUserAndRoleCheck:
        """Return a view that allows the user to change what version of Python their code is run on."""
        alt_python_version: SupportedPythonVersions
        if current_python_version == "3.10":  # noqa: SIM108 - no
            alt_python_version = "3.11"
        else:
            alt_python_version = "3.10"  # noqa: F841 - temporary

        view = interactions.ViewWithUserAndRoleCheck(
            allowed_users=(ctx.author.id,),
            allowed_roles=MODERATION_ROLES,
        )
        # Temp disabled until snekbox multi-version support is complete
        # https://github.com/python-discord/snekbox/issues/158
        # view.add_item(PythonVersionSwitcherButton(alt_python_version, self:Self, ctx, job))
        view.add_item(interactions.DeleteMessageButton())

        return view

    async def post_job(self: Self, job: EvalJob) -> EvalResult:
        """Send a POST request to the Snekbox API to evaluate code and return the results."""
        data = job.to_dict()

        async with self.bot.http_session.post(
            URLs.snekbox_eval_api,
            json=data,
            raise_for_status=True,
        ) as resp:
            return EvalResult.from_dict(await resp.json())

    async def upload_output(self, output: str) -> str | None:
        """Upload the job's output to a paste service and return a URL to it if successful."""
        log.trace("Uploading full output to paste service...")

        file = PasteFile(content=output, lexer="text")
        try:
            paste_response = await send_to_paste_service(
                files=[file],
                http_session=self.bot.http_session,
                paste_url=BaseURLs.paste_url,
            )
            return paste_response.link
        except paste_service.PasteTooLongError:
            return "too long to upload"
        except paste_service.PasteUploadError:
            return "unable to upload"

    @staticmethod
    def prepare_timeit_input(codeblocks: list[str]) -> list[str]:
        """
        Join the codeblocks into a single string, then return the arguments in a list.

        If there are multiple codeblocks, insert the first one into the wrapped setup code.
        """
        args = ["-m", "timeit"]
        setup_code = codeblocks.pop(0) if len(codeblocks) > 1 else ""
        code = "\n".join(codeblocks)

        args.extend(["-s", TIMEIT_SETUP_WRAPPER.format(setup=setup_code), code])
        return args

    async def format_output(
        self: Self,
        output: str,
        max_lines: int = MAX_OUTPUT_BLOCK_LINES,
        max_chars: int = MAX_OUTPUT_BLOCK_CHARS,
        line_nums: bool = True,  # noqa: FBT001,FBT002 - is literally fine
        output_default: str = "[No output]",
    ) -> tuple[str, str | None]:
        """
        Format the output and return a tuple of the formatted output and a URL to the full output.

        Prepend each line with a line number. Truncate if there are over 10 lines or 1000 characters
        and upload the full output to a paste service.
        """
        output = output.rstrip("\n")
        original_output = output  # To be uploaded to a pasting service if needed
        paste_link = None

        if "<@" in output:
            output = output.replace("<@", "<@\u200b")  # Zero-width space

        if "<!@" in output:
            output = output.replace("<!@", "<!@\u200b")  # Zero-width space

        if ESCAPE_REGEX.findall(output):
            paste_link = await self.upload_output(original_output)
            return (
                "Code block escape attempt detected; will not output result",
                paste_link,
            )

        truncated = False
        lines = output.splitlines()

        if len(lines) > 1:
            if line_nums:
                lines = [f"{i:03d} | {line}" for i, line in enumerate(lines, 1)]
            lines = lines[: max_lines + 1]  # Limiting to max+1 lines
            output = "\n".join(lines)

        if len(lines) > max_lines:
            truncated = True
            if len(output) >= max_chars:
                output = f"{output[:max_chars]}\n... (truncated - too long, too many lines)"
            else:
                output = f"{output}\n... (truncated - too many lines)"
        elif len(output) >= max_chars:
            truncated = True
            output = f"{output[:max_chars]}\n... (truncated - too long)"

        if truncated:
            paste_link = await self.upload_output(original_output)

        if output_default and not output:
            output = output_default

        return output, paste_link

    def _filter_files(
        self: Self,
        ctx: Context,
        files: list[FileAttachment],
        blocked_exts: set[str],
    ) -> FilteredFiles:
        """Filter to restrict files to allowed extensions. Return a named tuple of allowed and blocked files lists."""
        # Filter files into allowed and blocked
        blocked = []
        allowed = []
        for file in files:
            if file.suffix in blocked_exts:
                blocked.append(file)
            else:
                allowed.append(file)

        if blocked:
            blocked_str = ", ".join(f.suffix for f in blocked)
            log.info(
                f"User '{ctx.author}' ({ctx.author.id}) uploaded blacklisted file(s) in eval: {blocked_str}",
                extra={"attachment_list": [f.filename for f in files]},
            )

        return FilteredFiles(allowed, blocked)

    @lock_arg("snekbox.send_job", "ctx", attrgetter("author.id"), raise_error=True)
    async def send_job(self: Self, ctx: Context, job: EvalJob) -> Message:  # noqa: PLR0915
        """
        Evaluate code, format it, and send the output to the corresponding channel.

        Return the bot response.
        """
        async with ctx.typing():
            result = await self.post_job(job)
            msg = result.get_message(job)
            error = result.error_message

            if error:
                output, paste_link = error, None
            else:
                log.trace("Formatting output...")
                output, paste_link = await self.format_output(result.stdout)

            msg = f"{ctx.author.mention} {result.status_emoji} {msg}.\n"

            # This is done to make sure the last line of output contains the error
            # and the error is not manually printed by the author with a syntax error.
            if result.stdout.rstrip().endswith("EOFError: EOF when reading a line") and result.returncode == 1:
                msg += "\n:warning: Note: `input` is not supported by the bot :warning:\n"

            # Skip output if it's empty and there are file uploads
            if result.stdout or not result.has_files:
                msg += f"\n```\n{output}\n```"

            if paste_link:
                msg += f"\nFull output: {paste_link}"

            # Additional files error message after output
            if files_error := result.files_error_message:
                msg += f"\n{files_error}"

            # Split text files
            text_files = [f for f in result.files if f.suffix in TXT_LIKE_FILES]
            # Inline until budget, then upload to paste service
            # Budget is shared with stdout, so subtract what we've already used
            budget_lines = MAX_OUTPUT_BLOCK_LINES - (output.count("\n") + 1)
            budget_chars = MAX_OUTPUT_BLOCK_CHARS - len(output)
            for file in text_files:
                file_text = file.content.decode("utf-8", errors="replace") or "[Empty]"
                # Override to always allow 1 line and <= 50 chars, since this is less than a link
                if len(file_text) <= 50 and not file_text.count("\n"):
                    msg += f"\n`{file.name}`\n```\n{file_text}\n```"
                # otherwise, use budget
                else:
                    format_text, link_text = await self.format_output(
                        file_text,
                        budget_lines,
                        budget_chars,
                        line_nums=False,
                        output_default="[Empty]",
                    )
                    # With any link, use it (don't use budget)
                    if link_text:
                        msg += f"\n`{file.name}`\n{link_text}"
                    else:
                        msg += f"\n`{file.name}`\n```\n{format_text}\n```"
                        budget_lines -= format_text.count("\n") + 1
                        budget_chars -= len(file_text)

            filter_cog = self.bot.get_cog("Filtering")
            blocked_exts = set()
            # Include failed files in the scan.
            failed_files = [FileAttachment(name, b"") for name in result.failed_files]
            total_files = result.files + failed_files
            if filter_cog:
                block_output, blocked_exts = await filter_cog.filter_snekbox_output(
                    msg,
                    total_files,
                    ctx.message,
                )
                if block_output:
                    return await ctx.send(
                        "Attempt to circumvent filter detected. Moderator team has been alerted.",
                    )

            # Filter file extensions
            allowed, blocked = self._filter_files(ctx, result.files, blocked_exts)
            blocked.extend(self._filter_files(ctx, failed_files, blocked_exts).blocked)
            # Add notice if any files were blocked
            if blocked:
                blocked_sorted = sorted({f.suffix for f in blocked})
                # Only no extension
                if len(blocked_sorted) == 1 and blocked_sorted[0] == "":
                    blocked_msg = "Files with no extension can't be uploaded."
                # Both
                elif "" in blocked_sorted:
                    blocked_str = ", ".join(ext for ext in blocked_sorted if ext)
                    blocked_msg = (
                        f"Files with no extension or disallowed extensions can't be uploaded: **{blocked_str}**"
                    )
                else:
                    blocked_str = ", ".join(blocked_sorted)
                    blocked_msg = f"Files with disallowed extensions can't be uploaded: **{blocked_str}**"

                msg += f"\n{Emojis.failed_file} {blocked_msg}"

            # Upload remaining non-text files
            files = [f.to_file() for f in allowed if f not in text_files]
            allowed_mentions = AllowedMentions(
                everyone=False,
                roles=False,
                users=[ctx.author],
            )
            view = self.build_python_version_switcher_view(job.version, ctx, job)
            response = await ctx.send(
                msg,
                allowed_mentions=allowed_mentions,
                view=view,
                files=files,
            )
            view.message = response

            log.info(
                f"{ctx.author}'s {job.name} job had a return code of {result.returncode}",
            )
        return response

    async def continue_job(
        self: Self,
        ctx: Context,
        response: Message,
        job_name: str,
    ) -> EvalJob | None:
        """
        Check if the job's session should continue.

        If the code is to be re-evaluated, return the new EvalJob.
        Otherwise, return None if the job's session should be terminated.
        """
        _predicate_message_edit = partial(predicate_message_edit, ctx)
        _predicate_emoji_reaction = partial(predicate_emoji_reaction, ctx)

        with contextlib.suppress(NotFound):
            try:
                _, new_message = await self.bot.wait_for(
                    "message_edit",
                    check=_predicate_message_edit,
                    timeout=REDO_TIMEOUT,
                )
                await ctx.message.add_reaction(REDO_EMOJI)
                await self.bot.wait_for(
                    "reaction_add",
                    check=_predicate_emoji_reaction,
                    timeout=10,
                )

                # Ensure the response that's about to be edited is still the most recent.
                # This could have already been updated via a button press to switch to an alt Python version.
                if self.jobs[ctx.message.id] != response.id:
                    return None

                code = await self.get_code(new_message, ctx.command)
                with contextlib.suppress(HTTPException):
                    await ctx.message.clear_reaction(REDO_EMOJI)
                    await response.delete()

                if code is None:
                    return None

            except TimeoutError:
                with contextlib.suppress(HTTPException):
                    await ctx.message.clear_reaction(REDO_EMOJI)
                return None

            codeblocks = await CodeblockConverter.convert(ctx, code)

            if job_name == "timeit":
                return EvalJob(self.prepare_timeit_input(codeblocks))
            return EvalJob.from_code("\n".join(codeblocks))

        return None

    async def get_code(self: Self, message: Message, command: Command) -> str | None:
        """
        Return the code from `message` to be evaluated.

        If the message is an invocation of the command, return the first argument or None if it
        doesn't exist. Otherwise, return the full content of the message.
        """
        log.trace(f"Getting context for message {message.id}.")
        new_ctx = await self.bot.get_context(message)

        if new_ctx.command is command:
            log.trace(f"Message {message.id} invokes {command} command.")
            split = message.content.split(maxsplit=1)
            code = split[1] if len(split) > 1 else None
        else:
            log.trace(f"Message {message.id} does not invoke {command} command.")
            code = message.content

        return code

    async def run_job(
        self: Self,
        ctx: Context,
        job: EvalJob,
    ) -> None:
        """Handle checks, stats and re-evaluation of a snekbox job."""
        log.info(f"Received code from {ctx.author} for evaluation:\n{job}")

        while True:
            try:
                response = await self.send_job(ctx, job)
            except LockedResourceError:
                await ctx.send(
                    f"{ctx.author.mention} You've already got a job running - please wait for it to finish!",
                )
                return

            # Store the bot's response message id per invocation, to ensure the `wait_for`s in `continue_job`
            # don't trigger if the response has already been replaced by a new response.
            # This can happen when a button is pressed and then original code is edited and re-run.
            self.jobs[ctx.message.id] = response.id

            job = await self.continue_job(ctx, response, job.name)
            if not job:
                break
            log.info(f"Re-evaluating code from message {ctx.message.id}:\n{job}")

    @command(name="eval", aliases=("e",), usage="[python_version] <code, ...>")
    @guild_only()
    async def eval_command(
        self: Self,
        ctx: Context,
        python_version: SupportedPythonVersions | None,
        *,
        code: CodeblockConverter,
    ) -> None:
        """
        Run Python code and get the results.

        This command supports multiple lines of code, including formatted code blocks.
        Code can be re-evaluated by editing the original message within 10 seconds and
        clicking the reaction that subsequently appears.

        The starting working directory `/home`, is a writeable temporary file system.
        Files created, excluding names with leading underscores, will be uploaded in the response.

        If multiple codeblocks are in a message, all of them will be joined and evaluated,
        ignoring the text outside them.

        By default, your code is run on Python 3.11. A `python_version` arg of `3.10` can also be specified.

        We've done our best to make this sandboxed, but do let us know if you manage to find an
        issue with it!
        """
        code: list[str]
        python_version = python_version or "3.11"
        job = EvalJob.from_code("\n".join(code)).as_version(python_version)
        await self.run_job(ctx, job)

    @command(
        name="timeit",
        aliases=("ti",),
        usage="[python_version] [setup_code] <code, ...>",
    )
    @guild_only()
    async def timeit_command(
        self: Self,
        ctx: Context,
        python_version: SupportedPythonVersions | None,
        *,
        code: CodeblockConverter,
    ) -> None:
        """
        Profile Python Code to find execution time.

        This command supports multiple lines of code, including code wrapped inside a formatted code
        block. Code can be re-evaluated by editing the original message within 10 seconds and
        clicking the reaction that subsequently appears.

        If multiple formatted codeblocks are provided, the first one will be the setup code, which will
        not be timed. The remaining codeblocks will be joined together and timed.

        By default, your code is run on Python 3.11. A `python_version` arg of `3.10` can also be specified.

        We've done our best to make this sandboxed, but do let us know if you manage to find an
        issue with it!
        """
        code: list[str]
        python_version = python_version or "3.11"
        args = self.prepare_timeit_input(code)
        job = EvalJob(args, version=python_version, name="timeit")

        await self.run_job(ctx, job)


def predicate_message_edit(ctx: Context, old_msg: Message, new_msg: Message) -> bool:
    """Return True if the edited message is the context message and the content was indeed modified."""
    return new_msg.id == ctx.message.id and old_msg.content != new_msg.content


def predicate_emoji_reaction(ctx: Context, reaction: Reaction, user: User) -> bool:
    """Return True if the reaction REDO_EMOJI was added by the context message author on this message."""
    return reaction.message.id == ctx.message.id and user.id == ctx.author.id and str(reaction) == REDO_EMOJI

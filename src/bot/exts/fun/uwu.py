"""The ancient arts of Uwuification"""

from functools import partial

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context, clean_content
from imsosorry.uwuification import uwuify

from bot.bot import Bot
from bot.utils import helpers, messages


class Uwu(Cog):
    """Cog for the uwu command."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        name="uwu",
        aliases=(
            "uwuwize",
            "uwuify",
        ),
    )
    async def uwu_command(self, ctx: Context, *, text: str | None = None) -> None:
        """
        Echo an uwuified version the passed text.

        Example:
        '.uwu Hello, my name is John' returns something like
        'hewwo, m-my name is j-john nyaa~'.
        """
        # If `text` isn't provided then we try to get message content of a replied message
        text = text or getattr(ctx.message.reference, "resolved", None)
        if isinstance(text, discord.Message):
            embeds = text.embeds
            text = text.content
        else:
            embeds = None

        if text is None:
            # If we weren't able to get the content of a replied message
            raise commands.UserInputError("Your message must have content or you must reply to a message.")

        await clean_content(fix_channel_mentions=True).convert(ctx, text)

        newufy = partial(uwuify, emoji_strength=1.0)

        # Grabs the text from the embed for uwuification
        if embeds:
            embed = messages.convert_embed(newufy, embeds[0])
        else:
            # Parse potential message links in text
            text, embed = await messages.get_text_and_embed(ctx, text)

            # If an embed is found, grab and uwuify its text
            if embed:
                embed = messages.convert_embed(newufy, embed)

        # Adds the text harvested from an embed to be put into another quote block.
        if text:
            converted_text = newufy(text)
            converted_text = helpers.suppress_links(converted_text)
            converted_text = f">>> {converted_text.lstrip('> ')}"
        else:
            converted_text = None

        await ctx.send(content=converted_text, embed=embed)


async def setup(bot: Bot) -> None:
    """Load the uwu cog."""
    await bot.add_cog(Uwu(bot))

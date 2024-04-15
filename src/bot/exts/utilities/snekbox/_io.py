"""I/O File protocols for snekbox."""

from base64 import b64decode, b64encode
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import Self

import regex
from discord import File

# Note discord bot upload limit is 8 MiB per file,
# or 50 MiB for lvl 2 boosted servers
FILE_SIZE_LIMIT = 8 * 1024 * 1024

# Discord currently has a 10-file limit per message
FILE_COUNT_LIMIT = 10


# ANSI escape sequences
RE_ANSI = regex.compile(r"\\u.*\[(.*?)m")
# Characters with a leading backslash
RE_BACKSLASH = regex.compile(r"\\.")
# Discord disallowed file name characters
RE_DISCORD_FILE_NAME_DISALLOWED = regex.compile(r"[^a-zA-Z0-9._-]+")


def sizeof_fmt(num: float, suffix: str = "B") -> str:
    """Return a human-readable file size."""
    num = float(num)
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024:
            num_str = f"{int(num)}" if num.is_integer() else f"{num:3.1f}"
            return f"{num_str} {unit}{suffix}"
        num /= 1024
    num_str = f"{int(num)}" if num.is_integer() else f"{num:3.1f}"
    return f"{num_str} Yi{suffix}"


def normalize_discord_file_name(name: str) -> str:
    """Return a normalized valid discord file name."""
    # Discord file names only allow A-Z, a-z, 0-9, underscores, dashes, and dots
    # https://discord.com/developers/docs/reference#uploading-files
    # Server will remove any other characters, but we'll get a 400 error for \ escaped chars
    name = RE_ANSI.sub("_", name)
    name = RE_BACKSLASH.sub("_", name)
    # Replace any disallowed character with an underscore
    return RE_DISCORD_FILE_NAME_DISALLOWED.sub("_", name)


@dataclass(frozen=True)
class FileAttachment:
    """File Attachment from Snekbox eval."""

    filename: str
    content: bytes

    def __repr__(self: Self) -> str:
        """Return the content as a string."""
        content = f"{self.content[:10]}..." if len(self.content) > 10 else self.content
        return f"FileAttachment(path={self.filename!r}, content={content})"

    @property
    def suffix(self: Self) -> str:
        """Return the file suffix."""
        return PurePosixPath(self.filename).suffix

    @property
    def name(self: Self) -> str:
        """Return the file name."""
        return PurePosixPath(self.filename).name

    @classmethod
    def from_dict(
        cls: type[Self],
        data: dict,
        size_limit: int = FILE_SIZE_LIMIT,
    ) -> Self:
        """Create a FileAttachment from a dict response."""
        size = data.get("size")
        if (size and size > size_limit) or (len(data["content"]) > size_limit):
            msg = "File size exceeds limit"
            raise ValueError(msg)

        content = b64decode(data["content"])

        if len(content) > size_limit:
            msg = "File size exceeds limit"
            raise ValueError(msg)

        return cls(data["path"], content)

    def to_dict(self: Self) -> dict[str, str]:
        """Convert the attachment to a json dict."""
        content = self.content
        if isinstance(content, str):
            content = content.encode("utf-8")

        return {
            "path": self.filename,
            "content": b64encode(content).decode("ascii"),
        }

    def to_file(self: Self) -> File:
        """Convert to a discord.File."""
        name = normalize_discord_file_name(self.name)
        return File(BytesIO(self.content), filename=name)

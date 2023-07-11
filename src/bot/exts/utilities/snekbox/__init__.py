"""Snekbox."""

from bot.bot import Bot

from ._cog import CodeblockConverter, Snekbox
from ._eval import EvalJob, EvalResult

__all__ = ("CodeblockConverter", "Snekbox", "EvalJob", "EvalResult")


async def setup(bot: Bot) -> None:
    """Load the Snekbox cog."""
    # Defer import to reduce side effects from importing the codeblock package.
    from ._cog import Snekbox

    await bot.add_cog(Snekbox(bot))

"""Bot subclass."""

from typing import Self

from pydis_core import BotBase
from sentry_sdk import push_scope

from bot import exts
from bot.log import get_logger

log = get_logger("bot")


class StartupError(Exception):
    """Exception class for startup errors."""

    def __init__(self: Self, base: Exception) -> None:
        super().__init__()
        self.exception = base


class Bot(BotBase):
    """A subclass of `pydis_core.BotBase` that implements bot-specific functions."""

    def __init__(self: Self, *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)

    async def setup_hook(self: Self) -> None:
        """Default async initialisation method for discord.py."""  # noqa: D401
        await super().setup_hook()

        await self.load_extensions(exts)

    async def on_error(self: Self, event: str, *args: list, **kwargs: dict) -> None:
        """Log errors raised in event listeners rather than printing them to stderr."""
        with push_scope() as scope:
            scope.set_tag("event", event)
            scope.set_extra("args", args)
            scope.set_extra("kwargs", kwargs)

            log.exception(f"Unhandled exception in {event}.")

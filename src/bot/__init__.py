from typing import TYPE_CHECKING

from bot import log

if TYPE_CHECKING:
    from bot.bot import Bot

log.setup()

instance: "Bot" = None  # Global Bot instance.

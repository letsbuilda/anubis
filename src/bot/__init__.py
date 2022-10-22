import asyncio
import logging
import sys

import botcore

# Some basic logging to get existing loggers to show
logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("discord").setLevel(logging.INFO)


class Bot(botcore.BotBase):
    """Sample Bot implementation."""

    async def setup_hook(self) -> None:
        """Load extensions on startup."""
        await super().setup_hook()
        asyncio.create_task(self.load_extensions(sys.modules[__name__]))

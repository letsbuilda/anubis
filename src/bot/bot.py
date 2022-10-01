import botcore
from botcore.utils import scheduling

from bot import exts


class Bot(botcore.BotBase):
    """Sample Bot implementation."""

    async def setup_hook(self) -> None:
        """Default async initialisation method for discord.py."""
        await super().setup_hook()

        # This is not awaited to avoid a deadlock with any cogs that have
        # wait_until_guild_available in their cog_load method.
        scheduling.create_task(self.load_extensions(exts))

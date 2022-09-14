import types
import aiohttp

from discord.ext import commands

from bot import exts
from bot.log import get_logger
from bot.utils._extensions import walk_extensions

log = get_logger('bot')

__all__ = ("Bot", "bot")


class Bot(commands.Bot):
    name = "Anubis"

    def __init__(
        self,
        *args,
        http_session: aiohttp.ClientSession,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.http_session = http_session

    async def add_cog(self, cog: commands.Cog) -> None:
        """Add the given ``cog`` to the bot and log the operation."""
        await super().add_cog(cog)
        log.info(f"Cog loaded: {cog.qualified_name}")

    async def load_extensions(self, module: types.ModuleType) -> None:
        """
        Load all the extensions within the given module and save them to ``self.all_extensions``.
        This should be ran in a task on the event loop to avoid deadlocks caused by ``wait_for`` calls.
        """
        # await self.wait_until_guild_available()
        self.all_extensions = walk_extensions(module)

        for extension in self.all_extensions:            
            await self.load_extension(extension)

    async def setup_hook(self) -> None:
        """Default async initialisation method for discord.py."""
        await super().setup_hook()

        await self.load_extensions(exts)

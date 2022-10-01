import asyncio
from os import getenv

import aiohttp
import discord
import dotenv
from discord.ext import commands

import botcore
from . import Bot

dotenv.load_dotenv()
botcore.utils.apply_monkey_patches()

roles = getenv("ALLOWED_ROLES")
roles = [int(role) for role in roles.split(",")] if roles else []

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(
    guild_id=int(getenv("GUILD_ID")),
    http_session=None,  # type: ignore # We need to instantiate the session in an async context
    allowed_roles=roles,
    command_prefix=commands.when_mentioned_or(getenv("PREFIX", "!")),
    intents=intents,
    description="Bot-core test bot.",
)


async def main() -> None:
    """Run the bot."""
    bot.http_session = aiohttp.ClientSession()
    async with bot:
        await bot.start(getenv("BOT_TOKEN"))


asyncio.run(main())

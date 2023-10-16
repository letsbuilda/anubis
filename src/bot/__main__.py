"""Main runner."""

import asyncio

import aiohttp
import discord
from discord.ext import commands
from sqlalchemy.ext.asyncio import create_async_engine

from bot import constants
from bot.bot import Bot

intents = discord.Intents.default()
intents.message_content = True


async def main() -> None:
    """Run the bot."""
    bot = Bot(
        guild_id=constants.Guild.id,
        http_session=aiohttp.ClientSession(),
        allowed_roles=list({discord.Object(id_) for id_ in constants.MODERATION_ROLES}),
        engine=create_async_engine(constants.Bot.database_dsn),
        command_prefix=commands.when_mentioned,
        intents=intents,
    )

    async with bot:
        await bot.start(constants.Bot.token)


if __name__ == "__main__":
    asyncio.run(main())

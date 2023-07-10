"""Main runner."""

import asyncio
from os import getenv

import aiohttp
import discord
from discord.ext import commands

from bot import constants
from bot.bot import Bot

roles = getenv("ALLOWED_ROLES")
roles = [int(role) for role in roles.split(",")] if roles else []

intents = discord.Intents.default()
intents.message_content = True


async def main() -> None:
    """Run the bot."""
    bot = Bot(
        guild_id=constants.Guild.id,
        http_session=aiohttp.ClientSession(),
        allowed_roles=roles,
        command_prefix=commands.when_mentioned,
        intents=intents,
    )

    async with bot:
        await bot.start(constants.Bot.token)


if __name__ == "__main__":
    asyncio.run(main())

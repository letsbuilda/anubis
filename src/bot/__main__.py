import asyncio
from os import getenv
import aiohttp
import discord
from discord.ext.commands import when_mentioned_or

import bot
from bot.bot import Bot
from bot.log import get_logger


async def main() -> None:
    """Entry async method for starting the bot."""
    intents = discord.Intents.default()
    intents.message_content = True

    async with aiohttp.ClientSession() as session:
        bot.instance = Bot(
            command_prefix=when_mentioned_or("!"),
            intents=intents,
            http_session=session,
        )
        async with bot.instance as _bot:
            await _bot.start(getenv("ANUBIS_TOKEN"))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exception:
        log = get_logger("bot")
        log.exception(exception)

        exit(69)

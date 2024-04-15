"""Main runner."""

import asyncio

import aiohttp
import discord
from discord.ext import commands

from bot import constants
from bot.bot import Bot
from bot.log import setup_sentry


async def main() -> None:
    """Run the bot."""
    setup_sentry()

    allowed_roles = list({discord.Object(id_) for id_ in constants.MODERATION_ROLES})
    intents = discord.Intents.default()
    intents.message_content = True

    bot = Bot(
        guild_id=constants.Guild.id,
        http_session=aiohttp.ClientSession(),
        allowed_roles=allowed_roles,
        command_prefix=commands.when_mentioned_or(constants.Bot.prefix),
        intents=intents,
    )

    async with bot:
        await bot.start(constants.Bot.token)


if __name__ == "__main__":
    asyncio.run(main())

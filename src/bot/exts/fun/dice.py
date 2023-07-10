"""Dice rolling."""

from random import randint

import discord
from discord import app_commands
from discord.ext import commands

from bot.bot import Bot


class Dice(commands.Cog):
    """Roll dice."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @app_commands.command(name="roll")
    async def roll(self, interaction: discord.Interaction, number_of_dice: int, number_of_sides: int) -> None:
        """Roll dice."""
        rolls = ", ".join([str(randint(1, number_of_sides)) for _ in range(number_of_dice)])
        await interaction.response.send_message(rolls)


async def setup(bot: Bot) -> None:
    """Load the Ping cog."""
    await bot.add_cog(Dice(bot))

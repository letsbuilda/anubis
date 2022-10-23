from random import randint

from discord.ext import commands

from bot.bot import Bot


class Dice(commands.Cog):
    """Roll dice."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="roll", help="Roll dice")
    async def roll(self, ctx: commands.Context, number_of_dice: int, number_of_sides: int) -> None:
        """Roll dice."""
        await ctx.send(", ".join([str(randint(1, number_of_sides)) for _ in range(number_of_dice)]))


async def setup(bot: Bot) -> None:
    """Load the Ping cog."""
    await bot.add_cog(Dice(bot))

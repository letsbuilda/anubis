from discord.ext import commands

from bot.bot import Bot


class Cog(commands.Cog):
    """A simple discord.py cog."""

    def __init__(self, _bot: Bot):
        self.bot = _bot

    @commands.command()
    async def sentry_test(self, ctx: commands.Context) -> None:
        """Fail to test sentry"""
        maths = str(1 / 0)
        await ctx.send(maths)

    @commands.command()
    async def reload(self, ctx: commands.Context) -> None:
        """Reload all available cogs."""
        message = await ctx.send(":hourglass_flowing_sand: Reloading")
        for ext in list(self.bot.extensions):
            await self.bot.reload_extension(ext)
        await message.edit(content=":white_check_mark: Done")


async def setup(_bot: Bot) -> None:
    """Install the cog."""
    await _bot.add_cog(Cog(_bot))

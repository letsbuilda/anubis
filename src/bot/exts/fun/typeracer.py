"""Typeracer game."""

from asyncio import TimeoutError
from collections import defaultdict
from typing import Self

from discord import Colour, Embed, Message
from discord.ext import commands
from discord.ext.commands import BucketType, Context
from wonderwords import RandomWord

from bot.bot import Bot


class Race:
    """Class to manage each typerace."""

    def __init__(self: Self, ctx: Context, number_of_words: int) -> None:
        self.ctx = ctx
        self.word_generator = RandomWord()
        self.word_list = self.word_generator.random_words(number_of_words)
        self.i = 0
        self.scores = defaultdict(int)
        self.players = defaultdict(str)

    def _next_word(self: Self) -> None:
        """Get the next word."""
        self.i += 1

    def _word_display(self: Self) -> str:
        """Return word to display with Zero Width Space inserted to prevent copy pasting."""
        return "\u200b".join(self.word_list[self.i])

    def _update_scoreboard(self: Self, user_id: int, username: str) -> None:
        """Update the scoreboard."""
        self.players[user_id] = username
        self.scores[user_id] += 1

    def game_over(self: Self) -> bool:
        """Check if the game is over."""
        return self.i >= len(self.word_list)

    def word_embed(self: Self) -> Embed:
        """Build the word embed."""
        embed = Embed(title="The word is:", description=f"`{self._word_display()}`", colour=Colour.yellow())
        embed.set_footer(text=f"{self.i+1}/{len(self.word_list)}")
        return embed

    def is_correct(self: Self, answer: str) -> bool:
        """Check if the answer is correct."""
        return answer == self.word_list[self.i]

    def is_copypaste(self: Self, answer: str) -> bool:
        """Check if answer is copypasted."""
        return answer == self._word_display()

    def check_message(self: Self, message: Message) -> bool:
        """Check function for processing valid inputs."""
        return (
            message.content == self.word_list[self.i] or message.content == self._word_display()
        ) and message.channel == self.ctx.channel

    def scoreboard_embed(self: Self) -> Embed:
        """Build the scoreboard embed."""
        embed = Embed(title="Final Scoreboard", colour=Colour.blue())
        scoreboard_list = [(self.players[user_id], self.scores[user_id]) for user_id in self.players]
        scoreboard_list = sorted(scoreboard_list, key=lambda pair: pair[1], reverse=True)
        prev = None
        offset = 0
        for i, pair in enumerate(scoreboard_list):
            username = pair[0]
            score = pair[1]
            if score == prev:
                offset += 1
            else:
                offset = 0
            prev = score
            embed.add_field(name=f"{i+1-offset}. {username}", value=f"**{score} words**", inline=False)
        return embed

    def process_correct_answer(self: Self, message: Message) -> Embed:
        """Process if the answer is correct."""
        user_id = message.author.id
        username = message.author.name
        icon_url = message.author.avatar.url
        embed = Embed(title="The word was:", description=self.word_list[self.i], colour=Colour.green())
        embed.set_author(name=f"{username} got it right!", icon_url=icon_url)
        embed.set_footer(text=f"{self.i+1}/{len(self.word_list)}")
        self._update_scoreboard(user_id, username)
        self._next_word()
        return embed


class Typeracer(commands.Cog):
    """Play typeracer."""

    def __init__(self: Self, bot: Bot) -> None:
        self.bot = bot

    @commands.command(name="typeracer")
    @commands.max_concurrency(1, per=BucketType.channel)
    async def typeracer(self: Self, ctx: Context, number_of_words: int = 5) -> None:
        """Play Typeracer.

        Number of words defaults to 5 if not specified.
        Max number of words is 30.
        """
        if number_of_words < 1 or number_of_words > 30:
            msg = "Number of words must be between 1 and 30."
            raise commands.UserInputError(msg)

        race = Race(ctx, number_of_words)
        await ctx.send("*The race has started!\nThe word to type is...*")

        while not race.game_over():
            # sending typeracer word
            embed = race.word_embed()
            message = await ctx.send(embed=embed)
            try:
                # only process messages that satisfy the check function
                answer = await self.bot.wait_for("message", check=race.check_message, timeout=30)
            except TimeoutError:
                await message.edit(content=message.content + "\n\nThe game has timed out!")
                # display scoreboard if game times out
                if race.scores:
                    await ctx.send(embed=race.scoreboard_embed())
                return
            else:
                # check if answer is correct OR copy pasted
                if race.is_correct(answer.content):
                    embed = race.process_correct_answer(answer)
                    await message.edit(embed=embed)
                elif race.is_copypaste(answer.content):
                    await ctx.send(f"{answer.author.mention} No copy & pasting!")

        # send final scoreboard
        await ctx.send(embed=race.scoreboard_embed())


async def setup(bot: Bot) -> None:
    """Load the Typeracer cog."""
    await bot.add_cog(Typeracer(bot))

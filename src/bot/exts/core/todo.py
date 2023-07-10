"""Todo list"""

from discord import Embed
from discord.ext import commands
from sqlalchemy.dialects.postgresql import insert

from bot.bot import Bot
from bot.database.models import Users


class Todo(commands.Cog):
    """Todo list commands."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(name="todo")
    async def todo(self, ctx: commands.Context) -> None:
        """Todo commands."""
        # Add user to db
        query = insert(Users).values(user_id=ctx.author.id)
        query = query.on_conflict_do_nothing(index_elements=["user_id"])
        self.bot.db.execute(query)
        self.bot.db.commit()

        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @todo.command(name="list", aliases=("l",))
    async def list(self, ctx: commands.Context) -> None:
        """Get your todo list."""
        user = self.bot.db.query(Users).where(Users.user_id == ctx.author.id).one()
        todo_list = user.todo_list

        task_number = 1
        description = ""
        if todo_list:
            description = f"{task_number}. " + "\n- ".join(todo_list)
            task_number += 1

        embed = Embed(
            title=f"{ctx.author.name}'s Todo List",
            colour=ctx.author.color,
            description=description,
        )
        await ctx.send(embed=embed)

    @todo.command(name="add", aliases=("a",))
    async def add(self, ctx: commands.Context, *, text: str | None = None) -> None:
        """Add a task to your todo list."""
        if text is None:
            raise commands.UserInputError("Your message must have content.")
        user = self.bot.db.query(Users).where(Users.user_id == ctx.author.id).one()
        user.todo_list.append(text)
        self.bot.db.commit()
        await ctx.send(f"New task `{text}` added to todo-list.")

    @todo.command(name="remove", aliases=("r", "rm"))
    async def remove(self, ctx: commands.Context, task_number: int | None = None) -> None:
        """Remove a task from your todo list."""
        if task_number is None:
            raise commands.UserInputError("You must specify a task to remove.")

        user = self.bot.db.query(Users).where(Users.user_id == ctx.author.id).one()

        if len(user.todo_list) < task_number:
            raise commands.UserInputError("Task number out of bound.")

        task = user.todo_list[task_number - 1]
        user.todo_list.pop(task_number - 1)
        self.bot.db.commit()
        await ctx.send(f"Task `{task}` removed from todo-list.")


async def setup(bot: Bot) -> None:
    """Load the Todo cog."""
    await bot.add_cog(Todo(bot))

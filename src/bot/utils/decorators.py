import logging
from typing import Callable

from discord.ext import commands
from discord.ext.commands import Context
from sqlalchemy import select

from bot.database import session
from bot.database.models import Permissions, RolesPermissions

log = logging.getLogger(__name__)


def with_permission(permission: Permissions) -> Callable:
    async def predicate(ctx: Context) -> bool:
        if not ctx.guild:  # Return False in a DM
            log.debug(
                f"{ctx.author} tried to use the '{ctx.command.name}'command from a DM. "
                "This command is restricted by the with_permission decorator. Rejecting request."
            )
            return False

        permissions_roles_query = session.execute(
            select(RolesPermissions.role_id)
            .where(RolesPermissions.permission == permission.value)
            .where(RolesPermissions.guild_id == 956987833028083712)
        )
        permissions_roles = permissions_roles_query.scalars().all()

        if any(permissions_role in ctx.author.roles for permissions_role in permissions_roles):
            log.debug(f"{ctx.author} has the '{permission}' permission, and passes the check.")
            return True

        log.debug(
            f"{ctx.author} does not have the required permission to use "
            f"the '{ctx.command.name}' command, so the request is rejected."
        )
        return False

    return commands.check(predicate)

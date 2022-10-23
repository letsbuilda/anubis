"""Database models"""
from enum import Enum

from sqlalchemy import BigInteger, Column, Text, select
from sqlalchemy.ext.declarative import declarative_base

from bot.database import session

Base = declarative_base()


class Guild(Base):
    """A Discord guild"""

    __tablename__ = "guilds"

    guild_id = Column(BigInteger, primary_key=True)
    name = Column(Text)
    github_organization = Column(Text)


class Permissions(Enum):
    CAN_INTERNAL_EVAL = "can_internal_eval"


class RolesPermissions(Base):
    """RolesPermissions"""

    __tablename__ = "roles_permissions"

    roles_permissions_id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger)
    role_id = Column(BigInteger)
    permission = Column(Text)


if __name__ == "__main__":
    result = session.execute(
        select(RolesPermissions.role_id)
        .where(RolesPermissions.permission == "can_internal_eval")
        .where(RolesPermissions.guild_id == 956987833028083712)
    )

    print(result.scalars().all())

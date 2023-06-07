"""Database functions"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from bot.constants import Bot


engine = create_engine(
    Bot.database_url,
    future=True,
)

session: scoped_session = scoped_session(
    sessionmaker(
        bind=engine,
        future=True,
    )
)

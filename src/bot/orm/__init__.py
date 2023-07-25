"""Database functions."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.constants import Bot

engine = create_engine(Bot.database_dsn)
Session = sessionmaker(engine)

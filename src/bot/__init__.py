"""Anubis, a fancy Discord bot."""

import logging
from os import getenv

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from bot import log

sentry_logging = LoggingIntegration(level=logging.DEBUG, event_level=logging.WARNING)

sentry_sdk.init(
    dsn=getenv("BOT_SENTRY_DSN"),
    integrations=[
        sentry_logging,
    ],
    release=f"anubis@{getenv('GIT_SHA', 'development')}",
    traces_sample_rate=0.5,
    profiles_sample_rate=0.5,
)

log.setup()

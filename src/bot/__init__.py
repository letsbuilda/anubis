"""Anubis, a fancy Discord bot."""

import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from bot import log
from bot.constants import GIT_SHA, Sentry

sentry_logging = LoggingIntegration(level=logging.DEBUG, event_level=logging.WARNING)

sentry_sdk.init(
    dsn=Sentry.dsn,
    integrations=[
        sentry_logging,
    ],
    release=f"{Sentry.release_prefix}@{GIT_SHA}",
    traces_sample_rate=0.5,
    profiles_sample_rate=0.5,
)

log.setup()

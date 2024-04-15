"""Anubis, a fancy Discord bot."""

from pydis_core.utils import apply_monkey_patches

from bot import log

log.setup()

apply_monkey_patches()

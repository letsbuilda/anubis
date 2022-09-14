import logging
from logging import Logger, handlers
from pathlib import Path
from typing import TYPE_CHECKING, cast

TRACE_LEVEL = 5

if TYPE_CHECKING:
    LoggerClass = Logger
else:
    LoggerClass = logging.getLoggerClass()


class CustomLogger(LoggerClass):
    """Custom implementation of the `Logger` class with an added `trace` method."""

    def trace(self, msg: str, *args, **kwargs) -> None:
        """
        Log 'msg % args' with severity 'TRACE'.
        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.
        logger.trace("Houston, we have an %s", "interesting problem", exc_info=1)
        """
        if self.isEnabledFor(TRACE_LEVEL):
            self.log(TRACE_LEVEL, msg, *args, **kwargs)


def get_logger(name: str | None = None) -> CustomLogger:
    """Utility to make mypy recognise that logger is of type `CustomLogger`."""
    return cast(CustomLogger, logging.getLogger(name))


def setup() -> None:
    """Set up loggers."""
    logging.TRACE = TRACE_LEVEL
    logging.addLevelName(TRACE_LEVEL, "TRACE")
    logging.setLoggerClass(CustomLogger)
    root_log = get_logger()

    format_string = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    log_format = logging.Formatter(format_string)

    log_file = Path("logs", "bot.log")
    log_file.parent.mkdir(exist_ok=True)
    file_handler = handlers.RotatingFileHandler(
        log_file, maxBytes=5242880, backupCount=7, encoding="utf8"
    )
    file_handler.setFormatter(log_format)
    root_log.addHandler(file_handler)

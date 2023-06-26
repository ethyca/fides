"""
Defines the logging format and other helper functions to be used throughout the API server code.
"""
# pylint: disable=eval-used,no-member

from __future__ import annotations

import logging
import sys
from types import FrameType
from typing import Dict, List, Optional, Union

from loguru import logger

from fides.config import CONFIG

MASKED = "MASKED"


class Pii(str):
    """Mask pii data"""

    def __format__(self, __format_spec: str) -> str:
        if CONFIG.logging.log_pii:
            return super().__format__(__format_spec)
        return MASKED


def _log_exception(exc: BaseException, dev_mode: bool = False) -> None:
    """If dev mode, log the entire traceback"""
    if dev_mode:
        logger.opt(exception=True).error(exc)
    else:
        logger.error(exc)


def _log_warning(exc: BaseException, dev_mode: bool = False) -> None:
    """If dev mode, log the entire traceback"""
    if dev_mode:
        logger.opt(exception=True).warning(exc)
    else:
        logger.error(exc)


class FidesAPIHandler(logging.Handler):
    """
    The logging.Handler used by the api logger.
    """

    def __init__(
        self,
        level: Union[int, str],
        include_extra: bool = False,
        serialize: str = "",
        sink: str = "",
    ) -> None:
        super().__init__(level=level)
        self.loguru_vals: Dict = {
            "level": level,
            "serialize": serialize == "json",
            "sink": sys.stdout if sink == "" else sink,
        }

        format_module = ""
        if level == logging.DEBUG or level == logging.getLevelName(logging.DEBUG):
            format_module = " (<c>{module}:{function}:{line}</c>)"

        format_extra = ""
        self.loguru_vals["filter"] = "lambda logRecord: not bool(logRecord['extra'])"
        if include_extra:
            format_extra = " | {extra}"
            self.loguru_vals["filter"] = "lambda logRecord: bool(logRecord['extra'])"

        self.loguru_vals["format"] = (
            "<d>{time:YYYY-MM-DD HH:mm:ss.SSS}</d> [<lvl>{level}</lvl>]%s: {message}%s"
            % (format_module, format_extra)
        )

    def emit(self, record: logging.LogRecord) -> None:
        """
        Log the specified record.
        """
        # Get corresponding Loguru level if it exists
        level: Union[int, str]
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Determine the caller that originated the log entry
        frame: Optional[FrameType] = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

    def loguru_config(self) -> Dict:
        """
        Returns only the fields required to pass a FidesAPIHandler
        as a handler kwarg in Loguru's logger.configure().
        """
        return {
            "level": self.loguru_vals["level"],
            "filter": eval(self.loguru_vals["filter"]),
            "format": self.loguru_vals["format"],
            "serialize": self.loguru_vals["serialize"],
            "sink": self.loguru_vals["sink"],
        }


def setup(level: str, serialize: str = "", desination: str = "") -> None:
    """
    Removes all handlers from all loggers, and sets those
    loggers to propagate log entries to the root logger.
    Then, configures Loguru to use the desired handlers.

    This should be one of the last function calls made, as
    the addition of any new loggers afterwards will require
    it to be run again.
    """
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    logger.configure(
        handlers=[
            FidesAPIHandler(
                level, sink=desination, serialize=serialize
            ).loguru_config(),
            FidesAPIHandler(
                level, include_extra=True, sink=desination, serialize=serialize
            ).loguru_config(),
        ]
    )


def obfuscate_message(message: str) -> str:
    """
    Obfuscate specific bits of information that might get logged.

    Currently being obfuscated:
        - Database username + password
    """

    strings_to_replace: List[str] = [
        f"{CONFIG.database.user}:{CONFIG.database.password}"
    ]

    for string in strings_to_replace:
        result = message.replace(string, "*****")

    return result


# Loguru doesn't export the Record type so this can't be properly typed
# Taken from the following issue:
# https://github.com/Delgan/loguru/issues/537#issuecomment-986259036
def format_and_obfuscate(record) -> str:  # type: ignore[no-untyped-def]
    record["extra"]["obfuscated_message"] = obfuscate_message(record["message"])
    return "[{level}] {extra[obfuscated_message]}\n{exception}"

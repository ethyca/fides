"""
Defines the logging format and other helper functions to be used throughout the API server code.
"""

# pylint: disable=eval-used,no-member

from __future__ import annotations

import logging
import sys
from typing import Dict, List

from loguru import logger

from fides.config import CONFIG, FidesConfig

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


def create_handler_dicts(
    level: str, sink: str, serialize: bool, colorize: bool, include_called_from: bool
) -> List[Dict]:
    """
    Creates dictionaries used for configuring loguru handlers.

    Two dictionaries are returned, one for standard logs and another to handle
    logs that include "extra" information.
    """
    time_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    level_format = "<level>{level: <8}</level>"
    called_from_format = (
        ("<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>")
        if include_called_from
        else ""
    )
    message_format = "<level>{message}</level>"

    log_format = (
        time_format
        + " | "
        + level_format
        + " | "
        + called_from_format
        + " - "
        + message_format
    )

    standard_dict = {
        "colorize": colorize,
        "format": log_format,
        "level": level,
        "serialize": serialize,
        "sink": sys.stdout if sink == "" else sink,
        "filter": lambda logRecord: not bool(logRecord["extra"]),
        "diagnose": False,
        "backtrace": True,
        "catch": True,
    }
    extra_dict = {
        **standard_dict,
        "format": log_format + " | {extra}",
        "filter": lambda logRecord: bool(logRecord["extra"]),
    }
    return [standard_dict, extra_dict]


def setup(config: FidesConfig) -> None:
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

    handlers = create_handler_dicts(
        level=config.logging.level,
        include_called_from=config.dev_mode,
        sink=config.logging.destination,
        serialize=config.logging.serialization == "json",
        colorize=config.logging.colorize,
    )
    logger.configure(handlers=handlers)


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

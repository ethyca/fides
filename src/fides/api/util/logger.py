"""
Defines the logging format and other helper functions to be used throughout the API server code.
"""

# pylint: disable=eval-used,no-member

from __future__ import annotations

import logging
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from enum import Enum

from loguru import logger

from fides.config import CONFIG, FidesConfig

MASKED = "MASKED"


class SinkType(str, Enum):
    """Enum for supported logging sink types"""
    FILE = "file"
    REDIS = "redis"
    STDOUT = ""  # Empty string for backwards compatibility


class LogSink(ABC):
    """Abstract base class for log sinks"""
    @abstractmethod
    def get_sink_config(self,
        level: str,
        colorize: bool,
        serialize: bool,
        include_called_from: bool,
        format_string: str
    ) -> Dict[str, Any]:
        """Returns the sink configuration dictionary"""
        pass


class StdoutSink(LogSink):
    def get_sink_config(self,
        level: str,
        colorize: bool,
        serialize: bool,
        include_called_from: bool,
        format_string: str
    ) -> Dict[str, Any]:
        return {
            "sink": sys.stdout,
            "colorize": colorize,
            "format": format_string,
            "level": level,
            "serialize": serialize,
            "diagnose": False,
            "backtrace": True,
            "catch": True,
            "filter": lambda logRecord: not bool(logRecord["extra"]),
        }


class RedisSink(LogSink):
    """Redis sink implementation"""
    def get_sink_config(self,
        level: str,
        colorize: bool,
        serialize: bool,
        include_called_from: bool,
        format_string: str
    ) -> Dict[str, Any]:
        from fides.api.util.logger_redis_sink import RedisLogSink
        return {
            "sink": RedisLogSink(),
            "colorize": False,  # Redis doesn't need colorization
            "format": format_string,
            "level": level,
            "serialize": True,  # Always serialize for Redis
            "diagnose": False,
            "backtrace": True,
            "catch": True,
        }


class FileSink(LogSink):
    def __init__(self, path: str):
        self.path = path

    def get_sink_config(self,
        level: str,
        colorize: bool,
        serialize: bool,
        include_called_from: bool,
        format_string: str
    ) -> Dict[str, Any]:
        return {
            "sink": self.path,
            "colorize": colorize,
            "format": format_string,
            "level": level,
            "serialize": serialize,
            "diagnose": False,
            "backtrace": True,
            "catch": True,
            "filter": lambda logRecord: not bool(logRecord["extra"]),
        }


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


def get_sink(sink_type: str, **kwargs) -> LogSink:
    """Factory function to create appropriate sink"""
    try:
        sink_enum = SinkType(sink_type)
        if sink_enum == SinkType.STDOUT:
            return StdoutSink()
        elif sink_enum == SinkType.REDIS:
            return RedisSink()
        elif sink_enum == SinkType.FILE:
            return FileSink(kwargs.get('path', ''))
        raise ValueError(f"Unsupported sink type: {sink_type}")
    except ValueError as e:
        logger.warning(f"Invalid sink type '{sink_type}', falling back to stdout")
        return StdoutSink()


def create_handler_dicts(
    level: str,
    sink: str,
    serialize: bool,
    colorize: bool,
    include_called_from: bool
) -> List[Dict]:
    """
    Creates dictionaries used for configuring loguru handlers.
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

    # Get the appropriate sink
    log_sink = get_sink(sink)

    # Get base configuration from sink
    standard_dict = log_sink.get_sink_config(
        level=level,
        colorize=colorize,
        serialize=serialize,
        include_called_from=include_called_from,
        format_string=log_format
    )

    # Create extra dict with additional formatting for logs with extra context
    extra_dict = {
        **standard_dict,
        "format": log_format + " | <dim>{extra}</dim>",
        "filter": lambda logRecord: bool(logRecord["extra"]),
    }

    return [standard_dict, extra_dict]


def setup(config: FidesConfig) -> None:
    """
    Configures logging with the appropriate sink based on configuration.
    Removes all handlers from all loggers, and sets those loggers to propagate
    log entries to the root logger. Then, configures Loguru to use the desired handlers.
    """
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Configure main sink from config
    handlers = create_handler_dicts(
        level=config.logging.level,
        include_called_from=config.dev_mode,
        sink=config.logging.destination,
        serialize=config.logging.serialization == "json",
        colorize=config.logging.colorize,
    )

    # Add Redis sink if Redis is enabled
    if config.redis.enabled:
        redis_handlers = create_handler_dicts(
            level=config.logging.level,
            include_called_from=config.dev_mode,
            sink=SinkType.REDIS,
            serialize=True,  # Always serialize for Redis
            colorize=False,  # Redis doesn't need colorization
        )
        handlers.extend(redis_handlers)

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

"""
Defines the logging format to be used throughout the fidesapi server code.
"""
# pylint: disable=eval-used,no-member

import logging
import sys
from typing import Dict, Union

from loguru import logger


class FidesAPIHandler(logging.Handler):
    """
    The logging.Handler used by the fidesapi logger.
    """

    def __init__(
        self,
        level: Union[int, str],
        include_extra: bool = False,
        serialize: str = "",
        sink: str = "",
    ) -> None:
        super().__init__(level=level)
        self.level = level
        self.serialize = serialize == "json"
        self.sink = sys.stdout if sink == "" else sink

        format_module = ""
        if level == logging.DEBUG or level == logging.getLevelName(logging.DEBUG):
            format_module = " (<c>{module}:{function}:{line}</c>)"

        format_extra = ""
        self.filter = "lambda logRecord: not bool(logRecord['extra'])"
        if include_extra:
            format_extra = " | {extra}"
            self.filter = "lambda logRecord: bool(logRecord['extra'])"

        self.format = (
            "<d>{time:YYYY-MM-DD HH:mm:ss.SSS}</d> [<lvl>{level}</lvl>]%s: {message}%s"
            % (format_module, format_extra)
        )

    def emit(self, record: logging.LogRecord) -> None:
        """
        Log the specified record.
        """
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Determine the caller that originated the log entry
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
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
            "level": self.level,
            "filter": eval(self.filter),
            "format": self.format,
            "serialize": self.serialize,
            "sink": self.sink,
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

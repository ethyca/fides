"""
Defines the logging format and other helper functions to be used throughout the API server code.
"""

# pylint: disable=eval-used,no-member

from __future__ import annotations

import logging
import os
import sys
from contextlib import contextmanager
from types import FrameType
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional

from loguru import logger
from loguru._handler import Message

from fides.api.schemas.privacy_request import LogEntry, PrivacyRequestSource
from fides.api.util.sqlalchemy_filter import SQLAlchemyGeneratedFilter
from fides.config import CONFIG, FidesConfig

if TYPE_CHECKING:
    from fides.api.util.cache import FidesopsRedis

MASKED = "MASKED"


class InterceptHandler(logging.Handler):
    """
    Intercept standard library logging and redirect to Loguru.

    This handler is added to the root logger to capture logs from libraries
    that use standard library logging (SQLAlchemy, Alembic, Celery, etc.)
    and route them through Loguru for consistent formatting and serialization.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by routing it through Loguru."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame: Optional[FrameType] = logging.currentframe()
        depth = 2
        # Get the directory path of the logging module to match all files within it
        logging_module_path = os.path.dirname(logging.__file__) + os.sep
        while frame is not None and frame.f_code.co_filename.startswith(
            logging_module_path
        ):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class RedisSink:
    """A sink that writes log messages to Redis."""

    def __init__(self) -> None:
        self.cache: Optional["FidesopsRedis"] = None

    def _ensure_cache(self) -> None:
        """Lazily initialize Redis connection when needed."""
        if self.cache is None:
            from fides.api.util.cache import get_cache

            self.cache = get_cache()

    def __call__(self, message: Message) -> None:
        """Write log message to Redis if conditions are met."""

        record: Dict[str, Any] = message.record  # type: ignore[attr-defined]

        # Extract privacy request context
        extras = record["extra"]
        privacy_request_id = extras.get("privacy_request_id")
        privacy_request_source = extras.get("privacy_request_source")

        # Only process logs with privacy request ID and source is dataset_test
        if (
            not privacy_request_id
            or privacy_request_source != PrivacyRequestSource.dataset_test.value
        ):
            return

        # Ensure we have a Redis connection
        self._ensure_cache()
        assert self.cache  # for mypy

        # Create Redis key using privacy request ID
        key = f"log_{privacy_request_id}"

        # Format log message
        module_info = f"{record['name']}:{record['function']}:{record['line']}"

        log_entry = LogEntry(
            timestamp=record["time"].isoformat(),
            level=record["level"].name,
            module_info=module_info,
            message=record["message"],
        )

        # Encode and append log entry to the list in Redis
        self.cache.push_encoded_object(key, log_entry, expire_time=43200)  # 12 hours


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
    level: str, sink: Any, serialize: bool, colorize: bool, include_called_from: bool
) -> List[Dict]:
    """Creates dictionaries used for configuring loguru handlers."""
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

    # Create base handler config
    base_config = {
        "format": log_format,
        "level": level,
        "serialize": serialize,
        "colorize": colorize,
        "diagnose": False,
        "backtrace": True,
        "catch": True,
    }

    # Helper function to check if a log record has custom extra context
    # Loguru always includes an 'extra' dict, so we need to check if it has any keys
    def has_custom_extra(log_record: Dict) -> bool:
        """Check if log record has custom extra context beyond Loguru's defaults."""
        extra = log_record.get("extra", {})
        return len(extra) > 0

    # Helper to filter logs without custom extra
    def filter_standard(log_record: Dict) -> bool:
        """Filter for logs without custom extra context."""
        return not has_custom_extra(log_record)

    # Configure handler
    standard_dict = {
        **base_config,
        "sink": sink,
        "filter": filter_standard,
    }

    # Create extra dict with additional formatting for logs with extra context
    extra_dict = {
        **standard_dict,
        "format": log_format + " | <dim>{extra}</dim>",
        "filter": has_custom_extra,
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

    # Apply filter to remove generated timing logs
    sqlalchemy_generated_filter = SQLAlchemyGeneratedFilter()
    sqlalchemy_engine_logger = logging.getLogger("sqlalchemy.engine.Engine")
    sqlalchemy_engine_logger.addFilter(sqlalchemy_generated_filter)

    handlers = []

    # Configure main sink from config
    destination = config.logging.destination
    main_sink = sys.stdout if not destination else destination
    is_json_serialization = config.logging.serialization == "json"
    handlers.extend(
        create_handler_dicts(
            level=config.logging.level,
            include_called_from=config.dev_mode,
            sink=main_sink,
            serialize=is_json_serialization,
            colorize=config.logging.colorize and not is_json_serialization,
        )
    )

    # Add Redis sink if Redis is enabled
    if config.redis.enabled:
        redis_sink = RedisSink()
        handlers.extend(
            create_handler_dicts(
                level=config.logging.level,
                include_called_from=config.dev_mode,
                sink=redis_sink,
                serialize=True,  # Always serialize for Redis
                colorize=False,  # Redis doesn't need colorization
            )
        )

    logger.configure(handlers=handlers)  # type: ignore[arg-type]

    # Add InterceptHandler to root logger to capture standard library logs
    # This intercepts logs from SQLAlchemy, Alembic, Celery, etc.
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(config.logging.level)

    # Capture Python warnings and redirect them to logging so they get formatted by Loguru
    logging.captureWarnings(True)


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


# pylint: disable=protected-access
@contextmanager
def suppress_logging() -> Generator:
    """
    Temporarily suppress all logging by setting the log level to CRITICAL.
    """

    current_level = logger._core.min_level  # type: ignore[attr-defined]
    logger._core.min_level = logger.level("CRITICAL").no  # type: ignore[attr-defined]

    try:
        yield
    finally:
        # Restore original configuration
        logger._core.min_level = current_level  # type: ignore[attr-defined]

"""
Defines the logging format and other helper functions to be used throughout the API server code.
"""
# pylint: disable=eval-used,no-member

from __future__ import annotations

from structlog import get_logger

from fides.config import CONFIG

MASKED = "MASKED"
logger = get_logger()


class Pii(str):
    """Mask pii data"""

    def __format__(self, __format_spec: str) -> str:
        if CONFIG.logging.log_pii:
            return super().__format__(__format_spec)
        return MASKED


def _log_exception(exc: BaseException, dev_mode: bool = False) -> None:
    """If dev mode, log the entire traceback"""
    if dev_mode:
        logger.exception(exc)
    else:
        logger.error(exc)


def _log_warning(exc: BaseException, dev_mode: bool = False) -> None:
    """If dev mode, log the entire traceback"""
    if dev_mode:
        logger.exception(exc)
    else:
        logger.error(exc)

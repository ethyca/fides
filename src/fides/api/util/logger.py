"""
Defines the logging format and other helper functions to be used throughout the API server code.
"""
# pylint: disable=eval-used,no-member

from __future__ import annotations

from loguru import logger

from fides.config import CONFIG

MASKED = "MASKED"


class Pii(str):
    """Mask pii data"""

    def __format__(self, __format_spec: str) -> str:
        if CONFIG.logging.log_pii:
            return super().__format__(__format_spec)
        return MASKED

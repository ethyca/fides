"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
import os
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, getLevelName
from typing import Union

from pydantic import validator

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__LOGGING__"


class LoggingSettings(FidesSettings):
    """Class used to store values from the 'logging' section of the config."""

    # Logging
    destination: str = ""
    level: Union[int, str] = "INFO"
    serialization: str = ""

    @validator("destination", pre=True)
    @classmethod
    def get_destination(cls, value: str) -> str:
        """
        Print logs to sys.stdout, unless a valid file path is specified.
        """
        return value if os.path.exists(value) else ""

    @validator("level", pre=True)
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Ensure the provided LEVEL is a valid value."""

        if os.getenv("FIDES__TEST_MODE", "false").lower() == "true":
            return getLevelName(DEBUG)

        valid_values = [
            DEBUG,
            INFO,
            WARNING,
            ERROR,
            CRITICAL,
        ]
        value = value.upper()  # force uppercase, for safety

        if getLevelName(value) not in valid_values:
            raise ValueError(
                f"Invalid LOG_LEVEL provided '{value}', must be one of: {', '.join([getLevelName(level) for level in valid_values])}"
            )

        return value

    @validator("serialization", pre=True)
    @classmethod
    def get_serialization(cls, value: str) -> str:
        """
        Ensure that only JSON serialization, or no serialization, is used.
        """
        value = value.lower()
        return value if value == "json" else ""

    class Config:
        env_prefix = ENV_PREFIX

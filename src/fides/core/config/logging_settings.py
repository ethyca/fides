"""This module handles configuring logging for the appliation."""

# pylint: disable=C0115,C0116, E0213
import os
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, getLevelName

from pydantic import validator

from .fides_settings import FidesSettings
from .utils import get_test_mode

ENV_PREFIX = "FIDES__LOGGING__"


class LoggingSettings(FidesSettings):
    """Class used to store values from the 'logging' section of the config."""

    # Logging
    destination: str = ""
    level: str = "INFO"
    serialization: str = ""
    log_pii: bool = False

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

        if get_test_mode():
            return getLevelName(DEBUG)

        valid_values = [
            DEBUG,
            INFO,
            WARNING,
            ERROR,
            CRITICAL,
        ]
        value = value.upper()  # force uppercase for safety

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

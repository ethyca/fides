"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
import os
from logging import DEBUG, INFO, getLevelName
from typing import Union

from pydantic import validator

from .fides_settings import FidesSettings


class FidesctlLoggingSettings(FidesSettings):
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
    def get_level(cls, value: str) -> str:
        """
        Set the logging level to DEBUG if in test mode, INFO by default.
        Ensures that the string-form of a valid logging._Level is
        always returned.
        """
        if os.getenv("FIDESCTL_TEST_MODE", "false").lower() == "true":
            return getLevelName(DEBUG)

        if isinstance(value, str):
            value = value.upper()

        return value if getLevelName(value) != f"Level {value}" else getLevelName(INFO)

    @validator("serialization", pre=True)
    @classmethod
    def get_serialization(cls, value: str) -> str:
        """
        Ensure that only JSON serialization, or no serialization, is used.
        """
        value = value.lower()
        return value if value == "json" else ""

    class Config:
        env_prefix = "FIDESCTL__LOGGING__"

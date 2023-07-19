"""This module handles configuring logging for the appliation."""

# pylint: disable=C0115,C0116, E0213
import os
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, getLevelName

from pydantic import Field, validator

from .fides_settings import FidesSettings
from .utils import get_dev_mode

ENV_PREFIX = "FIDES__LOGGING__"


class LoggingSettings(FidesSettings):
    """Configuration settings for application logging."""

    # Logging
    destination: str = Field(
        default="",
        description="The output location for log files. Accepts any valid file path. If left unset, log entries are printed to stdout and log files are not produced.",
    )
    colorize: bool = Field(
        default=False,
        description="Force colored logs. Any value set via environment variables is considered 'True'.",
    )
    level: str = Field(
        default="INFO",
        description="The minimum log entry level to produce. Also accepts TRACE, DEBUG, WARNING, ERROR, or CRITICAL (case insensitive).",
    )
    serialization: str = Field(
        default="",
        description="The format with which to produce log entries. If left unset, produces log entries formatted using the internal custom formatter. Also accepts 'JSON' (case insensitive).",
    )
    log_pii: bool = Field(
        default=False,
        description="If True, PII values will display unmasked in log output. This variable should always be set to 'False' in production systems.",
    )

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

        if get_dev_mode():
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

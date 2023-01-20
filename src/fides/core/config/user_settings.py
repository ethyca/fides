"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213

from typing import Dict, Optional

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__USER__"


class UserSettings(FidesSettings):
    """Class used to store values from the 'user' section of the config."""

    # Auth headers are set when the CLI is initiated.
    auth_header: Optional[Dict[str, str]]
    analytics_opt_out: Optional[bool]
    encryption_key: str = "test_encryption_key"

    class Config:
        env_prefix = ENV_PREFIX

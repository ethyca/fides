"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from pydantic import Field

from typing import Dict, Optional

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__USER__"


class UserSettings(FidesSettings):
    """Class used to store values from the 'user' section of the config."""

    auth_header: Optional[Dict[str, str]] = Field(
        default=None,
        description="Authentication header built automatically from the credentials file.",
        exclude=True,
    )
    analytics_opt_out: Optional[bool] = Field(
        description="When set to true, prevents sending anonymous analytics data to Ethyca."
    )
    encryption_key: str = Field(
        default="test_encryption_key",
        description="An arbitrary string used to encrypt the user data stored in the database. Encryption is implemented using PGP.",
    )

    class Config:
        env_prefix = ENV_PREFIX

"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from typing import Dict

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from fides.core.utils import create_auth_header, get_auth_header

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__USER__"


def try_get_auth_header() -> Dict[str, str]:
    """Try to get the auth header. If an error is thrown, return a default auth header instead."""
    try:
        return get_auth_header(verbose=False)
    except SystemExit:
        return create_auth_header("defaulttoken")


class UserSettings(FidesSettings):
    """Configuration settings that apply to the current user as opposed to the entire application instance."""

    auth_header: Dict[str, str] = Field(
        default=try_get_auth_header(),
        description="Authentication header built automatically from the credentials file.",
        exclude=True,
    )
    analytics_opt_out: bool = Field(
        default=True,
        description="When set to true, prevents sending privacy-respecting anonymous analytics data to Ethyca.",
    )
    encryption_key: str = Field(
        default="test_encryption_key",
        description="An arbitrary string used to encrypt the user data stored in the database. Encryption is implemented using PGP.",
    )
    username: str = Field(
        default="", description="The username used to log into the Fides webserver."
    )
    password: str = Field(
        default="", description="The password used to log into the Fides webserver."
    )
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)

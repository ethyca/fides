"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213

from typing import Dict, Optional

from fides.core.utils import create_auth_header, get_auth_header

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__USER__"


def try_get_auth_header() -> Dict[str, str]:
    """Try to get the auth header. If an error is thrown, return a default auth header instead."""
    try:
        return get_auth_header(verbose=False)
    except FileNotFoundError:
        return create_auth_header("defaulttoken")


class UserSettings(FidesSettings):
    """Class used to store values from the 'user' section of the config."""

    auth_header: Dict[str, str] = try_get_auth_header()
    analytics_opt_out: Optional[bool]
    encryption_key: str = "test_encryption_key"

    class Config:
        env_prefix = ENV_PREFIX

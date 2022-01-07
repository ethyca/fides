"""This module defines the base settings for the other settings to inherit from."""

# pylint: disable=C0115,C0116, E0213

from typing import Tuple

from pydantic import BaseSettings
from pydantic.env_settings import SettingsSourceCallable


class FidesSettings(BaseSettings):
    """Class used as a base model for configuration subsections."""

    class Config:
        extra = "forbid"

        # Set environment variables to take precedence over init values
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings, file_secret_settings

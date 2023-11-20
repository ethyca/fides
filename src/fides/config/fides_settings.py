"""This module defines the base settings for the other settings to inherit from."""

# pylint: disable=C0115,C0116, E0213

from typing import Tuple

from pydantic import Extra
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class FidesSettings(BaseSettings):
    """Class used as a base model for configuration subsections."""

    # TODO[pydantic]: We couldn't refactor this class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config:
        # Need to allow extras because the inheriting class will have more info
        extra = Extra.allow

        @classmethod
        def customise_sources(
            cls,
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> Tuple[PydanticBaseSettingsSource, ...]:
            """Set environment variables to take precedence over init values."""
            return env_settings, init_settings, file_secret_settings

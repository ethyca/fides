"""This module defines the base settings for the other settings to inherit from."""

# pylint: disable=C0115,C0116, E0213

from typing import Tuple, Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class FidesSettings(BaseSettings):
    """Class used as a base model for configuration subsections."""

    model_config = SettingsConfigDict(extra="allow")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Set environment variables to take precedence over init values."""
        return env_settings, init_settings, file_secret_settings

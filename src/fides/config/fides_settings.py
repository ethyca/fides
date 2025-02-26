"""This module defines the base settings for the other settings to inherit from."""

# pylint: disable=C0115,C0116, E0213

from typing import Optional, Tuple, Type

from pydantic import ValidationInfo
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


def port_integer_converter(
    info: ValidationInfo, port_name: Optional[str] = None
) -> int:
    """
    Convert supplied port value to an integer.

    "Before" field validators mean that port is not yet guaranteed to exist or be the appropriate type
    """
    port = info.data.get(port_name or "port")

    if not isinstance(port, (str, int)):  # This check also helps satisfy mypy
        raise ValueError(
            "Port must be supplied and able to be converted to an integer."
        )

    return int(port)

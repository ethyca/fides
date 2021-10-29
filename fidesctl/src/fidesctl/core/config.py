"""This module handles finding and parsing fides configuration files."""
# pylint: disable=C0115,C0116, E0213

import os
from typing import Dict, Optional, Tuple

import toml

from pydantic.env_settings import SettingsSourceCallable
from pydantic import BaseModel, BaseSettings, validator

from fidesctl.core.utils import echo_red, generate_request_headers


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


class UserSettings(FidesSettings):
    """Class used to store values from the 'user' section of the config."""

    user_id: str = "1"
    api_key: str = "test_api_key"
    request_headers: Dict[str, str] = dict()

    # Automatically generate the request_headers on object creation
    @validator("request_headers", pre=True, always=True)
    def get_request_headers(
        cls: BaseModel, value: Optional[Dict], values: Dict
    ) -> Dict[str, str]:
        return generate_request_headers(values["user_id"], values["api_key"])

    class Config:
        env_prefix = "FIDESCTL__USER__"


class CLISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""

    server_url: str = "http://localhost:8080"

    class Config:
        env_prefix = "FIDESCTL__CLI__"


class APISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""

    database_url: str = "postgresql+psycopg2://fidesdb:fidesdb@localhost:5432/fidesdb"

    class Config:
        env_prefix = "FIDESCTL__API__"


class FidesctlConfig(BaseModel):
    """Umbrella class that encapsulates all of the config subsections."""

    api: APISettings = APISettings()
    cli: CLISettings = CLISettings()
    user: UserSettings = UserSettings()


def get_config(config_path: str = "") -> FidesctlConfig:
    """
    Attempt to read config file from:
    a) passed in configuration, if it exists
    b) env var FIDESCTL_CONFIG_PATH
    b) local directory
    c) home directory

    This will fail on the first encountered bad conf file.
    """
    default_file_name = "fidesctl.toml"

    possible_config_locations = [
        config_path,
        os.getenv("FIDESCTL_CONFIG_PATH", ""),
        os.path.join(os.curdir, default_file_name),
        os.path.join(os.path.expanduser("~"), default_file_name),
    ]

    for file_location in possible_config_locations:
        if file_location != "" and os.path.isfile(file_location):
            try:
                settings = toml.load(file_location)
                fidesctl_config = FidesctlConfig.parse_obj(settings)
                return fidesctl_config
            except IOError:
                echo_red(f"Error reading config file from {file_location}")
    fidesctl_config = FidesctlConfig()
    return fidesctl_config

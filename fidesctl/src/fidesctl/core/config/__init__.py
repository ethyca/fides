"""
This module is responsible for combining all of the different
config sections into a single config.
"""
import os

import toml
from pydantic import BaseModel

from fidesctl.core.utils import echo_red

from .api_settings import APISettings
from .cli_settings import CLISettings
from .user_settings import UserSettings


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
    default_file_name = ".fides/fidesctl.toml"

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
    print("No config file found. Using default configuration values.")
    return fidesctl_config

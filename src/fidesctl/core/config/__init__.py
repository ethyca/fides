"""
This module is responsible for combining all of the different
config sections into a single config.
"""

from typing import Dict

import toml
from pydantic import BaseModel

from fidesctl.core.config.utils import get_config_path
from fidesctl.core.utils import echo_red

from .api_settings import APISettings
from .cli_settings import CLISettings
from .credentials_settings import merge_credentials_environment
from .user_settings import UserSettings


class FidesctlConfig(BaseModel):
    """Umbrella class that encapsulates all of the config subsections."""

    api: APISettings = APISettings()
    cli: CLISettings = CLISettings()
    user: UserSettings = UserSettings()
    credentials: Dict[str, Dict] = dict()


def get_config(config_path: str = "") -> FidesctlConfig:
    """
    Attempt to load user-defined configuration.

    This will fail if the first encountered conf file is invalid.

    On failure, returns default configuration.
    """

    try:
        file_location = get_config_path(config_path)
        settings = toml.load(file_location)

        # credentials specific logic for populating environment variable configs.
        # this is done to allow overrides without hard typed pydantic models
        config_environment_dict = settings.get("credentials", dict())
        settings["credentials"] = merge_credentials_environment(
            credentials_dict=config_environment_dict
        )

        fidesctl_config = FidesctlConfig.parse_obj(settings)
        return fidesctl_config
    except FileNotFoundError:
        echo_red("No config file found")
    except IOError:
        echo_red(f"Error reading config file from {file_location}")

    fidesctl_config = FidesctlConfig()
    print("Using default configuration values.")
    return fidesctl_config

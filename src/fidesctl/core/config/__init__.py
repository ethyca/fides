"""
This module is responsible for combining all of the different
config sections into a single config.
"""

import toml
from pydantic import create_model

from fidesctl.core.config.utils import get_config_path
from fidesctl.core.utils import echo_red

from .api_settings import APISettings
from .cli_settings import CLISettings
from .credentials_settings import create_dynamic_credentials_settings_model
from .fides_settings import FidesSettings
from .user_settings import UserSettings


class FidesctlConfig(FidesSettings):
    """Umbrella class that encapsulates all of the config subsections."""

    api: APISettings = APISettings()
    cli: CLISettings = CLISettings()
    user: UserSettings = UserSettings()

    class Config:
        """Configures env override prefix and nested delimiter for all configs"""

        env_prefix = "FIDESCTL_"
        env_nested_delimiter = "__"


def get_config(config_path: str = "") -> FidesctlConfig:
    """
    Attempt to load user-defined configuration.

    This will fail if the first encountered conf file is invalid.

    On failure, returns default configuration.
    """

    try:
        file_location = get_config_path(config_path)
        settings = toml.load(file_location)
        # Top level config is extended dynamically to allow custom keys to be treated as attributes
        dynamic_credentials_settings_model = create_dynamic_credentials_settings_model(
            settings=settings
        )
        fidesctl_dynamic_config_model = create_model(
            "FidesctlDynamicConfig",
            credentials=(
                dynamic_credentials_settings_model,
                dynamic_credentials_settings_model(),
            ),
            __base__=FidesctlConfig,
        )
        fidesctl_config = fidesctl_dynamic_config_model.parse_obj(settings)
        return fidesctl_config
    except FileNotFoundError:
        echo_red("No config file found")
    except IOError:
        echo_red(f"Error reading config file from {file_location}")

    fidesctl_config = FidesctlConfig()
    print("Using default configuration values.")
    return fidesctl_config

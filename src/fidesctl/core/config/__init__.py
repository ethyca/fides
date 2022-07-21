"""
This module is responsible for combining all of the different
config sections into a single config.
"""
from functools import lru_cache
from typing import Dict

import toml
from fideslib.core.config import load_toml
from pydantic import BaseModel

from fidesctl.core.utils import echo_red

from .cli_settings import FidesctlCLISettings
from .credentials_settings import merge_credentials_environment
from .database_settings import FidesctlDatabaseSettings
from .logging_settings import FidesctlLoggingSettings
from .security_settings import FidesctlSecuritySettings
from .user_settings import FidesctlUserSettings

DEFAULT_CONFIG_PATH = ".fides/fidesctl.toml"


class FidesctlConfig(BaseModel):
    """Umbrella class that encapsulates all of the config subsections."""

    cli: FidesctlCLISettings = FidesctlCLISettings()
    user: FidesctlUserSettings = FidesctlUserSettings()
    credentials: Dict[str, Dict] = dict()
    database: FidesctlDatabaseSettings = FidesctlDatabaseSettings()
    security: FidesctlSecuritySettings = FidesctlSecuritySettings()
    logging: FidesctlLoggingSettings = FidesctlLoggingSettings()


@lru_cache(maxsize=1)
def get_config(config_path_override: str = "") -> FidesctlConfig:
    """
    Attempt to load user-defined configuration.

    This will fail if the first encountered conf file is invalid.

    On failure, returns default configuration.
    """

    try:
        settings = (
            toml.load(config_path_override)
            if config_path_override
            else load_toml(file_names=[DEFAULT_CONFIG_PATH])
        )

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
        echo_red("Error reading config file")

    fidesctl_config = FidesctlConfig()
    print("Using default configuration values.")
    return fidesctl_config

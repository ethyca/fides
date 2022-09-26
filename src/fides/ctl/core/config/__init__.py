"""
This module is responsible for combining all of the different
config sections into a single config.
"""
from functools import lru_cache
from os import environ
from re import compile as regex
from typing import Dict, MutableMapping

import toml
from fideslib.core.config import load_toml
from pydantic import BaseModel

from fidesctl.ctl.core.utils import echo_red

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


def handle_deprecated_fields(settings: MutableMapping) -> MutableMapping:
    """Custom logic for handling deprecated values."""

    if settings.get("api") and not settings.get("database"):
        api_settings = settings.pop("api")
        database_settings = dict()
        database_settings["user"] = api_settings.get("database_user")
        database_settings["password"] = api_settings.get("database_password")
        database_settings["server"] = api_settings.get("database_host")
        database_settings["port"] = api_settings.get("database_port")
        database_settings["db"] = api_settings.get("database_name")
        database_settings["test_db"] = api_settings.get("test_database_name")
        settings["database"] = database_settings

    return settings


def handle_deprecated_env_variables(settings: MutableMapping) -> MutableMapping:
    """
    Custom logic for handling deprecated ENV variable configuration.
    """

    deprecated_env_vars = regex(r"FIDESCTL__API__(\w+)")

    for key, val in environ.items():
        match = deprecated_env_vars.search(key)
        if match:
            setting = match.group(1).lower()
            setting = setting[setting.startswith("database_") and len("database_") :]
            if setting == "host":
                setting = "server"
            if setting == "name":
                setting = "db"
            if setting == "test_database_name":
                setting = "test_db"

            settings["database"][setting] = val

    return settings


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
        settings = handle_deprecated_fields(settings)

        # Called after `handle_deprecated_fields` to ensure ENV vars are respected
        settings = handle_deprecated_env_variables(settings)

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

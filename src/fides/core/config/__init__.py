"""
This module is responsible for combining all of the different
config sections into a single config object.
"""

from functools import lru_cache
from os import getenv
from typing import Any, Dict, Optional, Tuple

import toml
from loguru import logger as log
from pydantic.class_validators import _FUNCS
from pydantic.env_settings import SettingsSourceCallable

from fides.core.utils import echo_red

from .admin_ui_settings import AdminUISettings
from .cli_settings import CLISettings
from .credentials_settings import merge_credentials_environment
from .database_settings import DatabaseSettings
from .execution_settings import ExecutionSettings
from .fides_settings import FidesSettings
from .helpers import handle_deprecated_env_variables, handle_deprecated_fields
from .logging_settings import LoggingSettings
from .notification_settings import NotificationSettings
from .redis_settings import RedisSettings
from .security_settings import SecuritySettings
from .user_settings import UserSettings
from .utils import (
    CONFIG_KEY_ALLOWLIST,
    DEFAULT_CONFIG_PATH,
    DEFAULT_CONFIG_PATH_ENV_VAR,
    get_test_mode,
)


class FidesConfig(FidesSettings):
    """
    Composite class that encapsulates all of the config subsections
    as well as root-level values.
    """

    # Root Settings
    test_mode: bool = get_test_mode()
    is_test_mode: bool = test_mode
    hot_reloading: bool = getenv("FIDES__HOT_RELOAD", "").lower() == "true"
    dev_mode: bool = getenv("FIDES__DEV_MODE", "").lower() == "true"
    oauth_instance: Optional[str] = getenv("FIDES__OAUTH_INSTANCE")

    # Setting Subsections
    # These should match the `settings_map` in `build_config`
    admin_ui: AdminUISettings
    cli: CLISettings
    celery: Dict
    credentials: Dict
    database: DatabaseSettings
    execution: ExecutionSettings
    logging: LoggingSettings
    notifications: NotificationSettings
    redis: RedisSettings
    security: SecuritySettings
    user: UserSettings

    class Config:  # pylint: disable=C0115
        case_sensitive = True

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            """Set environment variables to take precedence over init values."""
            return env_settings, init_settings, file_secret_settings

    def log_all_config_values(self) -> None:
        """Output DEBUG logs of all the config values."""
        for settings in [
            self.cli,
            self.user,
            self.logging,
            self.database,
            self.notifications,
            self.redis,
            self.security,
            self.execution,
            self.admin_ui,
        ]:
            for key, value in settings.dict().items():  # type: ignore
                log.debug(
                    f"Using config: {settings.Config.env_prefix}{key.upper()} = {value}",  # type: ignore
                )


def censor_config(config: FidesConfig) -> Dict[str, Any]:
    """
    Returns a config that is safe to expose over the API. This function will
    strip out any keys not specified in the `CONFIG_KEY_ALLOWLIST` above.
    """
    as_dict = config.dict()
    filtered: Dict[str, Any] = {}
    for key, value in CONFIG_KEY_ALLOWLIST.items():
        data = as_dict[key]
        filtered[key] = {}
        for field in value:
            filtered[key][field] = data[field]

    return filtered


def build_config(config_dict: Dict[str, Any]) -> FidesConfig:
    """
    This function builds and instantiates a FidesConfig.

    It will pull from the provided config_dict when possible for subsections,
    otherwise instantiating the settings with default values.

    The settings_map will need to be kept up-to-date manually with the
    expected subsections of the FidesConfig.
    """
    config_dict = handle_deprecated_fields(config_dict)
    config_dict = handle_deprecated_env_variables(config_dict)

    settings_map: Dict[str, Any] = {
        "admin_ui": AdminUISettings,
        "cli": CLISettings,
        "database": DatabaseSettings,
        "execution": ExecutionSettings,
        "logging": LoggingSettings,
        "notifications": NotificationSettings,
        "redis": RedisSettings,
        "security": SecuritySettings,
        "user": UserSettings,
    }

    for key, value in settings_map.items():
        settings_map[key] = value.parse_obj(config_dict.get(key, {}))

    # Logic for populating the user-defined credentials sub-settings.
    # this is done to allow overrides without typed pydantic models
    config_environment_dict = config_dict.get("credentials", {})
    settings_map["credentials"] = merge_credentials_environment(
        credentials_dict=config_environment_dict
    )

    # The Celery subsection is uniquely simple
    settings_map["celery"] = config_dict.get("celery", {})

    fides_config = FidesConfig(**settings_map)
    return fides_config


@lru_cache(maxsize=1)
def get_config(config_path_override: str = "", verbose: bool = False) -> FidesConfig:
    """
    Attempt to load user-defined configuration file, otherwise will use defaults
    while still respecting any env vars set by the user.

    Order of file checks is:
        1. The config path provided by the user to the CLI
        2. The config path provided by the user via an env var
        3. The default config path

    This will fail if the first encountered configuration file is invalid.
    """

    # This prevents a Pydantic validator reuse error. For context see
    # https://github.com/streamlit/streamlit/issues/3218
    _FUNCS.clear()

    env_config_path = getenv(DEFAULT_CONFIG_PATH_ENV_VAR)
    config_path = config_path_override or env_config_path or DEFAULT_CONFIG_PATH
    if verbose:
        print(f"Loading config from: {config_path}")

    try:
        settings = toml.load(config_path)
        config = build_config(config_dict=settings)
        return config
    except FileNotFoundError:
        print("No config file found.")
    except IOError:
        echo_red(f"Error reading config file: {config_path}")

    print("Using default configuration values.")
    config = build_config(config_dict={})

    return config

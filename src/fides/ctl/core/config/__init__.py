"""
This module is responsible for combining all of the different
config sections into a single config.
"""

from functools import lru_cache
from os import environ, getenv
from re import compile as regex
from typing import Any, Dict, MutableMapping, Optional, Tuple

import toml
from fideslib.core.config import load_toml
from loguru import logger as log
from pydantic import BaseModel
from pydantic.class_validators import _FUNCS
from pydantic.env_settings import SettingsSourceCallable

from fides.ctl.core.utils import echo_red

from .admin_ui_settings import AdminUISettings
from .cli_settings import CLISettings
from .credentials_settings import merge_credentials_environment
from .database_settings import DatabaseSettings
from .execution_settings import ExecutionSettings
from .logging_settings import LoggingSettings
from .notification_settings import NotificationSettings
from .redis_settings import RedisSettings
from .security_settings import SecuritySettings
from .user_settings import UserSettings
from .utils import DEFAULT_CONFIG_PATH, get_test_mode


class FidesConfig(BaseModel):
    """
    Composite class that encapsulates all of the config subsections.
    """

    admin_ui: AdminUISettings = AdminUISettings()
    cli: CLISettings = CLISettings()
    credentials: Dict[str, Dict] = {}
    database: DatabaseSettings = DatabaseSettings()
    execution: ExecutionSettings = ExecutionSettings()
    logging: LoggingSettings = LoggingSettings()
    notifications: NotificationSettings = NotificationSettings()
    redis: RedisSettings = RedisSettings()
    # Use 'construct' to avoid running validation
    # This allows us to use the correct type but populate later
    security: SecuritySettings = SecuritySettings.construct()
    user: UserSettings = UserSettings()

    test_mode: bool = get_test_mode()
    is_test_mode: bool = test_mode
    hot_reloading: bool = getenv("FIDES__HOT_RELOAD", "").lower() == "true"
    dev_mode: bool = getenv("FIDES__DEV_MODE", "").lower() == "true"
    oauth_instance: Optional[str] = getenv("FIDES__OAUTH_INSTANCE")

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


def handle_deprecated_fields(settings: MutableMapping) -> MutableMapping:
    """Custom logic for handling deprecated values."""

    if settings.get("api") and not settings.get("database"):
        api_settings = settings.pop("api")
        database_settings = {}
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

    deprecated_env_vars = regex(r"FIDES__API__(\w+)")

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


CONFIG_KEY_ALLOWLIST = {
    "cli": ["server_host", "server_port"],
    "user": ["analytics_opt_out"],
    "logging": ["level"],
    "database": [
        "server",
        "user",
        "port",
        "db",
        "test_db",
    ],
    "notifications": [
        "send_request_completion_notification",
        "send_request_receipt_notification",
        "send_request_review_notification",
        "notification_service_type",
    ],
    "redis": [
        "host",
        "port",
        "charset",
        "decode_responses",
        "default_ttl_seconds",
        "db_index",
    ],
    "security": [
        "cors_origins",
        "encoding",
        "oauth_access_token_expire_minutes",
    ],
    "execution": [
        "task_retry_count",
        "task_retry_delay",
        "task_retry_backoff",
        "require_manual_request_approval",
    ],
}


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


@lru_cache(maxsize=1)
def get_config(config_path_override: str = "", verbose: bool = False) -> FidesConfig:
    """
    Attempt to load user-defined configuration.

    This will fail if the first encountered configuration file is invalid.

    On failure, returns default configuration.
    """

    # This prevents a Pydantic validator reuse error. For context see
    # https://github.com/streamlit/streamlit/issues/3218
    _FUNCS.clear()

    env_config_path = getenv("FIDES__CONFIG_PATH")
    config_path = config_path_override or env_config_path or DEFAULT_CONFIG_PATH
    if verbose:
        print(f"Loading config from: {config_path}")
    try:
        settings = (
            toml.load(config_path)
            if config_path_override
            else load_toml(file_names=[config_path])
        )

        # credentials specific logic for populating environment variable configs.
        # this is done to allow overrides without hard typed pydantic models
        settings = handle_deprecated_fields(settings)

        # Called after `handle_deprecated_fields` to ensure ENV vars are respected
        settings = handle_deprecated_env_variables(settings)

        config_environment_dict = settings.get("credentials", {})
        settings["credentials"] = merge_credentials_environment(
            credentials_dict=config_environment_dict
        )

        # This is required to set security settings from the environment
        # if that section of the config is missing
        security_settings = SecuritySettings.parse_obj(settings.get("security", {}))

        config = FidesConfig.parse_obj(settings)
        config.security = security_settings
        return config
    except FileNotFoundError:
        print("No config file found")
    except IOError:
        echo_red("Error reading config file")

    print("Using default configuration values.")
    security_settings = SecuritySettings()
    config = FidesConfig(security=security_settings)

    return config

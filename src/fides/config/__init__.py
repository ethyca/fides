"""
This module is responsible for combining all of the different
config sections into a single config object.
"""

from functools import lru_cache
from os import getenv
from typing import Any, Dict, Optional, Tuple, Type, Union

import toml
from loguru import logger as log
from pydantic import ConfigDict, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from fides.common.utils import echo_red

from .admin_ui_settings import AdminUISettings
from .celery_settings import CelerySettings
from .cli_settings import CLISettings
from .consent_settings import ConsentSettings
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
    test_mode: bool = Field(
        default=get_test_mode(),
        description="Whether or not the application is being run in test mode.",
        exclude=True,
    )
    hot_reloading: bool = Field(
        default=getenv("FIDES__HOT_RELOAD", "").lower() == "true",
        description="Whether or not to enable hot reloading for the webserver.",
        exclude=True,
    )
    dev_mode: bool = Field(
        default=getenv("FIDES__DEV_MODE", "").lower() == "true",
        description="Similar to 'test_mode', enables certain features when true.",
        exclude=True,
    )
    oauth_instance: Optional[str] = Field(
        default=getenv("FIDES__OAUTH_INSTANCE", None),
        description="A value that is prepended to the generated 'state' param in outbound OAuth2 authorization requests. Used during OAuth2 testing to associate callback responses back to this specific Fides instance.",
        exclude=True,
    )

    # Setting Subsections
    # These should match the `settings_map` in `build_config`
    admin_ui: AdminUISettings
    consent: ConsentSettings
    cli: CLISettings
    celery: CelerySettings
    credentials: Dict = Field(
        description="This is a special section that is used to store arbitrary key/value pairs to be used as credentials."
    )
    database: DatabaseSettings
    execution: ExecutionSettings
    logging: LoggingSettings
    notifications: NotificationSettings
    redis: RedisSettings
    security: SecuritySettings
    user: UserSettings

    model_config = SettingsConfigDict(case_sensitive=True)

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
            for key, value in settings.model_dump(mode="json").items():  # type: ignore
                log.debug(
                    f"Using config: {settings.Config.env_prefix}{key.upper()} = {value}",  # type: ignore
                )


def censor_config(config: Union[FidesConfig, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Returns a config that is safe to expose over the API. This function will
    strip out any keys not specified in the `CONFIG_KEY_ALLOWLIST` above.
    """
    if not isinstance(config, Dict):
        as_dict = config.model_dump(mode="json")
    else:
        as_dict = config
    filtered: Dict[str, Any] = {}
    for key, value in CONFIG_KEY_ALLOWLIST.items():
        if key in as_dict:
            data = as_dict[key]
            filtered[key] = {}
            for field in value:
                if field in data:
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
        "celery": CelerySettings,
        "consent": ConsentSettings,
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
        settings_map[key] = value.model_validate(config_dict.get(key, {}))

    # Logic for populating the user-defined credentials sub-settings.
    # this is done to allow overrides without typed pydantic models
    config_environment_dict = config_dict.get("credentials", {})
    settings_map["credentials"] = merge_credentials_environment(
        credentials_dict=config_environment_dict
    )

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

    env_config_path = getenv(DEFAULT_CONFIG_PATH_ENV_VAR)
    config_path = config_path_override or env_config_path or DEFAULT_CONFIG_PATH

    try:
        settings = toml.load(config_path)
        config = build_config(config_dict=settings)
        if verbose:
            print(f"> Loaded config from: {config_path}")
        return config
    except FileNotFoundError:
        pass
    except IOError:
        echo_red(f"Error reading config file: {config_path}")

    if verbose:  # pragma: no cover
        print("> Using default configuration values.")
    config = build_config(config_dict={})

    return config


def check_required_webserver_config_values(config: FidesConfig) -> None:
    """Check for required config values and print a user-friendly error message."""
    required_config_dict = {
        "security": [
            "app_encryption_key",
            "oauth_root_client_id",
            "oauth_root_client_secret",
        ]
    }

    missing_required_config_vars = []
    for subsection_key, values in required_config_dict.items():
        for key in values:
            subsection_model = dict(config).get(subsection_key, {})
            config_value = dict(subsection_model).get(key)

            if not config_value:
                missing_required_config_vars.append(".".join((subsection_key, key)))

    if missing_required_config_vars:
        echo_red(
            "\nThere are missing required configuration variables. Please add the following config variables to either the "
            "`fides.toml` file or your environment variables to start Fides: \n"
        )
        for missing_value in missing_required_config_vars:
            echo_red(f"- {missing_value}")
        echo_red(
            "\nVisit the Fides deployment documentation for more information: "
            "https://ethyca.com/docs/dev-docs/configuration/deployment"
        )

        raise SystemExit(1)


CONFIG = get_config()

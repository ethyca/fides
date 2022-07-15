# pylint: disable=C0115,C0116, E0213

import logging
import os
from typing import Any, Dict, MutableMapping, Optional

import toml
from fideslib.core.config import (
    DatabaseSettings,
    FidesSettings,
    SecuritySettings,
    get_config,
    load_file,
    load_toml,
)
from fideslog.sdk.python.utils import FIDESOPS, generate_client_id
from pydantic import validator

from fidesops.util.logger import NotPii

logger = logging.getLogger(__name__)


class FidesopsDatabaseSettings(DatabaseSettings):
    """Configuration settings for Postgres."""

    ENABLED: bool = True

    class Config:
        env_prefix = "FIDESOPS__DATABASE__"


class ExecutionSettings(FidesSettings):
    """Configuration settings for execution."""

    PRIVACY_REQUEST_DELAY_TIMEOUT: int = 3600
    TASK_RETRY_COUNT: int
    TASK_RETRY_DELAY: int  # In seconds
    TASK_RETRY_BACKOFF: int
    REQUIRE_MANUAL_REQUEST_APPROVAL: bool = False
    MASKING_STRICT: bool = True
    WORKER_ENABLED: bool = True
    CELERY_CONFIG_PATH: Optional[str] = "celery.toml"

    class Config:
        env_prefix = "FIDESOPS__EXECUTION__"


class RedisSettings(FidesSettings):
    """Configuration settings for Redis."""

    HOST: str
    PORT: int = 6379
    USER: Optional[str] = ""
    PASSWORD: str
    CHARSET: str = "utf8"
    DECODE_RESPONSES: bool = True
    DEFAULT_TTL_SECONDS: int = 604800
    DB_INDEX: Optional[int]
    ENABLED: bool = True
    SSL: bool = False
    SSL_CERT_REQS: Optional[str] = "required"
    CONNECTION_URL: Optional[str] = None

    @validator("CONNECTION_URL", pre=True)
    @classmethod
    def assemble_connection_url(
        cls,
        v: Optional[str],
        values: Dict[str, str],
    ) -> str:
        """Join Redis connection credentials into a connection string"""
        if isinstance(v, str):
            # If the whole URL is provided via the config, preference that
            return v

        return f"redis://{values.get('USER', '')}:{values['PASSWORD']}@{values['HOST']}:{values['PORT']}/{values.get('DB_INDEX', '')}"

    class Config:
        env_prefix = "FIDESOPS__REDIS__"


class FidesopsSecuritySettings(SecuritySettings):
    """Configuration settings for Security variables."""

    LOG_LEVEL: str = "INFO"

    @validator("LOG_LEVEL", pre=True)
    def validate_log_level(cls, value: str) -> str:
        """Ensure the provided LOG_LEVEL is a valid value."""
        valid_values = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]
        value = value.upper()  # force uppercase, for safety

        # Attempt to convert the string value (e.g. 'debug') to a numeric level, e.g. 10 (logging.DEBUG)
        # NOTE: If the string doesn't match a valid level, this will return a string like 'Level {value}'
        if logging.getLevelName(value) not in valid_values:
            raise ValueError(
                f"Invalid LOG_LEVEL provided '{value}', must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )

        return value

    class Config:
        env_prefix = "FIDESOPS__SECURITY__"


class RootUserSettings(FidesSettings):
    """Configuration settings for Analytics variables."""

    ANALYTICS_OPT_OUT: Optional[bool]
    ANALYTICS_ID: Optional[str]

    @validator("ANALYTICS_ID", pre=True)
    def populate_analytics_id(cls, v: Optional[str]) -> str:
        """
        Populates the appropriate value for analytics id based on config
        """
        return v or cls.generate_and_store_client_id()

    @staticmethod
    def generate_and_store_client_id() -> str:
        update_obj: Dict[str, Dict] = {}
        client_id: str = generate_client_id(FIDESOPS)
        logger.debug("analytics client id generated")
        update_obj.update(root_user={"ANALYTICS_ID": client_id})
        update_config_file(update_obj)
        return client_id

    class Config:
        env_prefix = "FIDESOPS__ROOT_USER__"


class AdminUiSettings(FidesSettings):
    """Configuration settings for Analytics variables."""

    ENABLED: bool

    class Config:
        env_prefix = "FIDESOPS__ADMIN_UI__"


class FidesopsConfig(FidesSettings):
    """Configuration variables for the FastAPI project"""

    database: FidesopsDatabaseSettings
    redis: RedisSettings
    security: FidesopsSecuritySettings
    execution: ExecutionSettings
    root_user: RootUserSettings
    admin_ui: AdminUiSettings

    PORT: int
    is_test_mode: bool = os.getenv("TESTING", "").lower() == "true"
    hot_reloading: bool = os.getenv("FIDESOPS__HOT_RELOAD", "").lower() == "true"
    dev_mode: bool = os.getenv("FIDESOPS__DEV_MODE", "").lower() == "true"

    class Config:  # pylint: disable=C0115
        case_sensitive = True

    logger.warning(
        f"Startup configuration: reloading = {hot_reloading}, dev_mode = {dev_mode}"
    )
    logger.warning(
        f'Startup configuration: pii logging = {os.getenv("FIDESOPS__LOG_PII", "").lower() == "true"}'
    )

    def log_all_config_values(self) -> None:
        """Output DEBUG logs of all the config values."""
        for settings in [
            self.database,
            self.redis,
            self.security,
            self.execution,
            self.admin_ui,
        ]:
            for key, value in settings.dict().items():  # type: ignore
                logger.debug(
                    "Using config: %s%s = %s",
                    NotPii(settings.Config.env_prefix),  # type: ignore
                    NotPii(key),
                    NotPii(value),
                )


CONFIG_KEY_ALLOWLIST = {
    "database": [
        "SERVER",
        "USER",
        "PORT",
        "DB",
        "TEST_DB",
    ],
    "redis": [
        "HOST",
        "PORT",
        "CHARSET",
        "DECODE_RESPONSES",
        "DEFAULT_TTL_SECONDS",
        "DB_INDEX",
    ],
    "security": [
        "CORS_ORIGINS",
        "ENCODING",
        "OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
    ],
    "execution": [
        "TASK_RETRY_COUNT",
        "TASK_RETRY_DELAY",
        "TASK_RETRY_BACKOFF",
        "REQUIRE_MANUAL_REQUEST_APPROVAL",
    ],
}


def get_censored_config(the_config: FidesopsConfig) -> Dict[str, Any]:
    """
    Returns a config that is safe to expose over the API. This function will
    strip out any keys not specified in the `CONFIG_KEY_ALLOWLIST` above.
    """
    as_dict = the_config.dict()
    filtered: Dict[str, Any] = {}
    for key, value in CONFIG_KEY_ALLOWLIST.items():
        data = as_dict[key]
        filtered[key] = {}
        for field in value:
            filtered[key][field] = data[field]

    return filtered


def update_config_file(updates: Dict[str, Dict[str, Any]]) -> None:
    """
    Overwrite the existing config file with a new version that includes the desired `updates`.
    :param updates: A nested `dict`, where top-level keys correspond to configuration sections and top-level values contain `dict`s whose key/value pairs correspond to the desired option/value updates.
    """
    try:
        config_path: str = load_file(["fidesops.toml"])
        current_config: MutableMapping[str, Any] = load_toml(["fidesops.toml"])
    except FileNotFoundError as e:
        logger.warning("fidesops.toml could not be loaded: %s", NotPii(e))

    for key, value in updates.items():
        if key in current_config:
            current_config[key].update(value)
        else:
            current_config.update({key: value})

    with open(config_path, "w") as config_file:  # pylint: disable=W1514
        toml.dump(current_config, config_file)

    logger.info(f"Updated {config_path}:")

    for key, value in updates.items():
        for subkey, val in value.items():
            logger.info("\tSet %s.%s = %s", NotPii(key), NotPii(subkey), NotPii(val))


config = get_config(FidesopsConfig)
# `censored_config` is included below because it's important we keep the censored
# config at parity with `config`. This means if we change the path at which fidesops
# loads `config`, we should also change `censored_config`.
censored_config = get_censored_config(config)

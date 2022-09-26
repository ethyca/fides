# pylint: disable=C0115,C0116, E0213

import logging
import os
from typing import Any, Dict, List, MutableMapping, Optional
from urllib.parse import quote_plus

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
from toml import dump

from fidesops.ops.api.v1.scope_registry import SCOPE_REGISTRY

logger = logging.getLogger(__name__)


class FidesopsDatabaseSettings(DatabaseSettings):
    """Configuration settings for Postgres."""

    ENABLED: bool = True

    class Config:
        env_prefix = "FIDESOPS__DATABASE__"


class ExecutionSettings(FidesSettings):
    """Configuration settings for execution."""

    privacy_request_delay_timeout: int = 3600
    task_retry_count: int
    task_retry_delay: int  # In seconds
    task_retry_backoff: int
    subject_identity_verification_required: bool = False
    require_manual_request_approval: bool = False
    masking_strict: bool = True
    worker_enabled: bool = True
    celery_config_path: Optional[str] = "celery.toml"

    class Config:
        env_prefix = "FIDESOPS__EXECUTION__"


class RedisSettings(FidesSettings):
    """Configuration settings for Redis."""

    host: str
    port: int = 6379
    user: Optional[str] = ""
    password: str
    charset: str = "utf8"
    decode_responses: bool = True
    default_ttl_seconds: int = 604800
    identity_verification_code_ttl_seconds: int = 600
    db_index: Optional[int]
    enabled: bool = True
    ssl: bool = False
    ssl_cert_reqs: Optional[str] = "required"
    connection_url: Optional[str] = None

    @validator("connection_url", pre=True)
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

        return f"redis://{quote_plus(values.get('user', ''))}:{quote_plus(values['password'])}@{values['host']}:{values['port']}/{values.get('db_index', '')}"

    class Config:
        env_prefix = "FIDESOPS__REDIS__"


class FidesopsSecuritySettings(SecuritySettings):
    """Configuration settings for Security variables."""

    log_level: str = "INFO"
    root_user_scopes: Optional[List[str]] = SCOPE_REGISTRY
    subject_request_download_link_ttl_seconds: Optional[int] = 86400

    @validator("log_level", pre=True)
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

    analytics_opt_out: Optional[bool]
    analytics_id: Optional[str]

    @validator("analytics_id", pre=True)
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
        update_obj.update(root_user={"analytics_id": client_id})
        update_config_file(update_obj)
        return client_id

    class Config:
        env_prefix = "FIDESOPS__ROOT_USER__"


class AdminUiSettings(FidesSettings):
    """Configuration settings for Analytics variables."""

    enabled: bool = True

    class Config:
        env_prefix = "FIDESOPS__ADMIN_UI__"


class FidesopsNotificationSettings(FidesSettings):
    """Configuration settings for data subject and/or data processor notifications"""

    send_request_completion_notification: Optional[bool] = True
    send_request_receipt_notification: Optional[bool] = True
    send_request_review_notification: Optional[bool] = True

    class Config:
        env_prefix = "FIDESOPS__NOTIFICATIONS__"


class FidesopsConfig(FidesSettings):
    """Configuration variables for the FastAPI project"""

    database: FidesopsDatabaseSettings
    redis: RedisSettings
    security: FidesopsSecuritySettings
    execution: ExecutionSettings
    root_user: RootUserSettings
    admin_ui: AdminUiSettings
    notifications: FidesopsNotificationSettings

    port: int
    is_test_mode: bool = os.getenv("TESTING", "").lower() == "true"
    hot_reloading: bool = os.getenv("FIDESOPS__HOT_RELOAD", "").lower() == "true"
    dev_mode: bool = os.getenv("FIDESOPS__DEV_MODE", "").lower() == "true"
    oauth_instance: Optional[str] = os.getenv("FIDESOPS__OAUTH_INSTANCE")

    class Config:  # pylint: disable=C0115
        case_sensitive = True

    logger.warning(
        "Startup configuration: reloading = %s, dev_mode = %s", hot_reloading, dev_mode
    )
    logger.warning(
        "Startup configuration: pii logging = %s",
        os.getenv("FIDESOPS__LOG_PII", "").lower() == "true",
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
                    settings.Config.env_prefix,  # type: ignore
                    key,
                    value,
                )


CONFIG_KEY_ALLOWLIST = {
    "database": [
        "server",
        "user",
        "port",
        "db",
        "test_db",
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
        "subject_request_download_link_ttl_seconds",
    ],
    "execution": [
        "task_retry_count",
        "task_retry_delay",
        "task_retry_backoff",
        "require_manual_request_approval",
        "subject_identity_verification_required",
    ],
    "notifications": ["send_request_completion_notification"],
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
        logger.warning("fidesops.toml could not be loaded: %s", e)

    for key, value in updates.items():
        if key in current_config:
            current_config[key].update(value)
        else:
            current_config.update({key: value})

    with open(config_path, "w") as config_file:  # pylint: disable=W1514
        dump(current_config, config_file)

    logger.info("Updated %s:", config_path)

    for key, value in updates.items():
        for subkey, val in value.items():
            logger.info("\tSet %s.%s = %s", key, subkey, val)


config = get_config(FidesopsConfig)
# `censored_config` is included below because it's important we keep the censored
# config at parity with `config`. This means if we change the path at which fidesops
# loads `config`, we should also change `censored_config`.
censored_config = get_censored_config(config)

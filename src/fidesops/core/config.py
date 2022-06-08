# pylint: disable=C0115,C0116, E0213

import hashlib
import logging
import os
from typing import Any, Dict, List, MutableMapping, Optional, Tuple, Union

import bcrypt
import toml
from fideslog.sdk.python.utils import FIDESOPS, generate_client_id
from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, ValidationError, validator
from pydantic.env_settings import SettingsSourceCallable

from fidesops.common_exceptions import MissingConfig
from fidesops.util.logger import NotPii

logger = logging.getLogger(__name__)


class FidesSettings(BaseSettings):
    """Class used as a base model for configuration subsections."""

    class Config:

        # Set environment variables to take precedence over init values
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings


class DatabaseSettings(FidesSettings):
    """Configuration settings for Postgres."""

    SERVER: str
    USER: str
    PASSWORD: str
    DB: str
    PORT: str = "5432"
    TEST_DB: str = "test"
    ENABLED: bool = True

    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    SQLALCHEMY_TEST_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, str]) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values["USER"],
            password=values["PASSWORD"],
            host=values["SERVER"],
            port=values.get("PORT"),
            path=f"/{values.get('DB') or ''}",
        )

    @validator("SQLALCHEMY_TEST_DATABASE_URI", pre=True)
    def assemble_test_db_connection(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values["USER"],
            password=values["PASSWORD"],
            host=values["SERVER"],
            port=values["PORT"],
            path=f"/{values.get('TEST_DB') or ''}",
        )

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

    class Config:
        env_prefix = "FIDESOPS__EXECUTION__"


class PackageSettings(FidesSettings):
    """Configuration settings for the fidesops package itself."""

    PATH: Optional[str] = None

    @validator("PATH", pre=True)
    def ensure_valid_package_path(cls, v: Optional[str]) -> str:
        """
        Ensure a valid path to the fidesops src/ directory is provided.

        This is required to enable fidesops-plus to start successfully.
        """

        if isinstance(v, str) and os.path.isdir(v):
            return (
                v if os.path.basename(v) == "fidesops" else os.path.join(v, "fidesops/")
            )

        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(current_dir, "../../"))

    class Config:
        env_prefix = "FIDESOPS__PACKAGE__"


class RedisSettings(FidesSettings):
    """Configuration settings for Redis."""

    HOST: str
    PORT: int = 6379
    PASSWORD: str
    CHARSET: str = "utf8"
    DECODE_RESPONSES: bool = True
    DEFAULT_TTL_SECONDS: int = 604800
    DB_INDEX: int
    ENABLED: bool = True
    SSL: bool = False
    SSL_CERT_REQS: Optional[str] = "required"

    class Config:
        env_prefix = "FIDESOPS__REDIS__"


class SecuritySettings(FidesSettings):
    """Configuration settings for Security variables."""

    AES_ENCRYPTION_KEY_LENGTH: int = 16
    AES_GCM_NONCE_LENGTH: int = 12
    APP_ENCRYPTION_KEY: str
    DRP_JWT_SECRET: str

    @validator("APP_ENCRYPTION_KEY")
    def validate_encryption_key_length(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> Optional[str]:
        """Validate the encryption key is exactly 32 characters"""
        if v is None:
            raise ValueError("APP_ENCRYPTION_KEY value not provided!")
        encryption_key = v.encode(values.get("ENCODING", "UTF-8"))
        if len(encryption_key) != 32:
            raise ValueError(
                f"APP_ENCRYPTION_KEY value must be exactly 32 characters, "
                f"received {len(encryption_key)} characters!"
            )
        return v

    CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Return a list of valid origins for CORS requests"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    ENCODING: str = "UTF-8"

    # OAuth
    OAUTH_ROOT_CLIENT_ID: str
    OAUTH_ROOT_CLIENT_SECRET: str
    OAUTH_ROOT_CLIENT_SECRET_HASH: Optional[Tuple]
    OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    OAUTH_CLIENT_ID_LENGTH_BYTES = 16
    OAUTH_CLIENT_SECRET_LENGTH_BYTES = 16

    @validator("OAUTH_ROOT_CLIENT_SECRET_HASH", pre=True)
    def assemble_root_access_token(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> Tuple:
        """Returns a hashed value of the root access key. This is hashed as it is not wise to
        return a plaintext for of the root credential anywhere in the system"""
        value = values["OAUTH_ROOT_CLIENT_SECRET"]
        encoding = values["ENCODING"]
        assert value is not None
        assert encoding is not None
        salt = bcrypt.gensalt()
        hashed_client_id = hashlib.sha512(value.encode(encoding) + salt).hexdigest()
        return hashed_client_id, salt

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


class FidesopsConfig(FidesSettings):
    """Configuration variables for the FastAPI project"""

    database: DatabaseSettings
    package = PackageSettings()
    redis: RedisSettings
    security: SecuritySettings
    execution: ExecutionSettings
    root_user: RootUserSettings

    PORT: int
    is_test_mode: bool = os.getenv("TESTING") == "True"
    hot_reloading: bool = os.getenv("FIDESOPS__HOT_RELOAD") == "True"
    dev_mode: bool = os.getenv("FIDESOPS__DEV_MODE") == "True"

    class Config:  # pylint: disable=C0115
        case_sensitive = True

    logger.warning(
        f"Startup configuration: reloading = {hot_reloading}, dev_mode = {dev_mode}"
    )
    logger.warning(
        f'Startup configuration: pii logging = {os.getenv("FIDESOPS__LOG_PII") == "True"}'
    )

    def log_all_config_values(self) -> None:
        """Output DEBUG logs of all the config values."""
        for settings in [self.database, self.redis, self.security, self.execution]:
            for key, value in settings.dict().items():
                logger.debug(
                    "Using config: %s%s = %s",
                    NotPii(settings.Config.env_prefix),
                    NotPii(key),
                    NotPii(value),
                )


def load_file(file_name: str) -> str:
    """Load a file and from the first matching location.

    In order, will check:
    - A path set at ENV variable FIDESOPS__CONFIG_PATH
    - The current directory
    - The parent directory
    - users home (~) directory

    raises FileNotFound if none is found
    """
    possible_directories = [
        os.getenv("FIDESOPS__CONFIG_PATH"),
        os.curdir,
        os.pardir,
        os.path.expanduser("~"),
    ]

    directories: List[str] = [d for d in possible_directories if d]

    for dir_str in directories:
        possible_location = os.path.join(dir_str, file_name)
        if possible_location and os.path.isfile(possible_location):
            logger.info("Loading file %s from %s", NotPii(file_name), NotPii(dir_str))
            return possible_location
        logger.debug("%s not found at %s", NotPii(file_name), NotPii(dir_str))
    raise FileNotFoundError


def load_toml(file_name: str) -> MutableMapping[str, Any]:
    """
    Load toml file from possible locations specified in load_file.

    Will raise FileNotFoundError or ValidationError on missing or
    bad file
    """
    return toml.load(load_file(file_name))


def get_config() -> FidesopsConfig:
    """
    Attempt to read config file from:
    a) env var FIDESOPS__CONFIG_PATH
    b) local directory
    c) parent directory
    d) home directory
    This will fail on the first encountered bad conf file.
    """
    try:
        return FidesopsConfig.parse_obj(load_toml("fidesops.toml"))
    except (FileNotFoundError) as e:
        logger.warning("fidesops.toml could not be loaded: %s", NotPii(e))
        # If no path is specified Pydantic will attempt to read settings from
        # the environment. Default values will still be used if the matching
        # environment variable is not set.
        try:
            return FidesopsConfig()
        except ValidationError as exc:
            logger.error("Fidesops config could not be loaded: %s", NotPii(exc))
            # If FidesopsConfig is missing any required values Pydantic will throw
            # an ImportError. This means the config has not been correctly specified
            # so we can throw the missing config error.
            raise MissingConfig(exc.args[0])


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
        config_path: str = load_file("fidesops.toml")
        current_config: MutableMapping[str, Any] = load_toml("fidesops.toml")
    except FileNotFoundError as e:
        logger.warning("fidesops.toml could not be loaded: %s", NotPii(e))

    for key, value in updates.items():
        if key in current_config:
            current_config[key].update(value)
        else:
            current_config.update({key: value})

    with open(config_path, "w") as config_file:
        toml.dump(current_config, config_file)

    logger.info(f"Updated {config_path}:")

    for key, value in updates.items():
        for subkey, val in value.items():
            logger.info("\tSet %s.%s = %s", NotPii(key), NotPii(subkey), NotPii(val))


config = get_config()
# `censored_config` is included below because it's important we keep the censored
# config at parity with `config`. This means if we change the path at which fidesops
# loads `config`, we should also change `censored_config`.
censored_config = get_censored_config(config)

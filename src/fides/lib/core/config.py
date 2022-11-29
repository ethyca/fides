import logging
import os
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional, Tuple, Type, Union

import tomli
import validators
from fides.lib.cryptography.cryptographic_util import generate_salt, hash_with_salt
from fides.lib.exceptions import MissingConfig
from pydantic import (
    BaseSettings,
    Extra,
    PostgresDsn,
    ValidationError,
    root_validator,
    validator,
)
from pydantic.env_settings import SettingsSourceCallable

logger = logging.getLogger(__name__)


class FidesSettings(BaseSettings):
    """Class used as a base model for configuration subsections."""

    class Config:
        # Need to allow extras because the inheriting class will have more info
        extra = Extra.allow

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            """Set environment variables to take precedence over init values."""
            return env_settings, init_settings, file_secret_settings


class DatabaseSettings(FidesSettings):
    """Configuration settings for Postgres."""

    server: str
    user: str
    password: str
    db: str = "test"
    port: str = "5432"
    test_db: str = "test"

    sqlalchemy_database_uri: Optional[str] = None
    sqlalchemy_test_database_uri: Optional[str] = None

    @validator("sqlalchemy_database_uri", pre=True)
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, str]) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(v, str):
            return v
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                user=values["user"],
                password=values["password"],
                host=values["server"],
                port=values.get("port"),
                path=f"/{values.get('db') or ''}",
            )
        )

    @validator("sqlalchemy_test_database_uri", pre=True)
    @classmethod
    def assemble_test_db_connection(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(v, str):
            return v
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                user=values["user"],
                password=values["password"],
                host=values["server"],
                port=values["port"],
                path=f"/{values.get('test_db') or ''}",
            )
        )

    class Config:
        env_prefix = "FIDES__DATABASE__"


class SecuritySettings(FidesSettings):
    """Configuration settings for Security variables."""

    aes_encryption_key_length: int = 16
    aes_gcm_nonce_length: int = 12
    app_encryption_key: str
    drp_jwt_secret: Optional[str] = None
    root_username: Optional[str] = None
    root_password: Optional[str] = None
    root_user_scopes: Optional[List[str]] = None

    @validator("app_encryption_key")
    @classmethod
    def validate_encryption_key_length(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> Optional[str]:
        """Validate the encryption key is exactly 32 characters"""
        if v is None or len(v.encode(values.get("encoding", "UTF-8"))) != 32:
            raise ValueError(
                "APP_ENCRYPTION_KEY value must be exactly 32 characters long"
            )
        return v

    cors_origins: List[str] = []

    @validator("cors_origins", pre=True)
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Return a list of valid origins for CORS requests"""

        def validate(values: List[str]) -> None:
            for value in values:
                if value != "*":
                    if not validators.url(value):
                        raise ValueError(f"{value} is not a valid url")

        if isinstance(v, str) and not v.startswith("["):
            values = [i.strip() for i in v.split(",")]
            validate(values)

            return values
        if isinstance(v, (list, str)):
            validate(v)  # type: ignore

            return v
        raise ValueError(v)

    encoding: str = "UTF-8"

    # OAuth
    oauth_root_client_id: str
    oauth_root_client_secret: str
    oauth_root_client_secret_hash: Optional[Tuple]
    oauth_access_token_expire_minutes: int = 60 * 24 * 8
    oauth_client_id_length_bytes = 16
    oauth_client_secret_length_bytes = 16

    @root_validator(pre=True)
    @classmethod
    def assemble_root_access_token(cls, values: Dict[str, str]) -> Dict[str, str]:
        """Sets a hashed value of the root access key.

        This is hashed as it is not wise to return a plaintext for of the
        root credential anywhere in the system.
        """
        value = values.get("oauth_root_client_secret")
        if not value:
            raise MissingConfig(
                "oauth_root_client_secret is required", SecuritySettings
            )

        encoding = values.get("encoding", "UTF-8")

        salt = generate_salt()
        hashed_client_id = hash_with_salt(value.encode(encoding), salt.encode(encoding))
        values["oauth_root_client_secret_hash"] = (hashed_client_id, salt.encode(encoding))  # type: ignore
        return values

    class Config:
        env_prefix = "FIDES__SECURITY__"


class FidesConfig(FidesSettings):
    """Configuration variables for the FastAPI project."""

    database: DatabaseSettings
    security: SecuritySettings

    is_test_mode: bool = os.getenv("TESTING", "").lower() == "true"
    hot_reloading: bool = os.getenv("FIDES__HOT_RELOAD", "").lower() == "true"
    dev_mode: bool = os.getenv("FIDES__DEV_MODE", "").lower() == "true"

    class Config:
        case_sensitive = True


def load_file(file_names: Union[List[Path], List[str]]) -> str:
    """Load a file from the first matching location.

    In order, will check:
    - A path set at ENV variable FIDES__CONFIG_PATH
    - The current directory
    - The parent directory
    - Two directories up for the current directory
    - The parent_directory/.fides
    - users home (~) directory
    raises FileNotFound if none is found
    """

    possible_directories = [
        os.getenv("FIDES__CONFIG_PATH"),
        os.curdir,
        os.pardir,
        os.path.abspath(os.path.join(os.curdir, "..", "..")),
        os.path.join(os.pardir, ".fides"),
        os.path.expanduser("~"),
    ]

    directories = [d for d in possible_directories if d]

    for dir_str in directories:
        for file_name in file_names:
            possible_location = os.path.join(dir_str, file_name)
            if possible_location and os.path.isfile(possible_location):
                logger.info("Loading file %s from %s", file_name, dir_str)
                return possible_location

    raise FileNotFoundError


def load_toml(file_names: Union[List[Path], List[str]]) -> MutableMapping[str, Any]:
    """Load toml file from possible locations specified in load_file.

    Will raise FileNotFoundError or ValidationError on missing or
    bad file
    """
    file_name = load_file(file_names)
    with open(file_name, "rb") as f:
        return tomli.load(f)


def get_config(
    class_name: Type[FidesConfig] = FidesConfig,
    *,
    file_names: Union[List[Path], List[str]] = [
        "fidesops.toml",
        "fidesctl.toml",
        "fides.toml",
    ],
) -> FidesConfig:
    """
    Attempt to read config file named fidesops.toml, fidesctl.toml, or fides.toml from:
    - env var FIDES__CONFIG_PATH
    - local directory
    - parent directory
    - home directory
    This will fail on the first encountered bad conf file.
    """
    try:
        filenames_as_str = " or ".join([str(x) for x in file_names])
        logger.info(
            "Attempting to load application config from files: %s", filenames_as_str
        )
        return class_name.parse_obj(load_toml(file_names))
    except (FileNotFoundError) as e:
        logger.warning(
            "Application config could not be loaded from files: %s due to error: %s",
            filenames_as_str,
            e,
        )
        # If no path is specified Pydantic will attempt to read settings from
        # the environment. Default values will still be used if the matching
        # environment variable is not set.
        try:
            logger.info(
                "Attempting to load application config from environment variables"
            )
            return class_name()
        except ValidationError as exc:
            logger.error(
                "Application config could not be loaded from environment variables due to error: %s",
                exc,
            )
            # If FidesConfig is missing any required values Pydantic will throw
            # an ImportError. This means the config has not been correctly specified
            # so we can throw the missing config error.
            raise MissingConfig(exc.args[0]) from exc

"""This module handles database credentials for the application database.."""

# pylint: disable=C0115,C0116, E0213

from copy import deepcopy
from typing import Dict, Optional, cast
from urllib.parse import quote, quote_plus, urlencode

from pydantic import Field, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import SettingsConfigDict

from fides.config.utils import get_test_mode

from .fides_settings import FidesSettings, port_integer_converter

ENV_PREFIX = "FIDES__DATABASE__"


class DatabaseSettings(FidesSettings):
    """Configuration settings for the application database."""

    automigrate: bool = Field(
        default=True,
        description="Automatically runs migrations on webserver startup. If set to `false`, will require the user to run migrations manually via the CLI or API. WARNING: Must be set to `true` for first-time startup.",
    )
    # API Engine Settings
    api_engine_pool_size: int = Field(
        default=50,
        description="Number of concurrent database connections Fides will use for API requests. Note that the pool begins with no connections, but as they are requested the connections are maintained and reused up to this limit.",
    )
    api_engine_max_overflow: int = Field(
        default=50,
        description="Number of additional 'overflow' concurrent database connections Fides will use for API requests if the pool reaches the limit. These overflow connections are discarded afterwards and not maintained.",
    )
    api_engine_keepalives_idle: int = Field(
        default=30,
        description="Number of seconds of inactivity before the client sends a TCP keepalive packet to verify the database connection is still alive.",
    )
    api_engine_keepalives_interval: int = Field(
        default=10,
        description="Number of seconds between TCP keepalive retries if the initial keepalive packet receives no response. These are client-side retries.",
    )
    api_engine_keepalives_count: int = Field(
        default=5,
        description="Maximum number of TCP keepalive retries before the client considers the connection dead and closes it.",
    )
    api_engine_pool_pre_ping: bool = Field(
        default=True,
        description="If true, the engine will pre-ping connections to ensure they are still valid before using them.",
    )

    # Async Engine Settings
    api_async_engine_keepalives_idle: Optional[int] = Field(
        default=None,
        description="Number of seconds of inactivity before the client sends a TCP keepalive packet to verify the database connection is still alive.",
    )
    api_async_engine_keepalives_interval: Optional[int] = Field(
        default=None,
        description="Number of seconds between TCP keepalive retries if the initial keepalive packet receives no response. These are client-side retries.",
    )
    api_async_engine_keepalives_count: Optional[int] = Field(
        default=None,
        description="Maximum number of TCP keepalive retries before the client considers the connection dead and closes it.",
    )
    api_async_engine_pool_pre_ping: bool = Field(
        default=True,
        description="If true, the async engine will pre-ping connections to ensure they are still valid before using them.",
    )

    db: str = Field(
        default="default_db", description="The name of the application database."
    )
    load_samples: bool = Field(
        default=False,
        description=(
            "When set to True, initializes the database with sample data for testing (Systems, Datasets, Connectors, etc.) "
            "Used by 'fides deploy' to configure the sample project."
        ),
    )
    password: str = Field(
        default="defaultpassword",
        description="The password with which to login to the application database.",
    )
    port: str = Field(
        default="5432",
        description="The port at which the application database will be accessible.",
    )
    server: str = Field(
        default="default-db",
        description="The hostname of the application database server.",
    )
    readonly_server: Optional[str] = Field(
        default=None,
        description="The hostname of the application read database server.",
    )

    # TODO (LJ-663): add optional readonly_user
    # TODO (LJ-663): add optional readonly_password
    # TODO (LJ-663): add optional readonly_port
    # TODO (LJ-663): add optional readonly_params
    # TODO (LJ-663): add optional readonly_db

    task_engine_pool_size: int = Field(
        default=50,
        description="Number of concurrent database connections Fides will use for executing privacy request tasks, either locally or on each worker. Note that the pool begins with no connections, but as they are requested the connections are maintained and reused up to this limit.",
    )
    task_engine_max_overflow: int = Field(
        default=50,
        description="Number of additional 'overflow' concurrent database connections Fides will use for executing privacy request tasks, either locally or on each worker, if the pool reaches the limit. These overflow connections are discarded afterwards and not maintained.",
    )
    task_engine_keepalives_idle: int = Field(
        default=30,
        description="Number of seconds of inactivity before the client sends a TCP keepalive packet to verify the database connection is still alive.",
    )
    task_engine_keepalives_interval: int = Field(
        default=10,
        description="Number of seconds between TCP keepalive retries if the initial keepalive packet receives no response. These are client-side retries.",
    )
    task_engine_keepalives_count: int = Field(
        default=5,
        description="Maximum number of TCP keepalive retries before the client considers the connection dead and closes it.",
    )
    task_engine_pool_pre_ping: bool = Field(
        default=True,
        description="If true, the engine will pre-ping connections to ensure they are still valid before using them.",
    )
    test_db: str = Field(
        default="default_test_db",
        description="Used instead of the 'db' value when the FIDES_TEST_MODE environment variable is set to True. Avoids overwriting production data.",
        exclude=True,
    )
    user: str = Field(
        default="defaultuser",
        description="The database user with which to login to the application database.",
    )
    params: Dict = Field(
        default={},  # Can't use the default_factory since it breaks docs generation
        description="Additional connection parameters used when connecting to the application database.",
    )

    # These must be at the end because they require other values to construct
    sqlalchemy_database_uri: str = Field(
        default="",
        description="Programmatically created connection string for the application database.",
        exclude=True,
    )
    sqlalchemy_readonly_database_uri: Optional[str] = Field(
        default=None,
        description="Programmatically created connection string for the read-only application database.",
        exclude=True,
    )
    sqlalchemy_test_database_uri: str = Field(
        default="",
        description="Programmatically created connection string for the test database.",
        exclude=True,
    )
    async_database_uri: str = Field(
        default="",
        description="Programmatically created asynchronous connection string for the configured database (either application or test).",
        exclude=True,
    )
    sync_database_uri: str = Field(
        default="",
        description="Programmatically created synchronous connection string for the configured database (either application or test).",
        exclude=True,
    )

    @field_validator("password", mode="before")
    @classmethod
    def escape_password(cls, value: Optional[str]) -> Optional[str]:
        """Escape password"""
        if value and isinstance(value, str):
            return quote_plus(value)
        return value

    @field_validator("sync_database_uri", mode="before")
    @classmethod
    def assemble_sync_database_uri(
        cls, value: Optional[str], info: ValidationInfo
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(value, str) and value:
            return value

        port: int = port_integer_converter(info)
        db_name = info.data.get("test_db") if get_test_mode() else info.data.get("db")
        return str(
            PostgresDsn.build(  # pylint: disable=no-member
                scheme="postgresql+psycopg2",
                username=info.data.get("user"),
                password=info.data.get("password"),
                host=info.data.get("server"),
                port=port,
                path=f"{db_name or ''}",
                query=(
                    urlencode(
                        cast(Dict, info.data.get("params")), quote_via=quote, safe="/"
                    )
                    if info.data.get("params")
                    else None
                ),
            )
        )

    @field_validator("async_database_uri", mode="before")
    @classmethod
    def assemble_async_database_uri(
        cls, value: Optional[str], info: ValidationInfo
    ) -> str:
        """Join DB connection credentials into an async connection string."""
        if isinstance(value, str) and value:
            return value

        db_name = info.data.get("test_db") if get_test_mode() else info.data.get("db")

        # Workaround https://github.com/MagicStack/asyncpg/issues/737
        # Required due to the unique way in which Asyncpg handles SSL
        params = cast(Dict, deepcopy(info.data.get("params")))
        if "sslmode" in params:
            params["ssl"] = params.pop("sslmode")
        # This must be constructed in fides.api.db.session as part of the ssl context
        # ref: https://github.com/sqlalchemy/sqlalchemy/discussions/5975
        params.pop("sslrootcert", None)
        # End workaround

        port: int = port_integer_converter(info)
        return str(
            PostgresDsn.build(  # pylint: disable=no-member
                scheme="postgresql+asyncpg",
                username=info.data.get("user"),
                password=info.data.get("password"),
                host=info.data.get("server"),
                port=port,
                path=f"{db_name or ''}",
                query=urlencode(params, quote_via=quote, safe="/") if params else None,
            )
        )

    @field_validator("sqlalchemy_database_uri", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Join DB connection credentials into a synchronous connection string."""
        if isinstance(v, str) and v:
            return v

        port: int = port_integer_converter(info)
        return str(
            PostgresDsn.build(  # pylint: disable=no-member
                scheme="postgresql",
                username=info.data.get("user"),
                password=info.data.get("password"),
                host=info.data.get("server"),
                port=port,
                path=f"{info.data.get('db') or ''}",
                query=(
                    urlencode(
                        cast(Dict, info.data.get("params")), quote_via=quote, safe="/"
                    )
                    if info.data.get("params")
                    else None
                ),
            )
        )

    @field_validator("sqlalchemy_readonly_database_uri", mode="before")
    @classmethod
    def assemble_readonly_db_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        """Join DB connection credentials into a synchronous connection string."""
        if isinstance(v, str) and v:
            return v
        if not info.data.get("readonly_server"):
            return None
        port: int = port_integer_converter(info)
        return str(
            # TODO: support optional readonly params for user, password, etc.
            PostgresDsn.build(  # pylint: disable=no-member
                scheme="postgresql",
                username=info.data.get("user"),
                password=info.data.get("password"),
                host=info.data.get("readonly_server"),
                port=port,
                path=f"{info.data.get('db') or ''}",
                query=(
                    urlencode(
                        cast(Dict, info.data.get("params")), quote_via=quote, safe="/"
                    )
                    if info.data.get("params")
                    else None
                ),
            )
        )

    @field_validator("sqlalchemy_test_database_uri", mode="before")
    @classmethod
    def assemble_test_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(v, str) and v:
            return v

        port: int = port_integer_converter(info)
        return str(
            PostgresDsn.build(  # pylint: disable=no-member
                scheme="postgresql",
                username=info.data.get("user"),
                password=info.data.get("password"),
                host=info.data.get("server"),
                port=port,
                path=f"{info.data.get('test_db') or ''}",
                query=(
                    urlencode(
                        cast(Dict, info.data.get("params")), quote_via=quote, safe="/"
                    )
                    if info.data.get("params")
                    else None
                ),
            )
        )

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, coerce_numbers_to_str=True)

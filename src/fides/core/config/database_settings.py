"""This module handles database credentials for the application database.."""

# pylint: disable=C0115,C0116, E0213

from typing import Dict, Optional

from pydantic import PostgresDsn, validator, Field

from fides.core.config.utils import get_test_mode

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__DATABASE__"


class DatabaseSettings(FidesSettings):
    """Configuration settings for Postgres."""

    db: str = Field(
        default="default_db", description="The name of the application database."
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
    task_engine_pool_size: int = Field(default=50, description="TODO")
    task_engine_max_overflow: int = Field(default=50, description="TODO")
    test_db: str = Field(
        default="default_test_db",
        description="Used instead of the 'db' value when the FIDES_TEST_MODE environment variable is set to True. Avoids overwriting production data.",
        exclude=True,
    )
    user: str = Field(
        default="defaultuser",
        description="The database user with which to login to the application database.",
    )

    # These must be at the end because they require other values to construct
    sqlalchemy_database_uri: Optional[str] = Field(
        description="Generic connection string for the application database.",
        exclude=True,
    )
    sqlalchemy_test_database_uri: Optional[str] = Field(
        description="Generic connection string for the test database.", exclude=True
    )
    async_database_uri: Optional[str] = Field(
        description="Asynchronous connection string for the configured database (either application or test).",
        exclude=True,
    )
    sync_database_uri: Optional[str] = Field(
        description="Synchronous connection string for the configured database (either application or test).",
        exclude=True,
    )

    @validator("sync_database_uri", pre=True)
    @classmethod
    def assemble_sync_database_uri(
        cls, value: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(value, str) and value != "":
            # This validates that the string is a valid PostgresDns.
            return str(PostgresDsn(value))

        db_name = values["test_db"] if get_test_mode() else values["db"]
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                user=values["user"],
                password=values["password"],
                host=values["server"],
                port=values.get("port"),
                path=f"/{db_name or ''}",
            )
        )

    @validator("async_database_uri", pre=True)
    @classmethod
    def assemble_async_database_uri(
        cls, value: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into an async connection string."""
        if isinstance(value, str) and value != "":
            # This validates that the string is a valid PostgresDns.
            return str(PostgresDsn(value))

        db_name = values["test_db"] if get_test_mode() else values["db"]
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                user=values["user"],
                password=values["password"],
                host=values["server"],
                port=values.get("port"),
                path=f"/{db_name or ''}",
            )
        )

    @validator("sqlalchemy_database_uri", pre=True)
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, str]) -> str:
        """Join DB connection credentials into a synchronous connection string."""
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
        env_prefix = ENV_PREFIX

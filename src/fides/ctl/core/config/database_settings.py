"""This module handles database credentials for the application database.."""

# pylint: disable=C0115,C0116, E0213

import logging
from typing import Dict, Optional

from fideslib.core.config import FidesSettings
from pydantic import PostgresDsn, validator

from fides.ctl.core.config.utils import get_test_mode

logger = logging.getLogger(__name__)

ENV_PREFIX = "FIDES__DATABASE__"


class DatabaseSettings(FidesSettings):
    """Configuration settings for Postgres."""

    user: str = "defaultuser"
    password: str = "defaultpassword"
    server: str = "default-db"
    port: str = "5432"
    db: str = "default_db"
    test_db: str = "default_test_db"

    sqlalchemy_database_uri: Optional[str] = None
    sqlalchemy_test_database_uri: Optional[str] = None

    # These values are set by validators, and are never empty strings within the
    # application. The default values here are required in order to prevent the
    # types being set to "Optional[str]", as they are not functionally optional.
    async_database_uri: str = ""
    sync_database_uri: str = ""

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
        """Join DB connection credentials into a connection string"""
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
        env_prefix = ENV_PREFIX

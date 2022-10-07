"""This module handles database credentials for the application database.."""

# pylint: disable=C0115,C0116, E0213

import logging
from typing import Dict, Optional

from fideslib.core.config import DatabaseSettings as FideslibDatabaseSettings
from pydantic import PostgresDsn, validator

from fides.ctl.core.config.utils import get_test_mode

logger = logging.getLogger(__name__)

ENV_PREFIX = "FIDES__DATABASE__"


class DatabaseSettings(FideslibDatabaseSettings):
    """Configuration settings for Postgres."""

    user: str = "defaultuser"
    password: str = "defaultpassword"
    server: str = "default-db"
    port: str = "5432"
    db: str = "default_db"
    test_db: str = "default_test_db"

    async_database_uri: Optional[PostgresDsn]
    sync_database_uri: Optional[str]

    @validator("sync_database_uri", pre=True)
    @classmethod
    def assemble_sync_database_uri(
        cls, value: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(value, str):
            return value

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
        if isinstance(value, str):
            return value

        db_name = values["test_db"] if get_test_mode() else values["db"]
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values["user"],
            password=values["password"],
            host=values["server"],
            port=values.get("port"),
            path=f"/{db_name or ''}",
        )

    class Config:
        env_prefix = ENV_PREFIX

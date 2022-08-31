"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213

import logging
import os
from typing import Dict, Optional

from fideslib.core.config import DatabaseSettings as FideslibDatabaseSettings
from pydantic import PostgresDsn, validator

logger = logging.getLogger(__name__)

ENV_PREFIX = "FIDES__DATABASE__"


class DatabaseSettings(FideslibDatabaseSettings):
    """Configuration settings for Postgres."""

    user: str = "postgres"
    password: str = "fides"
    server: str = "fides-db"
    port: str = "5432"
    db: str = "fides"
    test_db: str = "fides_test"

    async_database_uri: Optional[PostgresDsn]
    sync_database_uri: Optional[PostgresDsn]

    @validator("sync_database_uri", pre=True)
    @classmethod
    def assemble_sync_database_uri(
        cls, value: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(value, str):
            return value

        db_name = (
            values["test_db"]
            if os.getenv("FIDES_TEST_MODE") == "True"
            else values["db"]
        )
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            user=values["user"],
            password=values["password"],
            host=values["server"],
            port=values.get("port"),
            path=f"/{db_name or ''}",
        )

    @validator("async_database_uri", pre=True)
    @classmethod
    def assemble_async_database_uri(
        cls, value: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(value, str):
            return value

        db_name = (
            values["test_db"]
            if os.getenv("FIDES_TEST_MODE") == "True"
            else values["db"]
        )
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

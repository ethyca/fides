"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213

import os
from typing import Dict, Optional

from fideslib.core.config import DatabaseSettings
from pydantic import PostgresDsn, validator


class FidesctlDatabaseSettings(DatabaseSettings):
    """Configuration settings for Postgres."""

    async_database_uri: Optional[PostgresDsn]
    sync_database_uri: Optional[PostgresDsn]

    @staticmethod
    def default() -> "FidesctlDatabaseSettings":
        """Returns config object with default values set."""
        return FidesctlDatabaseSettings(
            user="postgres",
            password="fidesctl",
            server="fidesctl-db",
            port="5432",
            db="fidesctl",
            test_db="fidesctl_test",
        )

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
            if os.getenv("FIDESCTL_TEST_MODE") == "True"
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
            if os.getenv("FIDESCTL_TEST_MODE") == "True"
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
        env_prefix = "FIDESCTL__DATABASE__"

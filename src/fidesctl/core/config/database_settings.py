import os
from typing import Dict, Optional

from fideslib.core.config import DatabaseSettings
from pydantic import Field, PostgresDsn, validator


class FidesctlDatabaseSettings(DatabaseSettings):
    """Configuration settings for Postgres."""

    def __init__(self) -> None:
        self.user = "postgres"
        self.password = Field("fidesctl", exclude=True)
        self.server = "fidesctl-db"
        self.port = "5432"
        self.db = "fidesctl"
        self.test_db = "fidesctl_test"

    async_database_uri: Optional[PostgresDsn]
    sync_database_uri: Optional[PostgresDsn]

    @validator("sync_database_uri", pre=True)
    @classmethod
    def assemble_sync_database_uri(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(v, str):
            return v

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
        cls, v: Optional[str], values: Dict[str, str]
    ) -> str:
        """Join DB connection credentials into a connection string"""
        if isinstance(v, str):
            return v

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

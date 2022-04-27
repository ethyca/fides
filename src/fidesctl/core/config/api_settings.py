"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213

import os
from logging import DEBUG, INFO, getLevelName
from typing import Dict, Optional, Union

from pydantic import Field, validator

from .fides_settings import FidesSettings


class APISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""

    # Database
    database_user: str = "postgres"
    database_password: str = Field("fidesctl", exclude=True)
    database_host: str = "fidesctl-db"
    database_port: str = "5432"
    database_name: str = "fidesctl"
    test_database_name: str = "fidesctl_test"
    database_url: Optional[str] = Field(None, exclude=True)
    sync_database_url: Optional[str] = Field(None, exclude=True)
    async_database_url: Optional[str] = Field(None, exclude=True)

    # Logging
    log_destination: str = ""
    log_level: Union[int, str] = INFO
    log_serialization: str = ""

    @validator("database_url", always=True)
    def get_database_url(cls: FidesSettings, value: str, values: Dict) -> str:
        "Set the database_url to the test_database_url if in test mode."
        url = "{}:{}@{}:{}/{}".format(
            values["database_user"],
            values["database_password"],
            values["database_host"],
            values["database_port"],
            values["test_database_name"]
            if os.getenv("FIDESCTL_TEST_MODE") == "True"
            else values["database_name"],
        )
        return url

    @validator("sync_database_url", pre=True, always=True)
    def create_sync_database_url(cls: FidesSettings, value: str, values: Dict) -> str:
        "Create the sync database url."
        url = "postgresql+psycopg2://" + values["database_url"]
        return url

    @validator("async_database_url", pre=True, always=True)
    def create_async_database_url(cls: FidesSettings, value: str, values: Dict) -> str:
        "Create the async database url."
        url = "postgresql+asyncpg://" + values["database_url"]
        return url

    @validator("log_destination", pre=True)
    def get_log_destination(cls: FidesSettings, value: str) -> str:
        """
        Print logs to sys.stdout, unless a valid file path is specified.
        """
        return value if os.path.exists(value) else ""

    @validator("log_level", pre=True)
    def get_log_level(cls: FidesSettings, value: str) -> str:
        """
        Set the log_level to DEBUG if in test mode, INFO by default.
        Ensures that the string-form of a valid logging._Level is
        always returned.
        """
        if os.getenv("FIDESCTL_TEST_MODE") == "True":
            return getLevelName(DEBUG)

        if isinstance(value, str):
            value = value.upper()

        return value if getLevelName(value) != f"Level {value}" else getLevelName(INFO)

    @validator("log_serialization", pre=True)
    def get_log_serialization(cls: FidesSettings, value: str) -> str:
        """
        Ensure that only JSON serialization, or no serialization, is used.
        """
        value = value.lower()
        return value if value == "json" else ""

    class Config:
        env_prefix = "FIDESCTL__API__"

"""This module defines the settings for everything related to the CLI."""
from os import getenv
from typing import Optional

from fideslog.sdk.python.utils import generate_client_id, FIDESCTL_CLI
from pydantic import validator

from .fides_settings import FidesSettings

# pylint: disable=C0115,C0116, E0213


class CLISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""

    local_mode: bool = False
    server_url: str = "http://localhost:8080"
    analytics_id: Optional[str]

    @validator("analytics_id", always=True)
    def ensure_analytics_id_override(cls, value: str) -> str:
        """
        Resolves the `analytics_id` value in the following order of priority:
        1. The value of the `ANALYTICS_ID_OVERRIDE` environment variable
        2. The value of the `FIDESCTL__CLI__ANALYTICS_ID` environment variable
        3. The value included in the config file
        4. A newly generated value
        """

        override_id = getenv("ANALYTICS_ID_OVERRIDE")
        if override_id is not None and override_id != "":
            return override_id

        return value if value != "" else generate_client_id(FIDESCTL_CLI)

    class Config:
        env_prefix = "FIDESCTL__CLI__"

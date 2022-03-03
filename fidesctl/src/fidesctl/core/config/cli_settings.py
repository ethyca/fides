"""This module defines the settings for everything related to the CLI."""
from fideslog.sdk.python.utils import generate_client_id, FIDESCTL_CLI

from .fides_settings import FidesSettings

# pylint: disable=C0115,C0116, E0213


class CLISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""

    local_mode: bool = False
    server_url: str = "http://localhost:8080"
    analytics_id: str = generate_client_id(FIDESCTL_CLI)

    class Config:
        env_prefix = "FIDESCTL__CLI__"

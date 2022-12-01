"""This module defines the settings for everything related to the CLI."""
from typing import Dict, Optional

from fideslog.sdk.python.utils import FIDESCTL_CLI, generate_client_id
from pydantic import AnyHttpUrl, validator

from .fides_settings import FidesSettings

# pylint: disable=C0115,C0116, E0213
ENV_PREFIX = "FIDES__CLI__"


class CLISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""

    local_mode: bool = False
    analytics_id: str = generate_client_id(FIDESCTL_CLI)

    # These defaults are required to make connecting to
    # docker instances possible by default
    server_protocol: str = "http"
    server_host: str = "localhost"
    server_port: str = "8080"
    server_url: Optional[AnyHttpUrl]

    @validator("server_url", always=True)
    @classmethod
    def get_server_url(cls, value: str, values: Dict) -> str:
        "Create the server_url."
        host = values["server_host"]
        port = int(values["server_port"])
        protocol = values["server_protocol"]

        server_url = "{}://{}{}".format(
            protocol,
            host,
            f":{port}" if port else "",
        )

        return server_url

    @validator("analytics_id", always=True)
    def ensure_not_empty(cls, value: str) -> str:
        """
        Validate that the `analytics_id` is not `""`.
        """
        return value if value != "" else generate_client_id(FIDESCTL_CLI)

    class Config:
        env_prefix = ENV_PREFIX

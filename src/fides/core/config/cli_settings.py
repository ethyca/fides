"""This module defines the settings for everything related to the CLI."""
from typing import Dict, Optional

from fideslog.sdk.python.utils import FIDESCTL_CLI, generate_client_id
from pydantic import AnyHttpUrl, validator, Field

from .fides_settings import FidesSettings

# pylint: disable=C0115,C0116, E0213
ENV_PREFIX = "FIDES__CLI__"


class CLISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""

    analytics_id: str = Field(
        default=generate_client_id(FIDESCTL_CLI),
        description="A fully anonymized unique identifier that is automatically generated by the application and stored in the toml file.",
    )
    local_mode: bool = Field(
        default=False,
        description="When set to True, disables functionality that requires making calls to a Fides webserver.",
    )
    server_protocol: str = Field(
        default="http", description="The protocol used by the Fides webserver."
    )
    server_host: str = Field(
        default="localhost", description="The hostname of the Fides webserver."
    )
    server_port: str = Field(
        default="8080", description="The port of the Fides webserver"
    )
    server_url: Optional[AnyHttpUrl] = Field(
        default=None,
        description="The full server url generated from the other server configuration values.",
        exclude=True,
    )

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

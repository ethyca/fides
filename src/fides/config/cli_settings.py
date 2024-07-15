"""This module defines the settings for everything related to the CLI."""

from typing import Optional

from fideslang.validation import AnyHttpUrlString
from fideslog.sdk.python.utils import FIDESCTL_CLI, generate_client_id
from pydantic import Field, ValidationInfo, field_validator, SerializeAsAny
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

# pylint: disable=C0115,C0116, E0213

ENV_PREFIX = "FIDES__CLI__"


class CLISettings(FidesSettings):
    """Configuration settings for the command-line application."""

    analytics_id: str = Field(
        default=generate_client_id(FIDESCTL_CLI),
        description="A fully anonymized unique identifier that is automatically generated by the application. Used for anonymous analytics when opted-in.",
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
    server_url: SerializeAsAny[Optional[AnyHttpUrlString]] = Field(
        default=None,
        description="The full server url generated from the other server configuration values.",
        exclude=True,
    )

    @field_validator("server_url")
    @classmethod
    def get_server_url(cls, value: str, info: ValidationInfo) -> str:
        """Create the server_url."""
        host = info.data.get("server_host")
        port = int(info.data.get("server_port"))
        protocol = info.data.get("server_protocol")

        server_url = "{}://{}{}".format(
            protocol,
            host,
            f":{port}" if port else "",
        )

        return server_url

    @field_validator("analytics_id")
    def ensure_not_empty(cls, value: str) -> str:
        """
        Validate that the `analytics_id` is not `""`.
        """
        return value if value != "" else generate_client_id(FIDESCTL_CLI)

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, coerce_numbers_to_str=True)

"""This module defines the settings for everything related to the CLI."""
from typing import Dict, Optional

from fideslog.sdk.python.utils import generate_client_id, FIDESCTL_CLI
from pydantic import root_validator, validator, AnyHttpUrl

from .fides_settings import FidesSettings

# pylint: disable=C0115,C0116, E0213


class CLISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""

    local_mode: bool = False
    # Ignored due to this bug: https://github.com/samuelcolvin/pydantic/issues/3143
    server_host: AnyHttpUrl = "http://localhost"  # type: ignore
    server_port: Optional[int]
    server_url: Optional[AnyHttpUrl]
    analytics_id: str = generate_client_id(FIDESCTL_CLI)

    @root_validator(skip_on_failure=True)
    def get_database_url(cls: FidesSettings, values: Dict) -> Dict:
        """
        Create the server_url.

        This needs to be set as a root validator,
        otherwise the type errors gets suppressed.
        """
        server_host = values["server_host"]
        server_port = values["server_port"]
        values["server_url"] = "{}{}".format(
            server_host,
            ":" + str(server_port) if server_port else "",
        )
        return values

    @validator("analytics_id", always=True)
    def ensure_not_empty(cls, value: str) -> str:
        """
        Validate that the `analytics_id` is not `""`.
        """
        return value if value != "" else generate_client_id(FIDESCTL_CLI)

    class Config:
        env_prefix = "FIDESCTL__CLI__"

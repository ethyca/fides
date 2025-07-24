from enum import Enum
from typing import ClassVar, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MySQLSSLMode(str, Enum):
    preferred = "preferred"
    required = "required"
    disabled = "disabled"
    none = ""


class MySQLSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MySQL Database"""

    host: str = Field(
        title="Host",
        description="The hostname or IP address of the server where the database is running.",
    )
    port: int = Field(
        default=3306,
        title="Port",
        description="The network port number on which the server is listening for incoming connections (default: 3306).",
    )
    username: Optional[str] = Field(
        None,
        title="Username",
        description="The user account used to authenticate and access the database.",
    )
    password: Optional[str] = Field(
        None,
        title="Password",
        description="The password used to authenticate and access the database.",
        json_schema_extra={"sensitive": True},
    )
    dbname: str = Field(
        title="Database",
        description="The name of the specific database within the database server that you want to connect to.",
    )
    ssh_required: bool = Field(
        False,
        title="SSH required",
        description="Indicates whether an SSH tunnel is required for the connection. Enable this option if your MySQL server is behind a firewall and requires SSH tunneling for remote connections.",
    )
    ssl_mode: Optional[MySQLSSLMode] = Field(
        None,  # TODO: support for verify-ca and verify-full
        title="SSL Mode",
        description="The SSL mode to use for the connection. Accepted values are: 'required', 'preferred', 'disabled', or an empty value.",
    )

    _required_components: ClassVar[List[str]] = ["host", "dbname"]


class MySQLDocsSchema(MySQLSchema, NoValidationSchema):
    """MySQL Secrets Schema for API Docs"""

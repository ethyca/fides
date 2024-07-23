from typing import ClassVar, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class RedshiftSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to an Amazon Redshift cluster"""

    host: str = Field(
        title="Host",
        description="The hostname or IP address of the server where the database is running.",
    )
    port: int = Field(
        5439,
        title="Port",
        description="The network port number on which the server is listening for incoming connections (default: 5439).",
    )
    user: str = Field(
        title="Username",
        description="The user account used to authenticate and access the database.",
    )
    password: str = Field(
        title="Password",
        description="The password used to authenticate and access the database.",
        json_schema_extra={"sensitive": True},
    )
    database: str = Field(
        title="Database",
        description="The name of the specific database within the database server that you want to connect to.",
    )
    db_schema: Optional[str] = Field(
        None,
        title="Schema",
        description="The default schema to be used for the database connection (defaults to public).",
    )
    ssh_required: bool = Field(
        False,
        title="SSH required",
        description="Indicates whether an SSH tunnel is required for the connection. Enable this option if your Redshift database is behind a firewall and requires SSH tunneling for remote connections.",
    )

    _required_components: ClassVar[List[str]] = [
        "host",
        "user",
        "password",
        "database",
    ]


class RedshiftDocsSchema(RedshiftSchema, NoValidationSchema):
    """Redshift Secrets Schema for API Docs"""

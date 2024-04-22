from typing import List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class OracleDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to an Oracle database"""

    host: str = Field(
        title="Host",
        description="The hostname or IP address of the server where the database is running.",
    )
    port: int = Field(
        1521,
        title="Port",
        description="The network port number on which the server is listening for incoming connections (default: 1521).",
    )
    username: str = Field(
        title="Username",
        description="The user account used to authenticate and access the database.",
    )
    password: str = Field(
        title="Password",
        description="The password used to authenticate and access the database.",
        sensitive=True,
    )
    service_name: str = Field(
        description="A unique identifier used to establish a connection to a specific Oracle database instance within a database server.",
        title="Service name",
    )

    _required_components: List[str] = ["host", "username", "password", "service_name"]


class OracleDBDocsSchema(OracleDBSchema, NoValidationSchema):
    """Oracle DB Secrets Schema for API Docs"""

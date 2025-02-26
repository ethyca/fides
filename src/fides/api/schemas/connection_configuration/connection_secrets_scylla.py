from typing import ClassVar, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class ScyllaSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a Scylla Database"""

    host: str = Field(
        title="Host",
        description="The hostname or IP address of the server where the database is running.",
    )
    port: int = Field(
        9042,
        title="Port",
        description="The network port number on which the server is listening for incoming connections (default: 9042).",
    )
    username: str = Field(
        title="Username",
        description="The user account used to authenticate and access the database.",
    )
    password: str = Field(
        title="Password",
        description="The password used to authenticate and access the database.",
        json_schema_extra={"sensitive": True},
    )
    keyspace: Optional[str] = Field(
        default=None,
        title="Keyspace",
        description="The keyspace used. If not provided, DSRs for this integration will error. If the integration is used for D & D, then setting a keyspace is not required.",
    )

    _required_components: ClassVar[List[str]] = [
        "host",
        "username",
        "password",
    ]


class ScyllaDocsSchema(ScyllaSchema, NoValidationSchema):
    """Scylla Secrets Schema for API docs"""

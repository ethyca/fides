from typing import List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MongoDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MongoDB Database"""

    host: str = Field(
        title="Host",
        description="The hostname or IP address of the server where the database is running.",
    )
    port: int = Field(
        27017,
        title="Port",
        description="The network port number on which the server is listening for incoming connections (default: 27017).",
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
    defaultauthdb: str = Field(
        title="Default Auth DB",
        description="Used to specify the default authentication database.",
    )

    _required_components: List[str] = [
        "host",
        "username",
        "password",
        "defaultauthdb",
    ]


class MongoDBDocsSchema(MongoDBSchema, NoValidationSchema):
    """Mongo DB Secrets Schema for API docs"""

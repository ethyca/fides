from typing import List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MicrosoftSQLServerSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MS SQL Database

    connection string takes the format:
    mssql+pymssql://[username]:[password]@[host]:[port]/[dbname]

    """

    host: str = Field(
        title="Host",
        description="The hostname or IP address of the server where the database is running.",
    )
    port: int = Field(
        1433,
        title="Port",
        description="The network port number on which the server is listening for incoming connections (default: 1433).",
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
    dbname: str = Field(
        description="The name of the specific database within the database server that you want to connect to.",
        title="Database",
    )

    _required_components: List[str] = ["host", "username", "password", "dbname"]


class MSSQLDocsSchema(MicrosoftSQLServerSchema, NoValidationSchema):
    """MS SQL Secrets Schema for API Docs"""

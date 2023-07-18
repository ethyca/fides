from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MariaDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MariaDB Database"""

    host: str = Field(
        title="Host",
        description="The hostname or IP address of the server where the database is running.",
    )
    port: int = Field(
        3306,
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
        sensitive=True,
    )
    dbname: str = Field(
        description="The name of the specific database within the database server that you want to connect to.",
        title="Database",
    )

    _required_components: List[str] = ["host", "dbname"]


class MariaDBDocsSchema(MariaDBSchema, NoValidationSchema):
    """MariaDB Secrets Schema for API Docs"""

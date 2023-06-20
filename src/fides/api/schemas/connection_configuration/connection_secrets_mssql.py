from typing import List, Optional

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

    username: Optional[str] = None
    password: Optional[str] = Field(None, sensitive=True)
    host: Optional[str] = None
    port: Optional[int] = None
    dbname: Optional[str] = Field(None, title="DB Name")

    _required_components: List[str] = ["host"]


class MSSQLDocsSchema(MicrosoftSQLServerSchema, NoValidationSchema):
    """MS SQL Secrets Schema for API Docs"""

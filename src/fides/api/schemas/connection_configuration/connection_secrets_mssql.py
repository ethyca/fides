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

    host: str = Field(None, title="Host")  
    port: int = Field(None, title="Port")  
    username: str = Field(None, title="Username") 
    password: str = Field(None, title="Password", sensitive=True)
    dbname: Optional[str] = Field(None, title="Database")

    _required_components: List[str] = ["host","port","username","password"]


class MSSQLDocsSchema(MicrosoftSQLServerSchema, NoValidationSchema):
    """MS SQL Secrets Schema for API Docs"""

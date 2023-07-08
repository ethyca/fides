from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class PostgreSQLSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a PostgreSQL Database"""

    host: str = Field(None, title="Host")  
    port: int = Field(None, title="Port")  
    username: str = Field(None, title="Username") 
    password: str = Field(None, title="Password", sensitive=True)
    dbname: Optional[str] = Field(None, title="Database")
    db_schema: Optional[str] = Field(None, title="Schema")


    _required_components: List[str] = ["host","port","username","password"]


class PostgreSQLDocsSchema(PostgreSQLSchema, NoValidationSchema):
    """Postgres Secrets Schema for API Docs"""

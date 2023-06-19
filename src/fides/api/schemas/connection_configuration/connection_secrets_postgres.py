from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class PostgreSQLSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a PostgreSQL Database"""

    username: Optional[str] = None
    password: Optional[str] = Field(None, sensitive=True)
    dbname: Optional[str] = Field(None, title="DB Name")
    db_schema: Optional[str] = Field(None, title="DB Schema")
    host: Optional[
        str
    ] = None  # Either the entire "url" *OR* the "host" should be supplied.
    port: Optional[int] = None
    ssh_required: bool = Field(False, title="SSH Required")

    _required_components: List[str] = ["host"]


class PostgreSQLDocsSchema(PostgreSQLSchema, NoValidationSchema):
    """Postgres Secrets Schema for API Docs"""

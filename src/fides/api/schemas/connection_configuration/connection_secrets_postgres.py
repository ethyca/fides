from typing import List, Optional

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class PostgreSQLSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a PostgreSQL Database"""

    username: Optional[str] = None
    password: Optional[str] = None
    dbname: Optional[str] = None
    db_schema: Optional[str] = None
    host: Optional[
        str
    ] = None  # Either the entire "url" *OR* the "host" should be supplied.
    port: Optional[int] = None
    ssh_required: bool = False

    _required_components: List[str] = ["host"]


class PostgreSQLDocsSchema(PostgreSQLSchema, NoValidationSchema):
    """Postgres Secrets Schema for API Docs"""

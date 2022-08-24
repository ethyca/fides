from typing import List, Optional

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MySQLSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MySQL Database"""

    username: Optional[str] = None
    password: Optional[str] = None
    dbname: Optional[str] = None
    host: Optional[
        str
    ] = None  # Either the entire "url" *OR* the "host" should be supplied.
    port: Optional[int] = None

    _required_components: List[str] = ["host"]


class MySQLDocsSchema(MySQLSchema, NoValidationSchema):
    """MySQL Secrets Schema for API Docs"""

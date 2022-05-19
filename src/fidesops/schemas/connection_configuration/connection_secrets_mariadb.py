from typing import List, Optional

from fidesops.schemas.base_class import NoValidationSchema
from fidesops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MariaDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MariaDB Database"""

    username: Optional[str] = None
    password: Optional[str] = None
    dbname: Optional[str] = None
    host: Optional[
        str
    ] = None  # Either the entire "url" *OR* the "host" should be supplied.
    port: Optional[int] = None

    _required_components: List[str] = ["host"]


class MariaDBDocsSchema(MariaDBSchema, NoValidationSchema):
    """MariaDB Secrets Schema for API Docs"""

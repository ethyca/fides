from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MariaDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MariaDB Database"""

    username: Optional[str] = None
    password: Optional[str] = Field(None, sensitive=True)
    dbname: Optional[str] = Field(None, title="DB Name")
    host: Optional[
        str
    ] = None  # Either the entire "url" *OR* the "host" should be supplied.
    port: Optional[int] = None

    _required_components: List[str] = ["host"]


class MariaDBDocsSchema(MariaDBSchema, NoValidationSchema):
    """MariaDB Secrets Schema for API Docs"""

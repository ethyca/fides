from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class RedshiftSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to an Amazon Redshift cluster"""

    host: Optional[str] = None  # Endpoint of the Amazon Redshift server
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = Field(None, sensitive=True)
    db_schema: Optional[str] = Field(None, title="DB Schema")
    ssh_required: bool = Field(False, title="SSH Required")

    _required_components: List[str] = ["host", "user", "password"]


class RedshiftDocsSchema(RedshiftSchema, NoValidationSchema):
    """Redshift Secrets Schema for API Docs"""

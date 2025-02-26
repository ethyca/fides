from typing import ClassVar, List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class HttpsSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a client api"""

    url: str
    authorization: str = Field(json_schema_extra={"sensitive": True})

    _required_components: ClassVar[List[str]] = ["url", "authorization"]


class HttpsDocsSchema(HttpsSchema, NoValidationSchema):
    """HTTPS Secrets Schema for API Docs"""

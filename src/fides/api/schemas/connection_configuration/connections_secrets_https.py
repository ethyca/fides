from typing import List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class HttpsSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a client api"""

    url: str
    authorization: str = Field(sensitive=True)

    _required_components: List[str] = ["url", "authorization"]


class HttpsDocsSchema(HttpsSchema, NoValidationSchema):
    """HTTPS Secrets Schema for API Docs"""

from typing import List

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class HttpsSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a client api"""

    url: str
    authorization: str

    _required_components: List[str] = ["url", "authorization"]


class HttpsDocsSchema(HttpsSchema, NoValidationSchema):
    """HTTPS Secrets Schema for API Docs"""

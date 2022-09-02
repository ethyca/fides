from typing import List, Optional

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class EmailSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed for the EmailConnector"""

    to_email: str
    test_email: Optional[str]  # Email to send a connection test email

    _required_components: List[str] = ["to_email"]


class EmailDocsSchema(EmailSchema, NoValidationSchema):
    """EmailDocsSchema Secrets Schema for API Docs"""

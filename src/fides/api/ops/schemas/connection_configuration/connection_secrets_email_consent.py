from typing import List, Optional

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    RequiredComponentsValidator,
)


class ConsentEmailSchema(RequiredComponentsValidator):
    """Schema to validate the secrets needed for the ConsentEmailConnector"""

    third_party_vendor_name: str
    recipient_email_address: str
    test_email_address: Optional[str]

    _required_components: List[str] = [
        "recipient_email_address",
        "third_party_vendor_name",
    ]


class ConsentEmailDocsSchema(ConsentEmailSchema, NoValidationSchema):
    """ConsentEmailDocsSchema Secrets Schema for API Docs"""

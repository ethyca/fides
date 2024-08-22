from typing import Optional, Dict, Any

from fideslang.models import FidesDatasetReference
from pydantic import BaseModel, EmailStr, Extra, root_validator
from pydantic.fields import FieldInfo

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    EmailSchema,
)


class DynamicErasureEmailSchema(EmailSchema):
    """Schema to validate the secrets needed for a dynamic erasure email connector"""

    third_party_vendor_name: str
    recipient_email_address: FidesDatasetReference = FieldInfo(
        title="Recipient email address",
        external_reference=True,  # metadata added so we can identify these secret schema fields as external references
    )
    test_email_address: Optional[EmailStr] = (
        None  # Email to send a connection test email
    )


class DynamicErasureEmailDocsSchema(DynamicErasureEmailSchema, NoValidationSchema):
    """DynamicErasureEmailDocsSchema Secrets Schema for API Docs"""

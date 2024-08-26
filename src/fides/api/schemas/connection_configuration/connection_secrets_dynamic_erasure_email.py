from typing import Optional, Dict, Any

from fideslang.models import FidesDatasetReference
from pydantic import EmailStr, model_validator
from pydantic.fields import FieldInfo
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ValidationError
from fides.api.models.datasetconfig import validate_dataset_reference
from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    EmailSchema,
)


class DynamicErasureEmailSchema(EmailSchema):
    """Schema to validate the secrets needed for a dynamic erasure email connector"""

    third_party_vendor_name: str
    recipient_email_address: FidesDatasetReference = FieldInfo(
        title="Recipient email address field",
        external_reference=True,  # metadata added so we can identify these secret schema fields as external references
    )
    test_email_address: Optional[EmailStr] = (
        None  # Email to send a connection test email
    )

    @staticmethod
    def validate_recipient_email_address(
        db: Session,
        connection_secrets: "DynamicErasureEmailSchema",
    ) -> Any:
        validate_dataset_reference(db, connection_secrets.recipient_email_address)


class DynamicErasureEmailDocsSchema(DynamicErasureEmailSchema, NoValidationSchema):
    """DynamicErasureEmailDocsSchema Secrets Schema for API Docs"""

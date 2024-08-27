from typing import Any

from fideslang.models import FidesDatasetReference
from pydantic import Field
from sqlalchemy.orm import Session

from fides.api.models.datasetconfig import validate_dataset_reference
from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    BaseEmailSchema,
)


class DynamicErasureEmailSchema(BaseEmailSchema):
    """Schema to validate the secrets needed for a dynamic erasure email connector"""

    third_party_vendor_name: str
    recipient_email_address: FidesDatasetReference = Field(
        title="Recipient email address field",
        json_schema_extra={
            "external_reference": True
        },  # metadata added so we can identify these secret schema fields as external references
    )

    @staticmethod
    def validate_recipient_email_address(
        db: Session,
        connection_secrets: "DynamicErasureEmailSchema",
    ) -> Any:
        validate_dataset_reference(db, connection_secrets.recipient_email_address)


class DynamicErasureEmailDocsSchema(DynamicErasureEmailSchema, NoValidationSchema):
    """DynamicErasureEmailDocsSchema Secrets Schema for API Docs"""

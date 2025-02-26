from typing import Any

from fideslang.models import FidesDatasetReference
from pydantic import Field
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ValidationError
from fides.api.models.datasetconfig import validate_dataset_reference
from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    BaseEmailSchema,
)


class DynamicErasureEmailSchema(BaseEmailSchema):
    """
    Schema to validate the secrets needed for a dynamic erasure email connector.
    third_party_vendor_name and recipient_email_address must reference the same dataset
    and collection, e.g "dataset.publishers.vendor_name" and "dataset.publishers.email"
    """

    third_party_vendor_name: FidesDatasetReference = Field(
        title="Third party vendor name field",
        description="Dataset reference to the field containing the third party vendor name. Both third_party_vendor_name and recipient_email_address must reference the same dataset and collection.",
        json_schema_extra={
            "external_reference": True
        },  # metadata added so we can identify these secret schema fields as external references
    )
    recipient_email_address: FidesDatasetReference = Field(
        title="Recipient email address field",
        description="Dataset reference to the field containing the recipient email address. Both third_party_vendor_name and recipient_email_address must reference the same dataset and collection.",
        json_schema_extra={
            "external_reference": True
        },  # metadata added so we can identify these secret schema fields as external references
    )


class DynamicErasureEmailDocsSchema(DynamicErasureEmailSchema, NoValidationSchema):
    """DynamicErasureEmailDocsSchema Secrets Schema for API Docs"""


def validate_dynamic_erasure_email_dataset_references(
    db: Session,
    connection_secrets: "DynamicErasureEmailSchema",
) -> Any:
    """
    Validates that the provided connection secrets reference an existing datasetconfig collection,
    and that both third_party_vendor_name and recipient_email_address reference the same collection
    from the same dataset. If any of these conditions are not met, a ValidationError is raised.
    """
    validate_dataset_reference(db, connection_secrets.recipient_email_address)
    validate_dataset_reference(db, connection_secrets.third_party_vendor_name)

    if (
        connection_secrets.recipient_email_address.dataset
        != connection_secrets.third_party_vendor_name.dataset
    ):
        raise ValidationError(
            "Recipient email address and third party vendor name must reference the same dataset"
        )

    email_collection_name = connection_secrets.recipient_email_address.field.split(".")[
        0
    ]
    vendor_collection_name = connection_secrets.third_party_vendor_name.field.split(
        "."
    )[0]

    if email_collection_name != vendor_collection_name:
        raise ValidationError(
            "Recipient email address and third party vendor name must reference the same collection"
        )

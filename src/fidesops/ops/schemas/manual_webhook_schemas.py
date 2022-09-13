from typing import TYPE_CHECKING, List, Optional, Set

from fideslib.utils.text import to_snake_case
from pydantic import ConstrainedStr, conlist, validator

from fidesops.ops.schemas.base_class import BaseSchema
from fidesops.ops.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
)


class ManualWebhookFieldType(ConstrainedStr):
    """Using ConstrainedStr instead of constr to keep mypy happy"""

    min_length = 1
    max_length = 200


class ManualWebhookField(BaseSchema):
    """Schema to describe the attributes on a manual webhook field"""

    pii_field: ManualWebhookFieldType
    dsr_package_label: Optional[ManualWebhookFieldType] = None

    class Config:
        orm_mode = True


if TYPE_CHECKING:
    ManualWebhookFieldsList = List[ManualWebhookField]
else:
    ManualWebhookFieldsList = conlist(ManualWebhookField, min_items=1)


class AccessManualWebhooks(BaseSchema):
    """Expected request body for creating Access Manual Webhooks"""

    fields: ManualWebhookFieldsList

    class Config:
        orm_mode = True

    @validator("fields")
    def check_for_duplicates(
        cls, value: List[ManualWebhookField]
    ) -> List[ManualWebhookField]:
        """
        Verify that pii_fields and dsr_package_labels are unique.

        Set the dsr_package_label to a snake_cased lower case version of pii field if it doesn't exist.
        """
        unique_pii_fields: Set[str] = {field.pii_field for field in value}
        if len(value) != len(unique_pii_fields):
            raise ValueError("pii_fields must be unique")

        for field in value:
            if not field.dsr_package_label:
                field.dsr_package_label = to_snake_case(field.pii_field)

        unique_dsr_package_labels: Set[Optional[str]] = {
            field.dsr_package_label for field in value
        }
        if len(value) != len(unique_dsr_package_labels):
            # Postponing dsr_package_label uniqueness check in case we get overlaps
            # above when we fallback to converting pii_fields to dsr_package_labels
            raise ValueError("dsr_package_labels must be unique")

        return value

    @validator("fields")
    def fields_must_exist(
        cls, value: List[ManualWebhookField]
    ) -> List[ManualWebhookField]:
        """
        Verify that pii_fields and dsr_package_labels are unique.

        Set the dsr_package_label to a snake_cased lower case version of pii field if it doesn't exist.
        """
        unique_pii_fields: Set[str] = {field.pii_field for field in value}
        if len(value) != len(unique_pii_fields):
            raise ValueError("pii_fields must be unique")

        for field in value:
            if not field.dsr_package_label:
                field.dsr_package_label = to_snake_case(field.pii_field)

        unique_dsr_package_labels: Set[Optional[str]] = {
            field.dsr_package_label for field in value
        }
        if len(value) != len(unique_dsr_package_labels):
            raise ValueError("dsr_package_labels must be unique")

        return value


class AccessManualWebhookResponse(AccessManualWebhooks):
    """Expected response for accessing Access Manual Webhooks"""

    connection_config: ConnectionConfigurationResponse
    id: str

    class Config:
        orm_mode = True

from typing import TYPE_CHECKING, List, Optional, Set

from pydantic import ConstrainedStr, conlist, validator

from fides.api.ops.schemas.base_class import BaseSchema
from fides.api.ops.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
)
from fides.lib.utils.text import to_snake_case


class PIIFieldType(ConstrainedStr):
    """Using ConstrainedStr instead of constr to keep mypy happy"""

    min_length = 1
    max_length = 200
    strip_whitespace = True


class DSRLabelFieldType(ConstrainedStr):
    """Using ConstrainedStr instead of constr to keep mypy happy"""

    max_length = 200
    strip_whitespace = True


class ManualWebhookField(BaseSchema):
    """Schema to describe the attributes on a manual webhook field"""

    pii_field: PIIFieldType
    dsr_package_label: Optional[DSRLabelFieldType] = None

    @validator("dsr_package_label")
    def convert_empty_string_dsr_package_label(
        cls, value: Optional[str]
    ) -> Optional[str]:
        """
        We specifically allow the dsr_package_label to be submitted as an empty string on input,
        so converting to None here.
        """
        return None if value == "" else value

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
                field.dsr_package_label = DSRLabelFieldType(
                    to_snake_case(field.pii_field)
                )

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
                field.dsr_package_label = DSRLabelFieldType(
                    to_snake_case(field.pii_field)
                )

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

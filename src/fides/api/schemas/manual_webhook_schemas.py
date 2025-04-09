from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Literal, Optional, Set

from fideslang.validation import FidesKey
from pydantic import ConfigDict, Field, StringConstraints, model_validator

from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
)
from fides.api.util.text import to_snake_case

DSRLabelFieldType = Annotated[
    str, StringConstraints(max_length=200, strip_whitespace=True)
]


class ManualWebhookField(FidesSchema):
    """Schema to describe the attributes on a manual webhook field"""

    pii_field: Annotated[
        str, StringConstraints(min_length=1, max_length=200, strip_whitespace=True)
    ]
    types: List[Literal["string", "file"]] = ["string"]
    dsr_package_label: Optional[DSRLabelFieldType] = None
    data_categories: Optional[List[FidesKey]] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    def convert_empty_string_dsr_package_label(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert empty string dsr_package_label to None"""
        if "dsr_package_label" in values and values["dsr_package_label"] == "":
            values["dsr_package_label"] = None
        return values


if TYPE_CHECKING:
    ManualWebhookFieldsList = List[ManualWebhookField]
else:
    ManualWebhookFieldsList = Annotated[List[ManualWebhookField], Field(min_length=1)]


class AccessManualWebhooks(FidesSchema):
    """Expected request body for creating Access Manual Webhooks"""

    fields: ManualWebhookFieldsList
    model_config = ConfigDict(from_attributes=True)

    @field_validator("fields")
    @classmethod
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

    @field_validator("fields")
    @classmethod
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


class AccessManualWebhookResponse(AccessManualWebhooks):
    """Expected response for accessing Access Manual Webhooks"""

    id: str
    connection_config: ConnectionConfigurationResponse
    model_config = ConfigDict(from_attributes=True)

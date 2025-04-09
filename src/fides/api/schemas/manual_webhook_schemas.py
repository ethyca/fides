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

    @model_validator(mode="after")
    def check_for_duplicates(self) -> "AccessManualWebhooks":
        """
        Verify that pii_fields and dsr_package_labels are unique.
        Set the dsr_package_label to a snake_cased lower case version of pii field if it doesn't exist.
        """
        unique_pii_fields: Set[str] = {field.pii_field for field in self.fields}
        if len(self.fields) != len(unique_pii_fields):
            raise ValueError("pii_fields must be unique")

        for field in self.fields:
            if not field.dsr_package_label:
                field.dsr_package_label = DSRLabelFieldType(
                    to_snake_case(field.pii_field)
                )

        unique_dsr_package_labels: Set[str] = {
            field.dsr_package_label
            for field in self.fields
            if field.dsr_package_label is not None
        }
        if len(self.fields) != len(unique_dsr_package_labels):
            raise ValueError("dsr_package_labels must be unique")

        return self

    def access_field_definitions(self) -> Dict[str, Any]:
        """Shared access field definitions for manual webhook schemas"""
        field_definitions = {}
        for field in self.fields or []:
            if field.dsr_package_label:
                if "file" in field.types:
                    field_definitions[field.dsr_package_label] = (Optional[str], None)
                else:
                    field_definitions[field.dsr_package_label] = (Optional[str], None)
        return field_definitions

    def erasure_field_definitions(self) -> Dict[str, Any]:
        """Shared erasure field definitions for manual webhook schemas.
        Only string fields can be used for erasure confirmation."""
        return {
            field.dsr_package_label: (Optional[bool], None)
            for field in self.fields or []
            if field.dsr_package_label
            and "string" in field.types  # only include string fields
        }


class AccessManualWebhookResponse(AccessManualWebhooks):
    """Expected response for accessing Access Manual Webhooks"""

    id: str
    connection_config: ConnectionConfigurationResponse
    model_config = ConfigDict(from_attributes=True)

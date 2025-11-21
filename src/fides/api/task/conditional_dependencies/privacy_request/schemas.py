from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PrivacyRequestConvenienceFields(Enum):
    """Convenience fields for privacy request."""

    rule_action_types = "privacy_request.policy.rule_action_types"
    has_access_rule = "privacy_request.policy.has_access_rule"
    has_erasure_rule = "privacy_request.policy.has_erasure_rule"
    has_consent_rule = "privacy_request.policy.has_consent_rule"
    has_update_rule = "privacy_request.policy.has_update_rule"
    rule_count = "privacy_request.policy.rule_count"
    rule_names = "privacy_request.policy.rule_names"
    has_storage_destination = "privacy_request.policy.has_storage_destination"


class ConditionalDependencyFieldType(Enum):
    """Type of the field for conditional dependencies."""

    string = "string"
    boolean = "boolean"
    array = "array"
    integer = "integer"
    float = "float"
    date = "date"


class ConditionalDependencyFieldInfo(BaseModel):
    """Information about a field available for conditional dependencies."""

    field_path: PrivacyRequestConvenienceFields = Field(
        ...,
        description="Convenience field from PrivacyRequestConvenienceFields",
    )
    field_type: ConditionalDependencyFieldType = Field(
        ..., description="Type of the field from ConditionalDependencyFieldType"
    )
    description: Optional[str] = Field(None, description="Description of the field")
    is_convenience_field: bool = Field(
        False,
        description="Whether this is a convenience field (derived from other fields)",
    )

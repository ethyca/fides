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


class PrivacyRequestFields(Enum):
    """Fields for privacy request."""

    created_at = "privacy_request.created_at"
    due_date = "privacy_request.due_date"
    identity_verified_at = "privacy_request.identity_verified_at"
    location = "privacy_request.location"
    origin = "privacy_request.origin"
    requested_at = "privacy_request.requested_at"
    source = "privacy_request.source"
    submitted_by = "privacy_request.submitted_by"


class PolicyFields(Enum):
    """Fields for policy."""

    id = "privacy_request.policy.id"
    name = "privacy_request.policy.name"
    key = "privacy_request.policy.key"
    description = "privacy_request.policy.description"
    execution_timeframe = "privacy_request.policy.execution_timeframe"
    rules = "privacy_request.policy.rules"


class IdentityFields(Enum):
    """Fields for identity."""

    email = "privacy_request.identity.email"
    phone_number = "privacy_request.identity.phone_number"
    external_id = "privacy_request.identity.external_id"
    fides_user_device_id = "privacy_request.identity.fides_user_device_id"
    ljt_readerID = "privacy_request.identity.ljt_readerID"
    ga_client_id = "privacy_request.identity.ga_client_id"


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

    field_path: str = Field(
        ...,
        description="Path to the field in the PrivacyRequest",
    )
    field_type: ConditionalDependencyFieldType = Field(
        ..., description="Type of the field from ConditionalDependencyFieldType"
    )
    description: Optional[str] = Field(None, description="Description of the field")
    is_convenience_field: bool = Field(
        False,
        description="Whether this is a convenience field (derived from other fields)",
    )

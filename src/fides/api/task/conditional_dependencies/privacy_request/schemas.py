from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


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


class CustomFieldPathPrefix(Enum):
    """Valid path prefixes for custom fields in privacy request conditional dependencies.

    Custom fields are dynamically created based on privacy center configuration and
    follow these path patterns. Use these prefixes to validate that a custom field
    path has the correct structure.
    """

    policy_custom_fields = "privacy_request.policy.custom_privacy_request_fields"
    identity_custom_fields = "privacy_request.identity.custom_identity_fields"

    @classmethod
    def is_valid_custom_field_path(cls, field_path: str) -> bool:
        """Check if a field path is a valid custom field path.

        Args:
            field_path: The field path to validate

        Returns:
            True if the path starts with a valid custom field prefix, False otherwise
        """
        return any(field_path.startswith(prefix.value + ".") for prefix in cls)

    @classmethod
    def get_custom_field_name(cls, field_path: str) -> Optional[str]:
        """Extract the custom field name from a valid custom field path.

        Args:
            field_path: The field path to extract the field name from

        Returns:
            The custom field name if the path is valid, None otherwise
        """
        for prefix in cls:
            if field_path.startswith(prefix.value + "."):
                return field_path[len(prefix.value) + 1 :]
        return None


# Union type for all valid field paths
# Pydantic will validate against enum values for standard fields
# Custom field paths (dynamically created, validated at runtime) follow the pattern:
# privacy_request.policy.custom_privacy_request_fields.{field_name}
# or: privacy_request.identity.custom_identity_fields.{field_name}
ConditionalDependencyFieldPath = Union[
    PrivacyRequestFields,
    PolicyFields,
    IdentityFields,
    PrivacyRequestConvenienceFields,
    str,  # Custom field paths (must match prefix pattern, validated below)
]


class ConditionalDependencyFieldInfo(BaseModel):
    """Information about a field available for conditional dependencies."""

    field_path: ConditionalDependencyFieldPath = Field(
        ...,
        description="Path to the field in the PrivacyRequest. Must be one of the standard field paths or a valid custom field path.",
    )
    field_type: ConditionalDependencyFieldType = Field(
        ..., description="Type of the field from ConditionalDependencyFieldType"
    )
    description: Optional[str] = Field(None, description="Description of the field")
    is_convenience_field: bool = Field(
        False,
        description="Whether this is a convenience field (derived from other fields)",
    )

    @field_validator("field_path")
    @classmethod
    def validate_field_path(cls, value: Union[Enum, str]) -> Union[Enum, str]:
        """Validate that field_path is either an enum value or a valid custom field path.

        Args:
            value: The field path to validate (can be an enum member or string)

        Returns:
            The validated field path

        Raises:
            ValueError: If the field path is not valid
        """
        # If it's already an enum member, it's valid
        if isinstance(value, Enum):
            return value

        # If it's a string, check if it matches an enum value or is a valid custom field path
        if isinstance(value, str):
            # Check if it matches any enum value
            all_enum_values = (
                {field.value for field in PrivacyRequestFields}
                | {field.value for field in PolicyFields}
                | {field.value for field in IdentityFields}
                | {field.value for field in PrivacyRequestConvenienceFields}
            )

            if value in all_enum_values:
                return value

            # If it doesn't match an enum value, it must be a valid custom field path
            if not CustomFieldPathPrefix.is_valid_custom_field_path(value):
                raise ValueError(
                    f"Invalid field_path '{value}'. Must be one of the standard field paths "
                    f"or a valid custom field path starting with one of: "
                    f"{', '.join(prefix.value for prefix in CustomFieldPathPrefix)}"
                )
            return value

        return value

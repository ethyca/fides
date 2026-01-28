from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


class PrivacyRequestTopLevelFields(Enum):
    """Top level fields for privacy request."""

    privacy_request = "privacy_request"
    policy = "privacy_request.policy"
    identity = "privacy_request.identity"


class PrivacyRequestPolicyConvenienceFields(Enum):
    """Convenience fields for privacy request policy."""

    rule_action_types = "rule_action_types"
    has_access_rule = "has_access_rule"
    has_erasure_rule = "has_erasure_rule"
    has_consent_rule = "has_consent_rule"
    has_update_rule = "has_update_rule"
    rule_count = "rule_count"
    rule_names = "rule_names"
    has_storage_destination = "has_storage_destination"


class PrivacyRequestLocationConvenienceFields(Enum):
    """Convenience fields for privacy request location."""

    location_country = "location_country"
    location_groups = "location_groups"
    location_regulations = "location_regulations"


class PrivacyRequestConvenienceFields(Enum):
    """Convenience fields for privacy request."""

    # Policy convenience fields
    rule_action_types = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.rule_action_types.value}"
    has_access_rule = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_access_rule.value}"
    has_erasure_rule = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_erasure_rule.value}"
    has_consent_rule = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_consent_rule.value}"
    has_update_rule = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_update_rule.value}"
    rule_count = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.rule_count.value}"
    rule_names = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.rule_names.value}"
    has_storage_destination = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_storage_destination.value}"
    # Location hierarchy convenience fields
    location_country = f"{PrivacyRequestTopLevelFields.privacy_request.value}.{PrivacyRequestLocationConvenienceFields.location_country.value}"
    location_groups = f"{PrivacyRequestTopLevelFields.privacy_request.value}.{PrivacyRequestLocationConvenienceFields.location_groups.value}"
    location_regulations = f"{PrivacyRequestTopLevelFields.privacy_request.value}.{PrivacyRequestLocationConvenienceFields.location_regulations.value}"


class ConsentPrivacyRequestConvenienceFields(Enum):
    """Convenience fields available for consent privacy request conditions."""

    # Policy convenience fields (all available for consent)
    rule_action_types = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.rule_action_types.value}"
    has_access_rule = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_access_rule.value}"
    has_erasure_rule = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_erasure_rule.value}"
    has_consent_rule = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_consent_rule.value}"
    has_update_rule = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_update_rule.value}"
    rule_count = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.rule_count.value}"
    rule_names = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.rule_names.value}"
    has_storage_destination = f"{PrivacyRequestTopLevelFields.policy.value}.{PrivacyRequestPolicyConvenienceFields.has_storage_destination.value}"


class PrivacyRequestFields(Enum):
    """Fields for privacy request."""

    created_at = f"{PrivacyRequestTopLevelFields.privacy_request.value}.created_at"
    due_date = f"{PrivacyRequestTopLevelFields.privacy_request.value}.due_date"
    identity_verified_at = (
        f"{PrivacyRequestTopLevelFields.privacy_request.value}.identity_verified_at"
    )
    location = f"{PrivacyRequestTopLevelFields.privacy_request.value}.location"
    origin = f"{PrivacyRequestTopLevelFields.privacy_request.value}.origin"
    requested_at = f"{PrivacyRequestTopLevelFields.privacy_request.value}.requested_at"
    source = f"{PrivacyRequestTopLevelFields.privacy_request.value}.source"
    submitted_by = f"{PrivacyRequestTopLevelFields.privacy_request.value}.submitted_by"


class ConsentPrivacyRequestFields(Enum):
    """Fields available for consent privacy request conditions."""

    created_at = f"{PrivacyRequestTopLevelFields.privacy_request.value}.created_at"
    identity_verified_at = (
        f"{PrivacyRequestTopLevelFields.privacy_request.value}.identity_verified_at"
    )
    origin = f"{PrivacyRequestTopLevelFields.privacy_request.value}.origin"
    requested_at = f"{PrivacyRequestTopLevelFields.privacy_request.value}.requested_at"
    source = f"{PrivacyRequestTopLevelFields.privacy_request.value}.source"
    submitted_by = f"{PrivacyRequestTopLevelFields.privacy_request.value}.submitted_by"


class PolicyFields(Enum):
    """Fields for policy."""

    id = "privacy_request.policy.id"
    name = f"{PrivacyRequestTopLevelFields.policy.value}.name"
    key = f"{PrivacyRequestTopLevelFields.policy.value}.key"
    description = f"{PrivacyRequestTopLevelFields.policy.value}.description"
    execution_timeframe = (
        f"{PrivacyRequestTopLevelFields.policy.value}.execution_timeframe"
    )
    rules = f"{PrivacyRequestTopLevelFields.policy.value}.rules"


class ConsentPolicyFields(Enum):
    """Policy fields available for consent privacy request conditions."""

    id = "privacy_request.policy.id"
    name = f"{PrivacyRequestTopLevelFields.policy.value}.name"
    key = f"{PrivacyRequestTopLevelFields.policy.value}.key"
    description = f"{PrivacyRequestTopLevelFields.policy.value}.description"
    rules = f"{PrivacyRequestTopLevelFields.policy.value}.rules"


class IdentityFields(Enum):
    """Fields for identity."""

    email = f"{PrivacyRequestTopLevelFields.identity.value}.email"
    phone_number = f"{PrivacyRequestTopLevelFields.identity.value}.phone_number"
    external_id = f"{PrivacyRequestTopLevelFields.identity.value}.external_id"
    fides_user_device_id = (
        f"{PrivacyRequestTopLevelFields.identity.value}.fides_user_device_id"
    )
    ljt_readerID = f"{PrivacyRequestTopLevelFields.identity.value}.ljt_readerID"
    ga_client_id = f"{PrivacyRequestTopLevelFields.identity.value}.ga_client_id"


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

    Custom privacy request fields are dynamically created based on privacy center
    configuration and are stored on the privacy request itself (not the policy).
    """

    custom_privacy_request_fields = "privacy_request.custom_privacy_request_fields"

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
# privacy_request.custom_privacy_request_fields.{field_name}
ConditionalDependencyFieldPath = Union[
    PrivacyRequestFields,
    PolicyFields,
    IdentityFields,
    PrivacyRequestConvenienceFields,
    str,  # Custom field paths (must match prefix pattern, validated below)
]

# Union type for consent-specific field paths (subset of ConditionalDependencyFieldPath)
ConsentConditionalDependencyFieldPath = Union[
    ConsentPrivacyRequestFields,
    ConsentPolicyFields,
    IdentityFields,  # All identity fields are available for consent
    ConsentPrivacyRequestConvenienceFields,
    str,  # Custom field paths (still supported for consent)
]


# Fields that are NOT available for consent requests
# Used for generating helpful error messages when conditions reference unavailable fields
CONSENT_UNAVAILABLE_FIELDS: set[str] = {
    # Direct fields
    PrivacyRequestFields.due_date.value,
    PrivacyRequestFields.location.value,
    PolicyFields.execution_timeframe.value,
    # Location convenience fields
    PrivacyRequestConvenienceFields.location_country.value,
    PrivacyRequestConvenienceFields.location_groups.value,
    PrivacyRequestConvenienceFields.location_regulations.value,
}


def get_consent_unavailable_field_message(field_path: str) -> Optional[str]:
    """Get a human-readable message explaining why a field is unavailable for consent.

    Args:
        field_path: The field path that is unavailable

    Returns:
        A message explaining why the field is unavailable, or None if the field is available
    """
    field_messages = {
        PrivacyRequestFields.due_date.value: "due_date is not available for consent requests (no execution timeframe)",
        PrivacyRequestFields.location.value: "location is not captured in the consent request workflow",
        PolicyFields.execution_timeframe.value: "execution_timeframe is not applicable to consent requests",
        PrivacyRequestConvenienceFields.location_country.value: "location_country is not available (location not captured for consent)",
        PrivacyRequestConvenienceFields.location_groups.value: "location_groups is not available (location not captured for consent)",
        PrivacyRequestConvenienceFields.location_regulations.value: "location_regulations is not available (location not captured for consent)",
    }
    return field_messages.get(field_path)


def is_field_available_for_consent(field_path: str) -> bool:
    """Check if a field is available for consent request conditions.

    Args:
        field_path: The field path to check

    Returns:
        True if the field is available for consent, False otherwise
    """
    return field_path not in CONSENT_UNAVAILABLE_FIELDS


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

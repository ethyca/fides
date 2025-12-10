from typing import Any, Optional

from fides.api.models.location_regulation_selections import get_location_by_id
from fides.api.models.policy import Policy
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.privacy_request.schemas import (
    ConditionalDependencyFieldInfo,
    ConditionalDependencyFieldType,
    PrivacyRequestConvenienceFields,
    PrivacyRequestLocationConvenienceFields,
    PrivacyRequestPolicyConvenienceFields,
)


def build_convenience_field_list() -> list[ConditionalDependencyFieldInfo]:
    """Builds a list of ConditionalDependencyFieldInfo objects for convenience fields."""
    return [
        # Policy convenience fields
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.rule_action_types.value,
            field_type=ConditionalDependencyFieldType.array,
            description="List of action types from policy rules (e.g., ['access', 'erasure']). Use with list_contains operator.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.has_access_rule.value,
            field_type=ConditionalDependencyFieldType.boolean,
            description="Whether the policy has at least one rule with action_type 'access'.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.has_erasure_rule.value,
            field_type=ConditionalDependencyFieldType.boolean,
            description="Whether the policy has at least one rule with action_type 'erasure'.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.has_consent_rule.value,
            field_type=ConditionalDependencyFieldType.boolean,
            description="Whether the policy has at least one rule with action_type 'consent'.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.has_update_rule.value,
            field_type=ConditionalDependencyFieldType.boolean,
            description="Whether the policy has at least one rule with action_type 'update'.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.rule_count.value,
            field_type=ConditionalDependencyFieldType.integer,
            description="Number of rules in the policy.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.rule_names.value,
            field_type=ConditionalDependencyFieldType.array,
            description="List of rule names from the policy. Use with list_contains operator.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.has_storage_destination.value,
            field_type=ConditionalDependencyFieldType.boolean,
            description="Whether any rule in the policy has a storage destination configured.",
            is_convenience_field=True,
        ),
        # Location hierarchy convenience fields
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.location_country.value,
            field_type=ConditionalDependencyFieldType.string,
            description="The country code for the location (e.g., 'us' for 'us_ca', 'fr' for France). Use with eq operator to check if a location is in a specific country.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.location_groups.value,
            field_type=ConditionalDependencyFieldType.array,
            description="List of location groups this location belongs to (e.g., ['us'] for US states, ['eea'] for EU countries). Use with list_contains operator.",
            is_convenience_field=True,
        ),
        ConditionalDependencyFieldInfo(
            field_path=PrivacyRequestConvenienceFields.location_regulations.value,
            field_type=ConditionalDependencyFieldType.array,
            description="List of regulations applicable to this location (e.g., ['ccpa'] for California, ['gdpr'] for EU). Use with list_contains operator.",
            is_convenience_field=True,
        ),
    ]


def get_policy_convenience_fields(
    policy: Policy,
) -> dict[str, Any]:
    """Gets convenience fields for a policy."""
    extra_fields: dict[str, Any] = {}
    extra_fields["id"] = policy.id

    # Get rules for convenience field derivation
    rules = policy.rules if hasattr(policy, "rules") and policy.rules else []
    action_types = policy.get_all_action_types()

    # Add convenience fields for rules
    extra_fields[PrivacyRequestPolicyConvenienceFields.rule_action_types.value] = [
        action_type.value for action_type in action_types if action_type
    ]
    for action_type in ActionType:
        extra_fields[f"has_{action_type.value}_rule"] = action_type in action_types
    extra_fields[PrivacyRequestPolicyConvenienceFields.rule_count.value] = (
        len(rules) if rules else 0
    )
    extra_fields[PrivacyRequestPolicyConvenienceFields.rule_names.value] = [
        rule.name for rule in rules if hasattr(rule, "name") and rule.name
    ]
    extra_fields[
        PrivacyRequestPolicyConvenienceFields.has_storage_destination.value
    ] = any(
        hasattr(rule, "storage_destination") and rule.storage_destination is not None
        for rule in rules
    )
    return extra_fields


def get_location_convenience_fields(location: Optional[str]) -> dict[str, Any]:
    """Gets convenience fields for a location to support hierarchy-based conditions."""
    extra_fields: dict[str, Any] = {
        PrivacyRequestLocationConvenienceFields.location_country.value: None,
        PrivacyRequestLocationConvenienceFields.location_groups.value: [],
        PrivacyRequestLocationConvenienceFields.location_regulations.value: [],
    }

    if not location:
        return extra_fields

    location_data = get_location_by_id(location)
    if not location_data:
        return extra_fields

    # If location has parent groups, the first one is typically the country
    # (e.g., us_ca belongs to [us])
    belongs_to = location_data.belongs_to or []
    extra_fields[PrivacyRequestLocationConvenienceFields.location_groups.value] = (
        belongs_to
    )

    # Set location_country based on whether this is a country or subdivision
    if location_data.is_country:
        # If the location is already a country, use the normalized location ID
        extra_fields[PrivacyRequestLocationConvenienceFields.location_country.value] = (
            location_data.id
        )
    elif belongs_to:
        # If it's a subdivision, use the first parent (typically the country)
        # This helps with conditions like "is this a US state?"
        extra_fields[PrivacyRequestLocationConvenienceFields.location_country.value] = (
            belongs_to[0]
        )

    # Add regulations applicable to this location
    extra_fields[PrivacyRequestLocationConvenienceFields.location_regulations.value] = (
        location_data.regulation or []
    )

    return extra_fields

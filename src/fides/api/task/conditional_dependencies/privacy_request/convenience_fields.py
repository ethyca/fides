from typing import Any

from fides.api.models.policy import Policy
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.privacy_request.schemas import (
    ConditionalDependencyFieldInfo,
    ConditionalDependencyFieldType,
    PrivacyRequestConvenienceFields,
)


def build_convenience_field_list() -> list[ConditionalDependencyFieldInfo]:
    """Builds a list of ConditionalDependencyFieldInfo objects for convenience fields."""
    return [
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
    extra_fields["rule_action_types"] = [
        action_type.value for action_type in action_types if action_type
    ]
    for action_type in ActionType:
        extra_fields[f"has_{action_type.value}_rule"] = action_type in action_types
    extra_fields["rule_count"] = len(rules) if rules else 0
    extra_fields["rule_names"] = [
        rule.name for rule in rules if hasattr(rule, "name") and rule.name
    ]
    extra_fields["has_storage_destination"] = any(
        hasattr(rule, "storage_destination") and rule.storage_destination is not None
        for rule in rules
    )
    return extra_fields

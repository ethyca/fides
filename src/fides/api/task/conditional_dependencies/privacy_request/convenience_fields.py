from typing import Any

from fides.api.models.policy import Policy
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.schemas import (
    ConditionalDependencyFieldInfo,
)
from fides.api.task.conditional_dependencies.util import (
    create_conditional_dependency_field_info,
)


def build_convenience_field_list() -> list[ConditionalDependencyFieldInfo]:
    """
    Build a list of convenience fields for the privacy request.
    """

    return [
        create_conditional_dependency_field_info(
            "privacy_request.policy.rule_action_types",
            "array",
            "List of action types from policy rules (e.g., ['access', 'erasure']). Use with list_contains operator.",
            is_convenience_field=True,
        ),
        create_conditional_dependency_field_info(
            "privacy_request.policy.has_access_rule",
            "boolean",
            "Whether the policy has at least one rule with action_type 'access'.",
            is_convenience_field=True,
        ),
        create_conditional_dependency_field_info(
            "privacy_request.policy.has_erasure_rule",
            "boolean",
            "Whether the policy has at least one rule with action_type 'erasure'.",
            is_convenience_field=True,
        ),
        create_conditional_dependency_field_info(
            "privacy_request.policy.has_consent_rule",
            "boolean",
            "Whether the policy has at least one rule with action_type 'consent'.",
            is_convenience_field=True,
        ),
        create_conditional_dependency_field_info(
            "privacy_request.policy.has_update_rule",
            "boolean",
            "Whether the policy has at least one rule with action_type 'update'.",
            is_convenience_field=True,
        ),
        create_conditional_dependency_field_info(
            "privacy_request.policy.rule_count",
            "integer",
            "Number of rules in the policy.",
            is_convenience_field=True,
        ),
        create_conditional_dependency_field_info(
            "privacy_request.policy.rule_names",
            "array",
            "List of rule names from the policy. Use with list_contains operator.",
            is_convenience_field=True,
        ),
        create_conditional_dependency_field_info(
            "privacy_request.policy.has_storage_destination",
            "boolean",
            "Whether any rule in the policy has a storage destination configured.",
            is_convenience_field=True,
        ),
    ]


def get_policy_convenience_fields(
    policy: Policy,
) -> dict[str, Any]:

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
        extra_fields[f"has_{action_type.value}_rule"] = any(
            hasattr(rule, "action_type") and rule.action_type.value == action_type.value
            for rule in rules
        )
    extra_fields["rule_count"] = len(rules) if rules else 0
    extra_fields["rule_names"] = [
        rule.name for rule in rules if hasattr(rule, "name") and rule.name
    ]
    extra_fields["has_storage_destination"] = any(
        hasattr(rule, "storage_destination") and rule.storage_destination is not None
        for rule in rules
    )
    return extra_fields

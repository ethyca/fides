from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session, contains_eager

from fides.api.db.seed import (
    DEFAULT_ACCESS_POLICY,
    DEFAULT_CONSENT_POLICY,
    DEFAULT_ERASURE_POLICY,
)
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionTypeAdapter,
)
from fides.api.models.policy import Policy, Rule
from fides.api.models.policy.conditional_dependency import PolicyCondition
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.evaluator import ConditionEvaluator
from fides.api.task.conditional_dependencies.privacy_request.privacy_request_data import (
    EvaluablePrivacyRequest,
    PrivacyRequestDataTransformer,
)
from fides.api.task.conditional_dependencies.privacy_request.schemas import (
    PrivacyRequestConvenienceFields,
    PrivacyRequestFields,
)
from fides.api.task.conditional_dependencies.schemas import (
    PolicyEvaluationResult,
    PolicyEvaluationSpecificity,
)
from fides.api.task.conditional_dependencies.util import extract_field_addresses
from fides.api.util.default_policy_config import DEFAULT_POLICY_CONFIG_KEY

# Location hierarchy tiers for tiebreaking (higher = more specific)
# if 2 policies have the same specificity, the one with the higher tier will be selected
# example: policy A has location_country = US and policy B has location = US-CA -> policy B will be selected
LOCATION_HIERARCHY_TIERS: dict[str, int] = {
    PrivacyRequestFields.location.value: 4,  # Exact location (e.g., "us_ca")
    PrivacyRequestConvenienceFields.location_country.value: 3,  # Country level
    PrivacyRequestConvenienceFields.location_groups.value: 2,  # Regional groups (e.g., "eea")
    PrivacyRequestConvenienceFields.location_regulations.value: 1,  # Regulation (e.g., "gdpr")
}

# Derived constants from LOCATION_HIERARCHY_TIERS (single source of truth)
# All location-related fields
LOCATION_FIELDS: set[str] = set(LOCATION_HIERARCHY_TIERS.keys())

# Location fields that are list-valued (groups, regulations)
# These are validated differently than scalar location fields (location, location_country)
LOCATION_LIST_FIELDS: set[str] = {
    PrivacyRequestConvenienceFields.location_groups.value,
    PrivacyRequestConvenienceFields.location_regulations.value,
}

# Fields where different equality values make conditions mutually exclusive
MUTUALLY_EXCLUSIVE_FIELDS: set[str] = {
    PrivacyRequestFields.location.value,
    PrivacyRequestConvenienceFields.location_country.value,
    PrivacyRequestConvenienceFields.location_groups.value,
    PrivacyRequestConvenienceFields.location_regulations.value,
}


def calculate_specificity(
    field_addresses: set[str],
) -> PolicyEvaluationSpecificity:
    """Calculate specificity for a set of field addresses.

    Specificity is determined by:
    1. Condition count (more conditions = more specific)
    2. Location hierarchy tier (for tiebreaking - country beats regulation, etc.)

    Args:
        field_addresses: Set of field addresses from a condition tree

    Returns:
        PolicyEvaluationSpecificity with condition_count and location_tier
    """
    return PolicyEvaluationSpecificity(
        condition_count=len(field_addresses),
        location_tier=max(
            (LOCATION_HIERARCHY_TIERS.get(addr, 0) for addr in field_addresses),
            default=0,
        ),
    )


class PolicyEvaluationError(Exception):
    """Error raised when policy evaluation fails"""


class PolicyEvaluator:
    """Evaluates privacy requests against policies with conditions.

    This class handles the evaluation of privacy requests against configured policies,
    taking into account conditional logic defined in PolicyCondition records.
    """

    # Map action types to their system default policy keys (used as fallback)
    SYSTEM_DEFAULT_POLICY_KEYS: dict[ActionType, str] = {
        ActionType.access: DEFAULT_ACCESS_POLICY,
        ActionType.erasure: DEFAULT_ERASURE_POLICY,
        ActionType.consent: DEFAULT_CONSENT_POLICY,
    }

    # Keep legacy alias for backward compatibility
    DEFAULT_POLICY_KEYS = SYSTEM_DEFAULT_POLICY_KEYS

    def __init__(self, db: Session):
        """Initialize the policy evaluator.

        Args:
            db: Database session
        """
        self.db = db
        self.condition_evaluator = ConditionEvaluator(db)

    def _get_configured_default_policy_key(
        self, action_type: ActionType
    ) -> Optional[str]:
        """Get the configured default policy key from ApplicationConfig.

        Args:
            action_type: Action type to get the default for

        Returns:
            Policy key if a custom default is configured, None otherwise.
            Returns None defensively if the config structure is unexpected
            (e.g. None, wrong type) to avoid blocking policy evaluation.
        """
        api_set = ApplicationConfig.get_api_set(self.db)
        if not isinstance(api_set, dict):
            return None
        default_config = api_set.get(DEFAULT_POLICY_CONFIG_KEY)
        if not isinstance(default_config, dict):
            return None
        value = default_config.get(action_type.value)
        return value if isinstance(value, str) else None

    def evaluate_policy_conditions(
        self,
        privacy_request: EvaluablePrivacyRequest,
        action_type: ActionType,
    ) -> PolicyEvaluationResult:
        """Evaluates a privacy request against policies with conditions and returns the one
        with the highest specificity. Falls back to default policy if no conditions match.

        Specificity is determined by:
        1. Condition count (more conditions = more specific)
        2. Location hierarchy tier (for tiebreaking - country beats regulation, etc.)

        If multiple policies have identical specificity (same count AND same tier),
        raises an error since this is an ambiguous configuration.

        Args:
            privacy_request: The privacy request to evaluate
            action_type: Action type to filter policies (e.g., access, erasure)

        Returns:
            PolicyEvaluationResult with most specific matched policy or default

        Raises:
            PolicyEvaluationError: If multiple policies match with identical specificity
        """
        policy_conditions = (
            self.db.query(PolicyCondition)
            .join(Policy, PolicyCondition.policy_id == Policy.id)
            .options(contains_eager(PolicyCondition.policy))
            .join(Rule, Policy.id == Rule.policy_id)
            .filter(Rule.action_type == action_type)
        ).all()

        data_transformer = PrivacyRequestDataTransformer(privacy_request)

        # Collect all matching policies with their specificity scores
        # Each score is (condition_count, max_location_tier)
        matches: list[tuple[PolicyEvaluationSpecificity, PolicyEvaluationResult]] = []

        for policy_condition in policy_conditions:
            result = self._evaluate_single_condition(policy_condition, data_transformer)
            if result:
                logger.debug(
                    f"Policy {policy_condition.policy.key} matched with specificity "
                    f"(count={result[0].condition_count}, tier={result[0].location_tier})"
                )
                matches.append(result)

        if not matches:
            logger.debug(
                f"No policies matched for action type {action_type}, falling back to default policy"
            )
            return self._get_default_policy(action_type)

        # Sort by: condition count (desc), location tier (desc)
        matches.sort(key=lambda x: (-x[0].condition_count, -x[0].location_tier))
        best_specificity, best_match = matches[0]

        # Check for ambiguous ties - multiple policies with same specificity
        tied_policies = [m[1].policy.key for m in matches if m[0] == best_specificity]
        if len(tied_policies) > 1:
            raise PolicyEvaluationError(
                f"Ambiguous policy match: policies {tied_policies} have identical "
                f"specificity (count={best_specificity.condition_count}, tier={best_specificity.location_tier}) "
                f"for this privacy request. Please adjust policy conditions to resolve "
                f"the ambiguity by making one policy more specific than the other."
            )

        logger.debug(
            f"Selected policy {best_match.policy.key} with specificity "
            f"(count={best_specificity.condition_count}, tier={best_specificity.location_tier}) "
            f"from {len(matches)} matching policies"
        )

        return best_match

    def _evaluate_single_condition(
        self,
        policy_condition: PolicyCondition,
        data_transformer: PrivacyRequestDataTransformer,
    ) -> Optional[tuple[PolicyEvaluationSpecificity, PolicyEvaluationResult]]:
        """Evaluate a single policy condition.

        Args:
            policy_condition: The policy condition to evaluate
            data_transformer: Transformer for privacy request data

        Returns:
            tuple of (PolicyEvaluationSpecificity, PolicyEvaluationResult) if matches, None otherwise

        Raises:
            PolicyEvaluationError: If condition tree is malformed or evaluation fails unexpectedly
        """
        condition_tree = ConditionTypeAdapter.validate_python(
            policy_condition.condition_tree
        )

        field_addresses = extract_field_addresses(condition_tree)
        evaluation_result = self.condition_evaluator.evaluate_rule(
            condition_tree, data_transformer.to_evaluation_data(field_addresses)
        )

        if not evaluation_result.result:
            return None

        specificity = calculate_specificity(field_addresses)

        return (
            specificity,
            PolicyEvaluationResult(
                policy=policy_condition.policy,
                evaluation_result=evaluation_result,
                is_default=False,
            ),
        )

    def _get_default_policy(self, action_type: ActionType) -> PolicyEvaluationResult:
        """Get default policy for the given action type.

        First checks for a custom default policy configured via the API.
        If the custom default exists and is valid, uses it.
        Falls back to the system default if no custom default is configured
        or if the configured custom default policy no longer exists.

        Args:
            action_type: Action type to filter policies

        Returns:
            PolicyEvaluationResult with default policy

        Raises:
            PolicyEvaluationError: If no default policy found (neither custom nor system)
        """
        # First, check for a custom default policy
        custom_default_key = self._get_configured_default_policy_key(action_type)

        if custom_default_key:
            policy = Policy.get_by(self.db, field="key", value=custom_default_key)
            if policy:
                # Verify the policy still has rules for this action type
                if policy.get_rules_for_action(action_type):
                    logger.debug(
                        f"Using custom default policy '{custom_default_key}' for action type {action_type}"
                    )
                    return PolicyEvaluationResult(
                        policy=policy, evaluation_result=None, is_default=True
                    )
                else:
                    logger.warning(
                        f"Custom default policy '{custom_default_key}' no longer has rules "
                        f"for action type {action_type}, falling back to system default"
                    )
            else:
                logger.warning(
                    f"Custom default policy '{custom_default_key}' not found, "
                    f"falling back to system default"
                )

        # Fall back to system default policy
        system_default_key = self.SYSTEM_DEFAULT_POLICY_KEYS.get(action_type)

        policy = (
            Policy.get_by(self.db, field="key", value=system_default_key)
            if system_default_key
            else None
        )

        if not policy:
            raise PolicyEvaluationError(
                f"Default policy not found for action type: {action_type}. "
                f"No custom default is configured and system default '{system_default_key}' does not exist. "
                f"Ensure the system has been properly seeded."
            )

        logger.debug(
            f"Using system default policy '{system_default_key}' for action type {action_type}"
        )

        return PolicyEvaluationResult(
            policy=policy, evaluation_result=None, is_default=True
        )

from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session, contains_eager

from fides.api.db.seed import (
    DEFAULT_ACCESS_POLICY,
    DEFAULT_CONSENT_POLICY,
    DEFAULT_ERASURE_POLICY,
)
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionTypeAdapter,
)
from fides.api.models.policy import Policy, Rule
from fides.api.models.policy.conditional_dependency import PolicyCondition
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.evaluator import ConditionEvaluator
from fides.api.task.conditional_dependencies.privacy_request.privacy_request_data import (
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

    # Map action types to their default policy keys
    DEFAULT_POLICY_KEYS: dict[ActionType, str] = {
        ActionType.access: DEFAULT_ACCESS_POLICY,
        ActionType.erasure: DEFAULT_ERASURE_POLICY,
        ActionType.consent: DEFAULT_CONSENT_POLICY,
    }

    def __init__(self, db: Session):
        """Initialize the policy evaluator.

        Args:
            db: Database session
        """
        self.db = db
        self.condition_evaluator = ConditionEvaluator(db)

    def evaluate_policy_conditions(
        self,
        privacy_request: PrivacyRequest,
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
            result = self._evaluate_single_condition(
                policy_condition, data_transformer
            )
            if result:
                logger.debug(
                    f"Policy {policy_condition.policy.key} matched with specificity "
                    f"(count={result[0].condition_count}, tier={result[0].location_tier})"
                )
                matches.append(result)

        if not matches:
            logger.debug(f"No policies matched for action type {action_type}, falling back to default policy")
            return self._get_default_policy(action_type)

        # Sort by: condition count (desc), location tier (desc)
        matches.sort(key=lambda x: (-x[0].condition_count, -x[0].location_tier))
        best_specificity, best_match = matches[0]

        # Check for ambiguous ties - multiple policies with same specificity
        tied_policies = [
            m[1].policy.key for m in matches if m[0] == best_specificity
        ]
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
            )
        )

    def _get_default_policy(self, action_type: ActionType) -> PolicyEvaluationResult:
        """Get default policy for the given action type.

        Finds the system default policy for the action type by querying
        for the specific default policy key (e.g., "default_access_policy").

        Args:
            action_type: Action type to filter policies

        Returns:
            PolicyEvaluationResult with default policy

        Raises:
            PolicyEvaluationError: If no default policy configured or found
        """
        # Get the default policy key for this action type
        default_key = self.DEFAULT_POLICY_KEYS.get(action_type)

        # Query for the specific default policy by key
        policy = Policy.get_by(self.db, field="key", value=default_key) if default_key else None

        if not policy:
            raise PolicyEvaluationError(
                f"Default policy '{default_key}' not found for action type: {action_type}. "
                f"Ensure the system has been properly seeded."
            )

        return PolicyEvaluationResult(
            policy=policy, evaluation_result=None, is_default=True
        )

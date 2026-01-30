from typing import Dict, List, Optional

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
from fides.api.task.conditional_dependencies.schemas import (
    PolicyEvaluationResult,
)
from fides.api.task.conditional_dependencies.util import extract_field_addresses


class PolicyEvaluationError(Exception):
    """Error raised when policy evaluation fails"""


class PolicyEvaluator:
    """Evaluates privacy requests against policies with conditions.

    This class handles the evaluation of privacy requests against configured policies,
    taking into account conditional logic defined in PolicyCondition records.
    """

    # Map action types to their default policy keys
    DEFAULT_POLICY_KEYS: Dict[ActionType, str] = {
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
        """Evaluate privacy request against policies with conditions, return first match.

        Returns first matching conditional policy, or default policy if no match.

        Args:
            privacy_request: The privacy request to evaluate
            action_type: Action type to filter policies (e.g., access, erasure)

        Returns:
            PolicyEvaluationResult with matched or default policy
        """
        policy_conditions = self._query_policy_conditions(action_type)

        if not policy_conditions:
            return self._get_default_policy(action_type)

        data_transformer = PrivacyRequestDataTransformer(privacy_request)

        for policy_condition in policy_conditions:
            result = self._evaluate_single_condition(
                policy_condition, data_transformer
            )
            if result:
                return result

        return self._get_default_policy(action_type)

    def _query_policy_conditions(
        self, action_type: ActionType
    ) -> List[PolicyCondition]:
        """Query PolicyConditions filtered by action type.

        Uses eager loading to avoid N+1 queries.

        Args:
            action_type: Action type to filter by

        Returns:
            List of PolicyCondition records with policies eager-loaded
        """
        query = (
            self.db.query(PolicyCondition)
            .join(Policy, PolicyCondition.policy_id == Policy.id)
            .options(contains_eager(PolicyCondition.policy))
            .join(Rule, Policy.id == Rule.policy_id)
            .filter(Rule.action_type == action_type)
        )
        return query.all()

    def _evaluate_single_condition(
        self,
        policy_condition: PolicyCondition,
        data_transformer: PrivacyRequestDataTransformer,
    ) -> Optional[PolicyEvaluationResult]:
        """Evaluate a single policy condition.

        Args:
            policy_condition: The policy condition to evaluate
            data_transformer: Transformer for privacy request data

        Returns:
            PolicyEvaluationResult if condition matches, None otherwise
        """
        if not policy_condition.condition_tree:
            return None

        try:
            condition_tree = ConditionTypeAdapter.validate_python(
                policy_condition.condition_tree
            )
            field_addresses = extract_field_addresses(condition_tree)
            evaluation_data = data_transformer.to_evaluation_data(field_addresses)
            evaluation_result = self.condition_evaluator.evaluate_rule(
                condition_tree, evaluation_data
            )

            if evaluation_result.result:
                logger.debug(f"Policy {policy_condition.policy.key} matched")
                return PolicyEvaluationResult(
                    policy=policy_condition.policy,
                    evaluation_result=evaluation_result,
                    is_default=False,
                )
        except Exception as exc:
            logger.exception(
                f"Error evaluating policy {policy_condition.policy.key}: "
                f"{type(exc).__name__}: {exc}"
            )

        return None

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
        if not default_key:
            raise PolicyEvaluationError(
                f"No default policy configured for action type: {action_type}"
            )

        # Query for the specific default policy by key
        policy = Policy.get_by(self.db, field="key", value=default_key)

        if not policy:
            raise PolicyEvaluationError(
                f"Default policy '{default_key}' not found for action type: {action_type}. "
                f"Ensure the system has been properly seeded."
            )

        logger.debug(
            f"Using default policy '{default_key}' for action type {action_type}"
        )
        return PolicyEvaluationResult(
            policy=policy, evaluation_result=None, is_default=True
        )

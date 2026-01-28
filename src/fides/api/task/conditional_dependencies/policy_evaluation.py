from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session, contains_eager

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
from fides.api.task.conditional_dependencies.schemas import EvaluationResult
from fides.api.task.conditional_dependencies.util import extract_field_addresses


class PolicyEvaluationError(Exception):
    """Error raised when policy evaluation fails"""


class PolicyEvaluationResult:
    """Result of policy evaluation.

    Attributes:
        policy: The matched policy
        evaluation_result: Detailed evaluation report (None for default)
        is_default: Whether default policy was used
    """

    def __init__(
        self,
        policy: Policy,
        evaluation_result: Optional[EvaluationResult] = None,
        is_default: bool = False,
    ):
        self.policy = policy
        self.evaluation_result = evaluation_result
        self.is_default = is_default


def evaluate_policy_conditions(
    db: Session,
    privacy_request: PrivacyRequest,
    action_type: Optional[ActionType] = None,
) -> PolicyEvaluationResult:
    """Evaluate privacy request against policies with conditions, return first match.

    Returns first matching conditional policy, or default policy if no match.

    Args:
        db: Database session
        privacy_request: The privacy request to evaluate
        action_type: Optional action type to filter policies (e.g., access, erasure)
    """
    logger.info(
        f"Evaluating policies for request with action_type={action_type}" if action_type else "")

    # Query PolicyConditions with eager-loaded policies (single query instead of N+1)
    query = (
        db.query(PolicyCondition)
        .join(Policy, PolicyCondition.policy_id == Policy.id)
        .options(contains_eager(PolicyCondition.policy))
    )

    # Filter by action type if provided
    if action_type:
        query = query.join(Rule, Policy.id == Rule.policy_id).filter(
            Rule.action_type == action_type
        )

    policy_conditions = query.all()

    if not policy_conditions:
        # Default to access if no action_type provided
        return _get_default_policy_result(
            db, action_type or ActionType.access
        )

    evaluator = ConditionEvaluator(db)
    data_transformer = PrivacyRequestDataTransformer(privacy_request)

    for policy_condition in policy_conditions:
        if not policy_condition.condition_tree:
            continue

        try:
            root_condition = ConditionTypeAdapter.validate_python(
                policy_condition.condition_tree
            )
            field_addresses = extract_field_addresses(root_condition)
            evaluation_data = data_transformer.to_evaluation_data(field_addresses)
            evaluation_result = evaluator.evaluate_rule(root_condition, evaluation_data)

            if evaluation_result.result:
                logger.info(f"Policy {policy_condition.policy.key} matched")
                return PolicyEvaluationResult(
                    policy=policy_condition.policy,
                    evaluation_result=evaluation_result,
                    is_default=False,
                )
        except Exception as exc:
            logger.error(
                f"Error evaluating policy {policy_condition.policy.key}: "
                f"{type(exc).__name__}: {exc}",
                exc_info=True,
            )
            continue

    # Default to access if no action_type provided
    return _get_default_policy_result(
        db, action_type or ActionType.access
    )


def _get_default_policy_result(
    db: Session,
    action_type: ActionType,
) -> PolicyEvaluationResult:
    """Get default policy for the given action type.

    Finds any policy that has at least one rule with the specified action type.
    Policies can have multiple rules with different action types.

    Args:
        db: Database session
        action_type: Action type to filter policies
    """
    # Query for a policy that has at least one rule with the given action type
    # Note: A policy can have multiple rules with different action types
    policy = (
        db.query(Policy)
        .join(Rule, Policy.id == Rule.policy_id)
        .filter(Rule.action_type == action_type)
        .first()
    )

    if not policy:
        raise PolicyEvaluationError(
            f"No policy found with action type: {action_type}"
        )

    return PolicyEvaluationResult(
        policy=policy, evaluation_result=None, is_default=True
    )

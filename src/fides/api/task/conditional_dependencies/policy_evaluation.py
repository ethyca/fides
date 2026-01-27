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
    db: Session, privacy_request: PrivacyRequest, action_type: Optional[ActionType] = None
) -> PolicyEvaluationResult:
    """Evaluate privacy request against policies with conditions, return first match.

    Returns first matching conditional policy, or default policy if no match.

    Args:
        db: Database session
        privacy_request: The privacy request to evaluate
        action_type: Optional action type to filter policies (e.g., access, erasure)
    """
    logger.info(
        f"Evaluating policies for request {privacy_request.id}"
        + (f" with action_type={action_type}" if action_type else "")
    )

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

    # TODO: This is where the actual priority sort should be done, looking for
    # further information on priority.
    policy_conditions = query.order_by(Policy.created_at).all()

    if not policy_conditions:
        return _get_default_policy_result(db, privacy_request, action_type)

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
        except Exception as e:
            logger.error(f"Error evaluating policy {policy_condition.policy.key}: {e}")
            continue

    return _get_default_policy_result(db, privacy_request, action_type)


def _get_default_policy_result(
    db: Session, privacy_request: PrivacyRequest, action_type: Optional[ActionType] = None
) -> PolicyEvaluationResult:
    """Get default policy (first policy without conditions).

    Args:
        db: Database session
        privacy_request: The privacy request
        action_type: Optional action type to filter default policy
    """
    query = (
        db.query(Policy)
        .outerjoin(PolicyCondition, Policy.id == PolicyCondition.policy_id)
        .filter(PolicyCondition.id.is_(None))
    )

    # Filter by action type if provided
    if action_type:
        query = query.join(Rule, Policy.id == Rule.policy_id).filter(
            Rule.action_type == action_type
        )

    default_policy = query.order_by(Policy.created_at).first()

    if not default_policy:
        if privacy_request.policy:
            return PolicyEvaluationResult(
                policy=privacy_request.policy, evaluation_result=None, is_default=True
            )
        raise PolicyEvaluationError("No default policy configured")

    return PolicyEvaluationResult(
        policy=default_policy, evaluation_result=None, is_default=True
    )

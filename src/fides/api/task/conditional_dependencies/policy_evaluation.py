from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.policy import Policy
from fides.api.models.policy.conditional_dependency import PolicyCondition
from fides.api.models.privacy_request import PrivacyRequest
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
    db: Session, privacy_request: PrivacyRequest
) -> PolicyEvaluationResult:
    """Evaluate privacy request against policies with conditions, return first match.

    Returns first matching conditional policy, or default policy if no match.
    """
    logger.info(f"Evaluating policies for request {privacy_request.id}")

    policies_with_conditions = (
        db.query(Policy)
        .join(PolicyCondition, Policy.id == PolicyCondition.policy_id)
        .order_by(Policy.created_at)
        .all()
    )

    if not policies_with_conditions:
        return _get_default_policy_result(db, privacy_request)

    evaluator = ConditionEvaluator(db)

    for policy in policies_with_conditions:
        root_condition = PolicyCondition.get_condition_tree(db, policy_id=policy.id)

        if not root_condition:
            continue

        try:
            field_addresses = extract_field_addresses(root_condition)
            data_transformer = PrivacyRequestDataTransformer(privacy_request)
            evaluation_data = data_transformer.to_evaluation_data(field_addresses)
            evaluation_result = evaluator.evaluate_rule(root_condition, evaluation_data)

            if evaluation_result.result:
                logger.info(f"Policy {policy.key} matched")
                return PolicyEvaluationResult(
                    policy=policy, evaluation_result=evaluation_result, is_default=False
                )
        except Exception as e:
            logger.error(f"Error evaluating policy {policy.key}: {e}")
            continue

    return _get_default_policy_result(db, privacy_request)


def _get_default_policy_result(
    db: Session, privacy_request: PrivacyRequest
) -> PolicyEvaluationResult:
    """Get default policy (first policy without conditions)."""
    default_policy = (
        db.query(Policy)
        .outerjoin(PolicyCondition, Policy.id == PolicyCondition.policy_id)
        .filter(PolicyCondition.id.is_(None))
        .order_by(Policy.created_at)
        .first()
    )

    if not default_policy:
        if privacy_request.policy:
            return PolicyEvaluationResult(
                policy=privacy_request.policy, evaluation_result=None, is_default=True
            )
        raise PolicyEvaluationError("No default policy configured")

    return PolicyEvaluationResult(
        policy=default_policy, evaluation_result=None, is_default=True
    )

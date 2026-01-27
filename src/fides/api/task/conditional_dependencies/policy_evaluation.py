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
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    EvaluationResult,
)
from fides.api.task.conditional_dependencies.util import extract_field_addresses


class PolicyEvaluationError(Exception):
    """Error raised when policy evaluation fails"""


class PolicyEvaluationResult:
    """Result of evaluating a privacy request against policies with conditions.

    Attributes:
        policy: The matched policy (either conditional match or default)
        evaluation_result: Detailed evaluation report if a conditional policy matched, None for default
        is_default: Whether the default policy was used (no conditional match)
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

    def __repr__(self) -> str:
        if self.is_default:
            return f"<PolicyEvaluationResult policy={self.policy.key} (default)>"
        return f"<PolicyEvaluationResult policy={self.policy.key} matched={self.evaluation_result.result if self.evaluation_result else None}>"


def evaluate_policy_conditions(
    db: Session, privacy_request: PrivacyRequest
) -> PolicyEvaluationResult:
    """Evaluate a privacy request against all policies with conditions and return the first match.

    This function:
    1. Gets all policies with conditions, ordered by priority (to be implemented)
    2. For each policy, evaluates its root condition against the privacy request
    3. Returns the first matching policy + evaluation result
    4. Falls back to default policy if no match
    5. Returns error if no default policy configured and no match

    Args:
        db: SQLAlchemy database session
        privacy_request: The PrivacyRequest object to evaluate

    Returns:
        PolicyEvaluationResult containing the matched policy and evaluation details

    Raises:
        PolicyEvaluationError: If no matching policy found and no default policy configured

    Example:
        >>> result = evaluate_policy_conditions(db, privacy_request)
        >>> if result.is_default:
        ...     print(f"Using default policy: {result.policy.key}")
        ... else:
        ...     print(f"Matched policy: {result.policy.key}")
        ...     print(f"Evaluation: {result.evaluation_result.result}")
    """
    logger.info(
        f"Evaluating policy conditions for privacy request {privacy_request.id}"
    )

    # Get all policies with conditions
    # TODO: Add priority ordering - for now, order by created_at
    policies_with_conditions = (
        db.query(Policy)
        .join(PolicyCondition, Policy.id == PolicyCondition.policy_id)
        .order_by(Policy.created_at)
        .all()
    )

    if not policies_with_conditions:
        logger.info("No policies with conditions found, using default policy")
        return _get_default_policy_result(db, privacy_request)

    # Initialize evaluator and data transformer
    evaluator = ConditionEvaluator(db)

    # Evaluate each policy's conditions
    for policy in policies_with_conditions:
        logger.info(f"Evaluating policy: {policy.key}")

        # Get root condition for this policy
        root_condition = PolicyCondition.get_condition_tree(db, policy_id=policy.id)

        if not root_condition:
            logger.warning(
                f"Policy {policy.key} has PolicyCondition row but no condition_tree, skipping"
            )
            continue

        # Extract field addresses from the condition tree
        field_addresses = extract_field_addresses(root_condition)

        # Transform privacy request to evaluation data
        data_transformer = PrivacyRequestDataTransformer(privacy_request)
        evaluation_data = data_transformer.to_evaluation_data(field_addresses)

        # Evaluate the condition
        try:
            evaluation_result = evaluator.evaluate_rule(root_condition, evaluation_data)

            if evaluation_result.result:
                logger.info(
                    f"Policy {policy.key} conditions matched for privacy request {privacy_request.id}"
                )
                return PolicyEvaluationResult(
                    policy=policy,
                    evaluation_result=evaluation_result,
                    is_default=False,
                )
            else:
                logger.debug(
                    f"Policy {policy.key} conditions did not match: {evaluation_result.message if hasattr(evaluation_result, 'message') else 'no match'}"
                )

        except Exception as e:
            logger.error(
                f"Error evaluating policy {policy.key} conditions: {str(e)}",
                exc_info=True,
            )
            # Continue to next policy rather than failing the entire evaluation
            continue

    # No policies matched, fall back to default
    logger.info(
        f"No conditional policies matched for privacy request {privacy_request.id}, using default policy"
    )
    return _get_default_policy_result(db, privacy_request)


def _get_default_policy_result(
    db: Session, privacy_request: PrivacyRequest
) -> PolicyEvaluationResult:
    """Get the default policy result when no conditional policies match.

    Args:
        db: SQLAlchemy database session
        privacy_request: The PrivacyRequest object

    Returns:
        PolicyEvaluationResult with the default policy

    Raises:
        PolicyEvaluationError: If no default policy is configured
    """
    # For now, we'll define "default policy" as a policy without conditions
    # In the future, this could be enhanced with an explicit is_default flag
    default_policy = (
        db.query(Policy)
        .outerjoin(PolicyCondition, Policy.id == PolicyCondition.policy_id)
        .filter(PolicyCondition.id.is_(None))
        .first()
    )

    if not default_policy:
        # If the privacy request already has a policy assigned, use that as fallback
        if privacy_request.policy:
            logger.warning(
                f"No default policy found, using privacy request's assigned policy: {privacy_request.policy.key}"
            )
            return PolicyEvaluationResult(
                policy=privacy_request.policy,
                evaluation_result=None,
                is_default=True,
            )

        # No default policy and no assigned policy - this is an error condition
        raise PolicyEvaluationError(
            "No matching policy found and no default policy configured"
        )

    logger.info(f"Using default policy: {default_policy.key}")
    return PolicyEvaluationResult(
        policy=default_policy,
        evaluation_result=None,
        is_default=True,
    )

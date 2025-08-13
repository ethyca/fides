from typing import Optional, cast

from fides.api.task.conditional_dependencies.schemas import (
    ConditionEvaluationResult,
    EvaluationResult,
    GroupEvaluationResult,
)

MAX_DEPTH = 100


def format_evaluation_success_message(
    evaluation_result: Optional[EvaluationResult],
) -> str:
    """Format a detailed message about which conditions succeeded

    Args:
        evaluation_result: The evaluation result to create a string from

    Returns:
        A string describing the evaluation result

    """
    if not evaluation_result:
        return "No conditional dependencies to evaluate."

    return _format_evaluation_message(evaluation_result, success=True, depth=0)


def format_evaluation_failure_message(
    evaluation_result: Optional[EvaluationResult],
) -> str:
    """Format a detailed message about which conditions failed

    Args:
        evaluation_result: The evaluation result to create a string from

    Returns:
        A string describing the evaluation result
    """
    if not evaluation_result:
        return "No conditional dependencies to evaluate."

    return _format_evaluation_message(evaluation_result, success=False, depth=0)


def _format_leaf_condition(evaluation_result: ConditionEvaluationResult) -> str:
    """Format a single leaf condition into a readable string

    Args:
        evaluation_result: The conditionevaluation result to create a string from

    Returns:
        A string describing the evaluation result
    """
    condition_desc = f"{evaluation_result.field_address} {evaluation_result.operator}"
    if evaluation_result.expected_value is not None:
        condition_desc += f" {evaluation_result.expected_value}"
    return condition_desc


def _format_condition_list(
    results: list[EvaluationResult], success: bool, depth: int
) -> list[str]:
    """Format a list of conditions (either leaf or group) into readable strings

    Args:
        results: The list of conditions to format
        success: Whether the conditions were successful
        depth: The depth of the conditions

    Returns:
        A list of strings describing the conditions
    """
    condition_descriptions = []
    for sub_result in results:
        if _is_leaf_condition(sub_result):
            # Cast to the specific type after verification
            leaf_result = cast(ConditionEvaluationResult, sub_result)
            condition_descriptions.append(_format_leaf_condition(leaf_result))
        elif _is_group_condition(sub_result):
            # Cast to the specific type after verification
            group_result = cast(GroupEvaluationResult, sub_result)
            condition_descriptions.append(
                _format_evaluation_message(group_result, success, depth + 1)
            )
    return condition_descriptions


def _format_evaluation_message(
    evaluation_result: EvaluationResult, success: bool, depth: int = 0
) -> str:
    """Format evaluation results into a readable message

    Args:
        evaluation_result: The evaluation result to format
        success: Whether the conditions were successful
        depth: The depth of the conditions

    Returns:
        A string describing the evaluation result
    """
    # Prevent infinite recursion
    if depth > MAX_DEPTH:
        return "Condition evaluation too deeply nested"

    # Try to format as group condition first
    if _is_group_condition(evaluation_result):
        # Cast to the specific type after verification
        group_result = cast(GroupEvaluationResult, evaluation_result)
        return _format_group_condition(group_result, success, depth)

    # Try to format as leaf condition
    if _is_leaf_condition(evaluation_result):
        # Cast to the specific type after verification
        leaf_result = cast(ConditionEvaluationResult, evaluation_result)
        return _format_leaf_condition_message(leaf_result, success)

    # Unknown condition type
    return "Evaluation result details unavailable"


def _is_group_condition(evaluation_result: EvaluationResult) -> bool:
    """Check if evaluation_result is a group condition by checking for group-specific attributes

    Args:
        evaluation_result: The evaluation result to check

    Returns:
        True if the evaluation result is a group condition, False otherwise
    """
    # Check for attributes that are unique to GroupEvaluationResult
    return hasattr(evaluation_result, "logical_operator") and hasattr(
        evaluation_result, "condition_results"
    )


def _is_leaf_condition(evaluation_result: EvaluationResult) -> bool:
    """Check if evaluation_result is a leaf condition by checking for leaf-specific attributes

    Args:
        evaluation_result: The evaluation result to check

    Returns:
        True if the evaluation result is a leaf condition, False otherwise
    """
    # Check for attributes that are unique to ConditionEvaluationResult
    return hasattr(evaluation_result, "field_address") and hasattr(
        evaluation_result, "operator"
    )


def _format_group_condition(
    evaluation_result: GroupEvaluationResult, success: bool, depth: int
) -> str:
    """Format a group condition evaluation result

    Args:
        evaluation_result: The group evaluation result to format
        success: Whether the conditions were successful
        depth: The depth of the conditions

    Returns:
        A string describing the evaluation result
    """
    logical_operator = evaluation_result.logical_operator
    results = evaluation_result.condition_results
    condition_descriptions = _format_condition_list(results, success, depth)

    if success:
        return f"All conditions in {logical_operator.upper()} group were met: {'; '.join(condition_descriptions)}"

    if condition_descriptions:
        return f"Failed conditions in {logical_operator.upper()} group: {'; '.join(condition_descriptions)}"

    return f"Group condition with {logical_operator.upper()} operator failed"


def _format_leaf_condition_message(
    evaluation_result: ConditionEvaluationResult, success: bool
) -> str:
    """Format a leaf condition evaluation result

    Args:
        evaluation_result: The leaf evaluation result to format
        success: Whether the conditions were successful

    Returns:
        A string describing the evaluation result
    """
    condition_desc = _format_leaf_condition(evaluation_result)

    if success:
        return f"Condition '{condition_desc}' was met"

    return f"Condition '{condition_desc}' was not met"

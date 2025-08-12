from typing import Any


MAX_DEPTH = 100


def format_evaluation_success_message(evaluation_result: Any) -> str:
    """Format a detailed message about which conditions succeeded"""
    if not evaluation_result:
        return "No conditional dependencies to evaluate."

    return _format_evaluation_message(evaluation_result, success=True, depth=0)


def format_evaluation_failure_message(evaluation_result: Any) -> str:
    """Format a detailed message about which conditions failed"""
    if not evaluation_result:
        return "No conditional dependencies to evaluate."

    return _format_evaluation_message(evaluation_result, success=False, depth=0)


def _format_leaf_condition(evaluation_result: Any) -> str:
    """Format a single leaf condition into a readable string"""
    condition_desc = f"{evaluation_result.field_address} {evaluation_result.operator}"
    if evaluation_result.expected_value is not None:
        condition_desc += f" {evaluation_result.expected_value}"
    return condition_desc


def _format_condition_list(results: list, success: bool, depth: int) -> list[str]:
    """Format a list of conditions (either leaf or group) into readable strings"""
    condition_descriptions = []
    for sub_result in results:
        if _is_leaf_condition(sub_result):
            condition_descriptions.append(_format_leaf_condition(sub_result))
        elif _is_group_condition(sub_result):
            # Recursively format nested groups with depth tracking
            condition_descriptions.append(
                _format_evaluation_message(sub_result, success, depth + 1)
            )
    return condition_descriptions


def _format_evaluation_message(
    evaluation_result: Any, success: bool, depth: int = 0
) -> str:
    """Format evaluation results into a readable message"""
    # Prevent infinite recursion
    if depth > MAX_DEPTH:
        return "Condition evaluation too deeply nested"

    # Try to format as group condition first
    if _is_group_condition(evaluation_result):
        return _format_group_condition(evaluation_result, success, depth)

    # Try to format as leaf condition
    if _is_leaf_condition(evaluation_result):
        return _format_leaf_condition_message(evaluation_result, success)

    # Unknown condition type
    return "Evaluation result details unavailable"


def _is_group_condition(evaluation_result: Any) -> bool:
    """Check if evaluation_result is a group condition"""
    return (
        hasattr(evaluation_result, "logical_operator")
        and hasattr(evaluation_result, "condition_results")
        and evaluation_result.logical_operator is not None
        and isinstance(evaluation_result.logical_operator, str)
    )


def _is_leaf_condition(evaluation_result: Any) -> bool:
    """Check if evaluation_result is a leaf condition"""
    return (
        hasattr(evaluation_result, "field_address")
        and hasattr(evaluation_result, "operator")
        and evaluation_result.field_address is not None
        and isinstance(evaluation_result.field_address, str)
        and evaluation_result.operator is not None
        and isinstance(evaluation_result.operator, str)
    )


def _format_group_condition(evaluation_result: Any, success: bool, depth: int) -> str:
    """Format a group condition evaluation result"""
    logical_operator = evaluation_result.logical_operator
    results = evaluation_result.condition_results
    condition_descriptions = _format_condition_list(results, success, depth)

    if success:
        return f"All conditions in {logical_operator.upper()} group were met: {'; '.join(condition_descriptions)}"

    if condition_descriptions:
        return f"Failed conditions in {logical_operator.upper()} group: {'; '.join(condition_descriptions)}"

    return f"Group condition with {logical_operator.upper()} operator failed"


def _format_leaf_condition_message(evaluation_result: Any, success: bool) -> str:
    """Format a leaf condition evaluation result"""
    condition_desc = _format_leaf_condition(evaluation_result)

    if success:
        return f"Condition '{condition_desc}' was met"

    return f"Condition '{condition_desc}' was not met"

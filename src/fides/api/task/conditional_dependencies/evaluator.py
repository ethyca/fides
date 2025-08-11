from typing import Any, Union

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.graph.config import FieldPath
from fides.api.task.conditional_dependencies.operators import operator_methods
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionEvaluationResult,
    ConditionGroup,
    ConditionLeaf,
    EvaluationResult,
    GroupEvaluationResult,
    GroupOperator,
    Operator,
)


class ConditionEvaluationError(Exception):
    """Error raised when a condition evaluation fails"""


class ConditionEvaluator:
    """Evaluates nested conditions for manual task creation"""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_rule(
        self, rule: Condition, data: Union[dict, Any]
    ) -> tuple[bool, EvaluationResult]:
        """Evaluate a nested condition rule against input data and return detailed results"""
        if isinstance(rule, ConditionLeaf):
            leaf_result = self._evaluate_leaf_condition(rule, data)
            return leaf_result.result, leaf_result
        # ConditionGroup
        group_result = self._evaluate_group_condition(rule, data)
        return group_result.result, group_result

    def _evaluate_leaf_condition(
        self, condition: ConditionLeaf, data: Union[dict, Any]
    ) -> ConditionEvaluationResult:
        """Evaluate a leaf condition against input data"""
        # Handle both colon-separated and dot-separated field addresses
        if ":" in condition.field_address:
            # Full field address like "dataset:collection:field" - split on colons
            keys = condition.field_address.split(":")
        else:
            # Relative field path like "field.subfield" - split on dots
            keys = condition.field_address.split(".")

        data_value = self._get_nested_value(data, keys)

        # Apply operator and get result
        try:
            result = self._apply_operator(
                data_value, condition.operator, condition.value
            )
            message = f"Condition '{condition.field_address} {condition.operator} {condition.value}' evaluated to {result}"
        except Exception as e:
            result = False
            message = f"Error evaluating condition '{condition.field_address} {condition.operator} {condition.value}': {str(e)}"

        return ConditionEvaluationResult(
            field_address=condition.field_address,
            operator=condition.operator,
            expected_value=condition.value,
            actual_value=data_value,
            result=result,
            message=message,
        )

    def _evaluate_group_condition(
        self, group: ConditionGroup, data: Union[dict, Any]
    ) -> GroupEvaluationResult:
        """Evaluate a group condition against input data"""
        results = [
            self.evaluate_rule(condition, data)[1] for condition in group.conditions
        ]

        logical_operators = {GroupOperator.and_: all, GroupOperator.or_: any}
        operator_func = logical_operators.get(group.logical_operator)

        if operator_func is None:
            logger.warning(f"Unknown logical operator: {group.logical_operator}")
            result = False
        else:
            result = operator_func([r.result for r in results])

        return GroupEvaluationResult(
            logical_operator=group.logical_operator,
            condition_results=results,
            result=result,
        )

    def _get_nested_value(self, data: Union[dict, Any], keys: list[str]) -> Any:
        """Get nested value from data using dot notation or colon notation

        Supports both simple dictionary access and Fides reference structures:
        - Simple dict: data["user"]["name"]
        - Fides FieldAddress: data.get_field_value(FieldAddress("dataset", "collection", "field_address"))
        - Fides Collection: data.get_field_value(FieldPath("field_address", "subfield"))

        Also supports full field addresses with dataset:collection:field format
        """
        if not keys:
            return data

        current = data

        # Try Fides reference structures first
        if hasattr(current, "get_field_value"):
            try:
                field_path = FieldPath(*keys) if len(keys) > 1 else FieldPath(keys[0])
                return current.get_field_value(field_path)
            except (AttributeError, ValueError):
                pass

        # Fall back to dictionary access for all path types
        for key in keys:
            if not isinstance(current, dict):
                current = current.get(key, {}) if hasattr(current, "get") else None
            else:
                current = current.get(key, {})

        return current if current != {} else None

    def _apply_operator(
        self, data_value: Any, operator: Operator, user_input_value: Any
    ) -> bool:
        """Apply operator to actual and expected values"""

        # Get the method for the operator and execute it
        operator_method = operator_methods.get(operator)
        if operator_method is None:
            logger.warning(f"Unknown operator: {operator}")
            raise ConditionEvaluationError(f"Unknown operator: {operator}")
        try:
            return operator_method(data_value, user_input_value)
        except (TypeError, ValueError) as e:
            raise ConditionEvaluationError(f"Error evaluating condition: {e}") from e

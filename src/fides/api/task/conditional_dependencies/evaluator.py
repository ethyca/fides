from typing import Any, Union

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.graph.config import FieldPath
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


class ConditionEvaluator:
    """Evaluates nested conditions for manual task creation"""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_rule(self, rule: Condition, data: Union[dict, Any]) -> bool:
        """Evaluate a nested condition rule against input data"""
        if isinstance(rule, ConditionLeaf):
            return self._evaluate_leaf_condition(rule, data)
        # ConditionGroup
        return self._evaluate_group_condition(rule, data)

    def _evaluate_leaf_condition(
        self, condition: ConditionLeaf, data: Union[dict, Any]
    ) -> bool:
        """Evaluate a leaf condition against input data"""
        actual_value = self._get_nested_value(data, condition.field.split("."))
        # Apply operator and return result
        return self._apply_operator(actual_value, condition.operator, condition.value)

    def _evaluate_group_condition(
        self, group: ConditionGroup, data: Union[dict, Any]
    ) -> bool:
        """Evaluate a group condition against input data"""
        results = [
            self.evaluate_rule(condition, data) for condition in group.conditions
        ]

        logical_operators = {GroupOperator.and_: all, GroupOperator.or_: any}
        operator_func = logical_operators.get(group.op)

        if operator_func is None:
            logger.warning(f"Unknown logical operator: {group.op}")
            return False

        return operator_func(results)

    def _get_nested_value(self, data: Union[dict, Any], keys: list[str]) -> Any:
        """Get nested value from data using dot notation

        Supports both simple dictionary access and Fides reference structures:
        - Simple dict: data["user"]["name"]
        - Fides FieldAddress: data.get_field_value(FieldAddress("dataset", "collection", "field"))
        - Fides Collection: data.get_field_value(FieldPath("field", "subfield"))
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

        # Fall back to dictionary access
        for key in keys:
            if not isinstance(current, dict):
                current = current.get(key, {}) if hasattr(current, "get") else None
            else:
                current = current.get(key, {})

        return current if current != {} else None

    def _apply_operator(
        self, actual_value: Any, operator: Operator, expected_value: Any
    ) -> bool:
        """Apply operator to actual and expected values"""

        # Map operators to their evaluation methods
        operator_methods = {
            Operator.exists: self._operator_exists,
            Operator.not_exists: self._operator_not_exists,
            Operator.eq: self._operator_eq,
            Operator.neq: self._operator_neq,
            Operator.lt: self._operator_lt,
            Operator.lte: self._operator_lte,
            Operator.gt: self._operator_gt,
            Operator.gte: self._operator_gte,
            Operator.list_contains: self._operator_list_contains,
            Operator.not_in_list: self._operator_not_in_list,
        }

        # Get the method for the operator and execute it
        operator_method = operator_methods.get(operator)
        if operator_method is None:
            logger.warning(f"Unknown operator: {operator}")
            return False

        return operator_method(actual_value, expected_value)

    def _operator_exists(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if value exists (is not None)"""
        return actual_value is not None

    def _operator_not_exists(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if value does not exist (is None)"""
        return actual_value is None

    def _operator_eq(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if values are equal"""
        return actual_value == expected_value

    def _operator_neq(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if values are not equal"""
        return actual_value != expected_value

    def _operator_lt(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if actual value is less than expected value"""
        return actual_value < expected_value if actual_value is not None else False

    def _operator_lte(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if actual value is less than or equal to expected value"""
        return actual_value <= expected_value if actual_value is not None else False

    def _operator_gt(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if actual value is greater than expected value"""
        return actual_value > expected_value if actual_value is not None else False

    def _operator_gte(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if actual value is greater than or equal to expected value"""
        return actual_value >= expected_value if actual_value is not None else False

    def _operator_list_contains(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if expected value is in the actual list"""
        return (
            expected_value in actual_value if isinstance(actual_value, list) else False
        )

    def _operator_not_in_list(self, actual_value: Any, expected_value: Any) -> bool:
        """Check if actual value is not in the expected list"""
        return (
            actual_value not in expected_value
            if isinstance(expected_value, list)
            else True
        )

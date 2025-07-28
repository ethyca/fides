import operator as py_operator
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

operator_methods = {
    Operator.exists: lambda a, _: a is not None,
    Operator.not_exists: lambda a, _: a is None,
    Operator.eq: py_operator.eq,
    Operator.neq: py_operator.ne,
    Operator.lt: lambda a, b: a < b if a is not None else False,
    Operator.lte: lambda a, b: a <= b if a is not None else False,
    Operator.gt: lambda a, b: a > b if a is not None else False,
    Operator.gte: lambda a, b: a >= b if a is not None else False,
    Operator.list_contains: lambda a, b: b in a if isinstance(a, list) else False,
    Operator.not_in_list: lambda a, b: a not in b if isinstance(b, list) else True,
}


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
        actual_value = self._get_nested_value(data, condition.field_address.split("."))
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
        operator_func = logical_operators.get(group.logical_operator)

        if operator_func is None:
            logger.warning(f"Unknown logical operator: {group.logical_operator}")
            return False

        return operator_func(results)

    def _get_nested_value(self, data: Union[dict, Any], keys: list[str]) -> Any:
        """Get nested value from data using dot notation

        Supports both simple dictionary access and Fides reference structures:
        - Simple dict: data["user"]["name"]
        - Fides FieldAddress: data.get_field_value(FieldAddress("dataset", "collection", "field_address"))
        - Fides Collection: data.get_field_value(FieldPath("field_address", "subfield"))
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

        # Get the method for the operator and execute it
        operator_method = operator_methods.get(operator)
        if operator_method is None:
            logger.warning(f"Unknown operator: {operator}")
            return False

        return operator_method(actual_value, expected_value)

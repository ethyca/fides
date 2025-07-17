from typing import Any, Union

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.graph.config import CollectionAddress, FieldAddress, FieldPath
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
        else:  # ConditionGroup
            return self._evaluate_group_condition(rule, data)

    def _evaluate_leaf_condition(
        self, condition: ConditionLeaf, data: Union[dict, Any]
    ) -> bool:
        """Evaluate a leaf condition against input data"""
        # Get the actual value from the data
        actual_value = self._get_nested_value(data, condition.field.split("."))
        # Apply operator and return result
        return self._apply_operator(actual_value, condition.operator, condition.value)

    def _evaluate_group_condition(
        self, group: ConditionGroup, data: Union[dict, Any]
    ) -> bool:
        """Evaluate a group condition against input data"""
        results = [self.evaluate_rule(cond, data) for cond in group.conditions]
        # Apply logical operator
        if group.op == GroupOperator.and_:
            return all(results)
        else:  # GroupOperator.or_
            return any(results)

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
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, {})
            elif hasattr(current, "get_field_value"):
                # Handle Fides reference structures
                try:
                    # Try to access as a field path
                    field_path = FieldPath(*keys)
                    current = current.get_field_value(field_path)
                    break  # We've processed all keys as a single field path
                except (AttributeError, ValueError):
                    # Fall back to dictionary access
                    current = current.get(key, {}) if hasattr(current, "get") else None
            else:
                return None
        return current if current != {} else None

    def _apply_operator(
        self, actual_value: Any, operator: Operator, expected_value: Any
    ) -> bool:
        """Apply operator to actual and expected values"""
        if operator == Operator.exists:
            return actual_value is not None
        elif operator == Operator.not_exists:
            return actual_value is None
        elif operator == Operator.eq:
            return actual_value == expected_value
        elif operator == Operator.neq:
            return actual_value != expected_value
        elif operator == Operator.lt:
            return actual_value < expected_value if actual_value is not None else False
        elif operator == Operator.lte:
            return actual_value <= expected_value if actual_value is not None else False
        elif operator == Operator.gt:
            return actual_value > expected_value if actual_value is not None else False
        elif operator == Operator.gte:
            return actual_value >= expected_value if actual_value is not None else False
        elif operator == Operator.list_contains:
            return (
                expected_value in actual_value
                if isinstance(actual_value, list)
                else False
            )
        elif operator == Operator.not_in_list:
            return (
                actual_value not in expected_value
                if isinstance(expected_value, list)
                else True
            )
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

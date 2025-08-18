from typing import Any, Optional, Union

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.graph.config import FieldPath
from fides.api.task.conditional_dependencies.operators import (
    LOGICAL_OPERATORS,
    OPERATOR_METHODS,
)
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionEvaluationResult,
    ConditionGroup,
    ConditionLeaf,
    EvaluationResult,
    GroupEvaluationResult,
    Operator,
)


class ConditionEvaluationError(Exception):
    """Error raised when a condition evaluation fails"""


class ConditionEvaluator:
    """Evaluates nested conditions and returns a boolean result and a detailed evaluation report"""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_rule(
        self, rule: Condition, data: Union[dict, Any]
    ) -> EvaluationResult:
        """Evaluate a nested condition rule against input data and return detailed results

        Args:
            rule: The condition rule to evaluate
            data: The data to evaluate the condition against

        Returns:
            evaluation report: A detailed report of the evaluation
            - The field address of the condition
            - The operator used in the condition
            - The expected value of the condition
            - The actual value of the condition
            - The result of the condition evaluation
            - A message describing the condition evaluation
        """
        if isinstance(rule, ConditionLeaf):
            leaf_result = self._evaluate_leaf_condition(rule, data)
            return leaf_result
        # ConditionGroup
        group_result = self._evaluate_group_condition(rule, data)
        return group_result

    def _evaluate_leaf_condition(
        self, condition: ConditionLeaf, data: Union[dict, Any]
    ) -> ConditionEvaluationResult:
        """Evaluate a leaf condition against input data

        Args:
            condition: The leaf condition to evaluate
            data: The data to evaluate the condition against

        Returns:
            A detailed evaluation report for the leaf condition

        Raises:
            ConditionEvaluationError: If there is an issue applying the operator or if an unexpected error occurs.
        """
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
        except ConditionEvaluationError as e:
            logger.error(
                f"Unexpected error evaluating condition '{condition.field_address} {condition.operator} {condition.value}': {str(e)}"
            )
            raise

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
        """Evaluate a group condition against input data

        Args:
            group: The group condition to evaluate
            data: The data to evaluate the condition against

        Returns:
            A detailed evaluation report for the group condition

        Raises:
            ConditionEvaluationError: If there is an issue evaluating the group condition (e.g., from evaluate_rule calls)
        """
        try:
            operator_func = LOGICAL_OPERATORS[group.logical_operator]
        except KeyError as e:
            raise ConditionEvaluationError(
                f"Unknown logical operator: {group.logical_operator}"
            ) from e

        results = [
            self.evaluate_rule(condition, data) for condition in group.conditions
        ]
        group_result = operator_func([r.result for r in results])

        return GroupEvaluationResult(
            logical_operator=group.logical_operator,
            condition_results=results,
            result=group_result,
        )

    def _get_nested_value_from_fides_reference_structure(
        self, data: Any, keys: list[str]
    ) -> Optional[Any]:
        """Get nested value from Fides reference structure

        Args:
            data: The Fides reference structure to get the nested value from
            keys: The keys to for the specific nested value in the data

        Returns:
            The nested value from the data or None if not a Fides reference structure

        Raises:
            AttributeError: If the data does not have a get_field_value method
            ValueError: If the keys are not valid for the Fides reference structure
        """
        if hasattr(data, "get_field_value"):
            try:
                field_path = FieldPath(*keys) if len(keys) > 1 else FieldPath(keys[0])
                return data.get_field_value(field_path)
            except (AttributeError, ValueError):
                logger.debug(
                    f"Fides reference structure does not have a get_field_value method: {data}"
                )
                raise
        raise ConditionEvaluationError(
            f"Data does not have a get_field_value method: {data}"
        )

    def _get_nested_value_from_dict(self, data: dict, keys: list[str]) -> Optional[Any]:
        """Get nested value from dictionary. This is the fallback and will return None if the key is not found.
        When the data is missing the None value will work with exists/not_exists operations and correctly evaluate to False
        for other operations like eq, not_eq, etc.

        Args:
            data: The dictionary to get the nested value from
            keys: The keys to for the specific nested value in the data

        Returns:
            The nested value from the data

        Raises:
            KeyError: If the keys are not valid for the dictionary
        """
        current: Any = data
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
            if current is None:
                return None
        return current

    def _get_nested_value(self, data: Union[dict, Any], keys: list[str]) -> Any:
        """Get nested value from data using dot notation or colon notation

        Supports both simple dictionary access and Fides reference structures:
        - Simple dict: data["user"]["name"]
        - Fides FieldAddress: data.get_field_value(FieldAddress("dataset", "collection", "field_address"))
        - Fides Collection: data.get_field_value(FieldPath("field_address", "subfield"))

        Also supports full field addresses with dataset:collection:field format

        Args:
            data: The data to get the nested value from
            keys: The keys to for the specific nested value in the data

        Returns:
            The nested value from the data

        Raises:
            KeyError: If the keys are not valid for the dictionary
        """
        if not keys:
            return data

        # Try Fides reference structures first
        try:
            return self._get_nested_value_from_fides_reference_structure(data, keys)
        except (AttributeError, ValueError, ConditionEvaluationError):
            pass

        # Fall back to dictionary access for all path types
        return self._get_nested_value_from_dict(data, keys)

    def _apply_operator(
        self, data_value: Any, operator: Operator, user_input_value: Any
    ) -> bool:
        """Apply operator to actual and expected values
        The operator is validated in the ConditionLeaf and ConditionGroup schemas,
        so we don't need to validate it here.

        Args:
            data_value: The actual value to evaluate
            operator: The operator to apply
            user_input_value: The expected value to evaluate against

        Returns:
            The result of the operator applied to the actual and expected values
        """
        # Get the method for the operator and execute it
        try:
            operator_method = OPERATOR_METHODS[operator]
            return operator_method(data_value, user_input_value)
        except KeyError as e:
            # Unknown operator
            logger.error(f"Unknown operator: {operator}")
            raise ConditionEvaluationError(f"Unknown operator: {operator}") from e
        except Exception as e:
            # Log unexpected errors but still raise them
            logger.error(f"Unexpected error in operator {operator}: {e}")
            raise ConditionEvaluationError(
                f"Unexpected error evaluating condition: {e}"
            ) from e

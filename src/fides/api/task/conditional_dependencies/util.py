from datetime import datetime
from typing import Any, Union
from uuid import UUID

from pydantic import BaseModel

from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
)


# pylint: disable=too-many-return-statements
def transform_value_for_evaluation(value: Any) -> Any:
    """
    Transforms a value to its evaluation-ready form.

    Handles various data types defensively to ensure compatibility with
    the operators defined in task.conditional_dependencies.operators.py

    Args:
        value: The value to transform

    Returns:
        The transformed value compatible with evaluation operators
    """
    if value is None:
        return None

    # Handle Pydantic models first (before checking for other attributes)
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    # Handle enums (must come before other checks as enums might have other attributes)
    if hasattr(value, "value") and not isinstance(value, BaseModel):
        return value.value

    # Handle date/time types
    if isinstance(value, datetime):
        return value.isoformat()

    # Handle UUIDs
    if isinstance(value, UUID):
        return str(value)

    # Handle bytes types - convert to strings for string operators
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            # If decode fails, use repr for a string representation
            return repr(value)

    # Handle complex numbers - convert to string as they can't be compared with < > etc
    if isinstance(value, complex):
        return str(value)

    # Handle set/frozenset/tuple - convert to lists for list operators
    # (operators.py list operations check isinstance(x, list))
    if isinstance(value, (set, frozenset, tuple)):
        return list(value)

    # Return value as-is if no transformation needed
    return value


def extract_nested_field_value(data: Any, field_path: list[str]) -> Any:
    """
    Extracts a value from a dictionary by following the path.

    Args:
        data: The dictionary to extract from
        field_path: The path to extract the value from

    Returns:
        The extracted value
    """
    current: Any = data
    for part in field_path:
        if current is None:
            return None
        if hasattr(current, part):
            current = getattr(current, part)
        elif isinstance(current, list) and part.isdigit():
            if 0 <= int(part) < len(current):
                current = current[int(part)]
            else:
                return None
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            # If we can't find the part, return None
            return None
    return current


def set_nested_value(path: list[str], value: Any) -> dict[str, Any]:
    """
    Returns a dictionary with a nested value set at the path.

    Args:
        path: List of keys to traverse (e.g., ["policy", "key"])
        value: The value to set at the end of the path
    """
    result: dict[str, Any] = {}
    final_key = path[-1]
    current = result

    for key in path[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the final value
    current[final_key] = value
    return result


def extract_field_addresses(condition: Union[ConditionLeaf, ConditionGroup]) -> set[str]:
    """
    Recursively extracts all field addresses from a condition tree.

    Args:
        condition: The condition tree (leaf or group) to extract field addresses from

    Returns:
        Set of unique field addresses referenced in the condition tree

    Example:
        >>> leaf = ConditionLeaf(field_address="user.age", operator=Operator.gte, value=18)
        >>> extract_field_addresses(leaf)
        {'user.age'}

        >>> group = ConditionGroup(
        ...     logical_operator=GroupOperator.and_,
        ...     conditions=[
        ...         ConditionLeaf(field_address="user.age", operator=Operator.gte, value=18),
        ...         ConditionLeaf(field_address="user.verified", operator=Operator.eq, value=True)
        ...     ]
        ... )
        >>> extract_field_addresses(group)
        {'user.age', 'user.verified'}
    """
    field_addresses: set[str] = set()

    if isinstance(condition, ConditionLeaf):
        # Leaf condition - add its field address
        field_addresses.add(condition.field_address)
    elif isinstance(condition, ConditionGroup):
        # Group condition - recursively process all sub-conditions
        for sub_condition in condition.conditions:
            field_addresses.update(extract_field_addresses(sub_condition))

    return field_addresses

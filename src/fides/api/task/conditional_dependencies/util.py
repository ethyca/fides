from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


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

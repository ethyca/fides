from typing import Any, Optional

from fides.api.task.conditional_dependencies.schemas import (
    ConditionalDependencyFieldInfo,
)


def create_conditional_dependency_field_info(
    field_path: str,
    field_type: str,
    description: Optional[str] = None,
    is_convenience_field: bool = False,
) -> ConditionalDependencyFieldInfo:
    """Helper to create ConditionalDependencyFieldInfo objects."""
    return ConditionalDependencyFieldInfo(
        field_path=field_path,
        field_type=field_type,
        description=description,
        is_convenience_field=is_convenience_field,
    )


def merge_dicts_no_overwrite(
    result: dict[str, Any], privacy_request_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Merges two dictionaries, avoiding overwriting existing values.

    Args:
        result: The dictionary to merge into
        privacy_request_data: The dictionary to merge from

    Returns:
        The merged dictionary
    """
    for key, value in privacy_request_data.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            merge_dicts_no_overwrite(result[key], value)
        elif key not in result:
            result[key] = value
    return result


def extract_nested_field_value(data: dict[str, Any], field_path: list[str]) -> Any:
    """
    Extracts a value from a dictionary by following the path.

    Args:
        data: The dictionary to extract from
        path: The path to extract the value from

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

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


def extract_nested_field_value(data: Any, field_path: list[str]) -> Any:
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

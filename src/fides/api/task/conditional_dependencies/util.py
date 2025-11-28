from typing import Any


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

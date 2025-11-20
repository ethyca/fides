from typing import Any


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

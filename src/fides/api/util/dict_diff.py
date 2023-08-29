from typing import Any, Dict, Tuple


def dict_diff(
    first_dict: Dict[str, Any], second_dict: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    before = {}
    after = {}

    for key in set(first_dict) | set(second_dict):
        before_value, after_value = first_dict.get(key), second_dict.get(key)

        # Treat empty strings and None as equivalent
        if before_value in ["", None] and after_value in ["", None]:
            continue

        if isinstance(before_value, dict) and isinstance(after_value, dict):
            nested_before, nested_after = dict_diff(before_value, after_value)
            if nested_before:
                before[key] = nested_before
            if nested_after:
                after[key] = nested_after
        elif before_value != after_value:
            if key in first_dict and before_value is not None:
                before[key] = before_value
            if key in second_dict and after_value is not None:
                after[key] = after_value

    return before, after

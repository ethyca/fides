from typing import Any, Dict, Tuple


def dict_diff(
    dict1: Dict[str, Any], dict2: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    before = {}
    after = {}

    for key in set(dict1) | set(dict2):
        val1, val2 = dict1.get(key), dict2.get(key)

        if isinstance(val1, dict) and isinstance(val2, dict):
            nested_before, nested_after = dict_diff(val1, val2)
            if nested_before:
                before[key] = nested_before
            if nested_after:
                after[key] = nested_after
        elif val1 != val2:
            if key in dict1:
                before[key] = val1
            if key in dict2:
                after[key] = val2

    return before, after

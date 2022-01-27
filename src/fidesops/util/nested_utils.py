from collections import defaultdict
from typing import Dict, Any

from fidesops.common_exceptions import FidesopsException


def unflatten_dict(input_row: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    Takes a dictionary that has been normalized to level 1 and reconstitutes:

    {
       "a": 1,
       "b.c": 2,
       "b.d": 3
    }

    and turns it into:
    {"a": 1, "b": {"c": 2, "d": 3}
    """

    def _create_dict() -> defaultdict:
        """Can create a defaultdict at every level"""
        return defaultdict(_create_dict)

    unpacked_results = _create_dict()

    for key, value in input_row.items():
        if isinstance(value, dict):
            raise FidesopsException(
                "`unflatten_dict` expects a flattened dictionary as input."
            )

        levels = key.split(separator)
        subdict = unpacked_results
        for level in levels[:-1]:
            subdict = subdict[level]

        try:
            subdict[levels[-1]] = value
        except TypeError as exc:
            raise FidesopsException(
                f"Error unflattening dictionary, conflicting levels detected: {exc}"
            )

    return unpacked_results

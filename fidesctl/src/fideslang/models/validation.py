from typing import List

from pydantic import BaseModel


def sort_list_objects(values: List) -> List:
    """Sort objects in a list by their name. This makes object comparisons deterministic."""
    values.sort(key=lambda value: value.name)
    return values

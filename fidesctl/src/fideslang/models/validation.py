from typing import List, Optional, Dict

from pydantic import BaseModel, ValidationError

from fideslang.models.fides_model import FidesKey


def sort_list_objects(values: List) -> List:
    """Sort objects in a list by their name. This makes object comparisons deterministic."""
    values.sort(key=lambda value: value.name)
    return values


def no_self_reference(value, values: Dict, **kwargs) -> FidesKey:
    if value == values["fidesKey"]:
        raise SystemError
    return value

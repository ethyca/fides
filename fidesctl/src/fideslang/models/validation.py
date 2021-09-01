from typing import List, Dict

from fideslang.models.fides_model import FidesKey


class FidesValidationError(Exception):
    """Custom exception for when the pydantic ValidationError can't be used."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def sort_list_objects(values: List) -> List:
    """Sort objects in a list by their name. This makes object comparisons deterministic."""
    values.sort(key=lambda value: value.name)
    return values


def no_self_reference(value: FidesKey, values: Dict) -> FidesKey:
    if value == values["fidesKey"]:
        raise FidesValidationError("FidesKey can not self-reference!")
    return value

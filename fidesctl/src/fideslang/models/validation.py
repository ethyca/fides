import re
from typing import List, Dict, Pattern

from pydantic import ConstrainedStr


class FidesValidationError(Exception):
    """Custom exception for when the pydantic ValidationError can't be used."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class FidesKey(ConstrainedStr):
    """
    A FidesKey should only contain alphanumeric characters or '_'
    """

    regex: Pattern[str] = re.compile(r"^[a-zA-Z_]+$")

    @classmethod  # This overrides the default method to throw the custom FidesValidationError
    def validate(cls, value: str) -> str:
        if not cls.regex.match(value):
            raise FidesValidationError(
                "FidesKey must only contain alphanumeric characters or '_'."
            )

        return value


def sort_list_objects(values: List) -> List:
    """Sort objects in a list by their name. This makes object comparisons deterministic."""
    values.sort(key=lambda value: value.name)
    return values


def no_self_reference(value: FidesKey, values: Dict) -> FidesKey:
    if value == values["fidesKey"]:
        raise FidesValidationError("FidesKey can not self-reference!")
    return value

"""
Contains all of the additional validation for the resource models.
"""

import re
from typing import List, Dict, Pattern

from pydantic import ConstrainedStr


class FidesValidationError(Exception):
    """Custom exception for when the pydantic ValidationError can't be used."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()


class FidesKey(ConstrainedStr):
    """
    A FidesKey should only contain alphanumeric characters or '_'
    """

    regex: Pattern[str] = re.compile(r"^[a-zA-Z0-9_]+$")

    @classmethod  # This overrides the default method to throw the custom FidesValidationError
    def validate(cls, value: str) -> str:
        if not cls.regex.match(value):
            raise FidesValidationError(
                "FidesKey must only contain alphanumeric characters or '_'."
            )

        return value


def sort_list_objects_by_name(values: List) -> List:
    """
    Sort objects in a list by their name.
    This makes resource comparisons deterministic.
    """
    values.sort(key=lambda value: value.name)
    return values


def sort_list_objects_by_key(values: List) -> List:
    """
    Sort objects in a list by their fides_key.
    This makes resource comparisons deterministic.
    """
    values.sort(key=lambda value: value.fides_key)
    return values


def no_self_reference(value: FidesKey, values: Dict) -> FidesKey:
    """
    Check to make sure that the fides_key doesn't match other fides_key
    references within an object.

    i.e. DataCategory.parent_key != DataCategory.fides_key
    """

    if value == values["fides_key"]:
        raise FidesValidationError("FidesKey can not self-reference!")
    return value

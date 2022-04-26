"""
Contains all of the additional validation for the resource models.
"""

import re
from typing import Dict, List, Pattern

from pydantic import ConstrainedStr

from fideslang.default_fixtures import COUNTRY_CODES

VALID_COUNTRY_CODES = [country["alpha3Code"] for country in COUNTRY_CODES]


class FidesValidationError(Exception):
    """Custom exception for when the pydantic ValidationError can't be used."""


class FidesKey(ConstrainedStr):
    """
    A FidesKey type that creates a custom constrained string.
    """

    regex: Pattern[str] = re.compile(r"^[a-zA-Z0-9_.-]+$")

    @classmethod  # This overrides the default method to throw the custom FidesValidationError
    def validate(cls, value: str) -> str:
        if not cls.regex.match(value):
            raise FidesValidationError(
                "FidesKey must only contain alphanumeric characters, '.', '_' or '-'."
            )

        return value


def sort_list_objects_by_name(values: List) -> List:
    """
    Sort objects in a list by their name.
    This makes resource comparisons deterministic.
    """
    values.sort(key=lambda value: value.name)
    return values


def no_self_reference(value: FidesKey, values: Dict) -> FidesKey:
    """
    Check to make sure that the fides_key doesn't match other fides_key
    references within an object.

    i.e. DataCategory.parent_key != DataCategory.fides_key
    """

    fides_key = FidesKey.validate(values.get("fides_key", ""))
    if value == fides_key:
        raise FidesValidationError("FidesKey can not self-reference!")
    return value


def matching_parent_key(value: FidesKey, values: Dict) -> FidesKey:
    """
    Confirm that the parent_key matches the parent parsed from the FidesKey.
    """

    fides_key = FidesKey.validate(values.get("fides_key", ""))
    split_fides_key = fides_key.split(".")

    # Check if it is a top-level resource
    if len(split_fides_key) == 1 and not value:
        return value

    # Reform the parent_key from the fides_key and compare
    parent_key_from_fides_key = ".".join(split_fides_key[:-1])
    if parent_key_from_fides_key != value:
        raise FidesValidationError(
            "The parent_key ({0}) does not match the parent parsed ({1}) from the fides_key ({2})!".format(
                value, parent_key_from_fides_key, fides_key
            )
        )
    return value


def check_valid_country_code(country_code_list: List) -> List:
    """
    Validate all listed countries (if present) are valid country codes.
    """
    if country_code_list is not None:
        for country_code in country_code_list:
            if country_code not in VALID_COUNTRY_CODES:
                raise FidesValidationError(
                    "The country identified as {} is not a valid Alpha-3 code per ISO 3166.".format(
                        country_code
                    )
                )
    return country_code_list

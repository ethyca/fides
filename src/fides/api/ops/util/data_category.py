from enum import Enum as EnumType
from typing import Type

from fideslang import DEFAULT_TAXONOMY

from fides.api.ops import common_exceptions


def generate_fides_data_categories() -> Type[EnumType]:
    """Programmatically generated the DataCategory enum based on the imported Fides data."""
    FidesDataCategory = EnumType(  # type: ignore
        "FidesDataCategory",
        {cat.fides_key: cat.fides_key for cat in DEFAULT_TAXONOMY.data_category},
    )
    return FidesDataCategory


DataCategory = generate_fides_data_categories()


def _validate_data_category(data_category: str) -> str:
    """Checks that the data category passed in is currently supported."""
    valid_categories = DataCategory.__members__.keys()
    if data_category not in valid_categories:
        raise common_exceptions.DataCategoryNotSupported(
            f"The data category {data_category} is not supported."
        )
    return data_category

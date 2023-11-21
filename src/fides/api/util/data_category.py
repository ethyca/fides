from enum import Enum as EnumType
from typing import List, Type

from fideslang.default_taxonomy import DEFAULT_TAXONOMY
from fideslang.models import DataCategory as FideslangDataCategory
from fideslang.validation import FidesKey
from sqlalchemy.orm import Session

from fides.api import common_exceptions

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    DataCategory as DataCategoryDbModel,
)


def generate_fides_data_categories() -> Type[EnumType]:
    """Programmatically generated the DataCategory enum based on the imported Fides data."""
    data_categories: List[FideslangDataCategory] = DEFAULT_TAXONOMY.data_category
    FidesDataCategory = EnumType(
        "FidesDataCategory",
        {
            cat.fides_key: cat.fides_key
            for cat in data_categories  # pylint: disable=not-an-iterable
        },
    )
    return FidesDataCategory


DataCategory = generate_fides_data_categories()


def get_data_categories_from_db(db: Session) -> List[FidesKey]:
    """Query for existing data categories in the db using a synchronous session"""
    return [cat[0] for cat in db.query(DataCategoryDbModel.fides_key).all()]


def _validate_data_category(
    db: Session,
    data_category: str,
) -> str:
    """Checks that the data category passed in is currently supported."""
    valid_categories = get_data_categories_from_db(db=db)
    if data_category not in valid_categories:
        raise common_exceptions.DataCategoryNotSupported(
            f"The data category '{data_category}' was not found in the database, and is therefore not valid for use here."
        )
    return data_category

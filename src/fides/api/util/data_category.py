from enum import Enum as EnumType
from typing import Dict, List, Set, Type

from fideslang.default_taxonomy import DEFAULT_TAXONOMY
from fideslang.validation import FidesKey
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from fides.api import common_exceptions

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    DataCategory as DataCategoryDbModel,
    Dataset,
)


def generate_fides_data_categories() -> Type[EnumType]:
    """Programmatically generated the DataCategory enum based on the imported Fides data."""
    FidesDataCategory = EnumType(  # type: ignore
        "FidesDataCategory",
        {
            cat.fides_key: cat.fides_key
            for cat in DEFAULT_TAXONOMY.data_category  # pylint:disable=not-an-iterable
        },  # pylint:disable=not-an-iterable
    )
    return FidesDataCategory


# TODO: Move away from using this, it conflicts with the DataCategory model
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


def get_user_data_categories() -> List[str]:
    # organizations need to be extra careful about how these are used -
    # especially for erasure! Therefore, a safe default for "out of the
    # box" behaviour is to exclude these
    excluded_data_categories = [
        "user.financial",
        "user.payment",
        "user.authorization",
    ]
    all_data_categories = [
        str(category.fides_key)
        for category in DEFAULT_TAXONOMY.data_category  # pylint:disable=not-an-iterable
    ]
    return filter_data_categories(all_data_categories, excluded_data_categories)


def filter_data_categories(
    categories: List[str], excluded_categories: List[str]
) -> List[str]:
    """
    Filter data categories and their children out of a list of categories.

    We only want user-related data categories, but not the parent category
    We also only want 2nd level categories, otherwise there are policy conflicts
    """
    user_categories = [
        category
        for category in categories
        if category.startswith("user.") and len(category.split(".")) < 3
    ]
    if excluded_categories:
        duplicated_categories = [
            category
            for excluded_category in excluded_categories
            for category in user_categories
            if not category.startswith(excluded_category)
        ]
        default_categories = {
            category
            for category in duplicated_categories
            if duplicated_categories.count(category) == len(excluded_categories)
        }
        return sorted(list(default_categories))
    return sorted(user_categories)


def get_data_categories_map(db: Session) -> Dict[str, Set[str]]:
    """
    Returns a map of all datasets, where the keys are the fides keys
    of each dataset and the value is a set of data categories associated with each dataset
    """

    subquery = (
        select(
            Dataset.fides_key,
            func.jsonb_array_elements_text(
                text(
                    "jsonb_path_query(collections::jsonb, '$.** ? (@.data_categories != null).data_categories')"
                )
            ).label("category"),
        ).select_from(Dataset)
    ).cte()

    query = (
        select(
            [subquery.c.fides_key, func.array_agg(func.distinct(subquery.c.category))]
        )
        .select_from(subquery)
        .group_by(subquery.c.fides_key)
    )
    result = db.execute(query)
    return {key: set(value) if value else set() for key, value in result.all()}

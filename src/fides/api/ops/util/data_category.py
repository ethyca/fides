from enum import Enum as EnumType
from typing import List, Set, Type, Union

from fideslang import DEFAULT_TAXONOMY
from fideslang.models import DataCategory as FideslangDataCategory
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import DataCategory as DataCategoryDbModel
from fides.api.ops import common_exceptions
from fides.core.config import get_config
from fides.lib.db.session import get_db_session


def get_fides_data_categories_from_db() -> List[FideslangDataCategory]:
    """
    Returns each DataCategory from the database as it would have been defined in the
    default taxonomy.
    """
    db: Session = get_db_session(get_config())()
    return [cat.to_fideslang_obj() for cat in DataCategoryDbModel.all(db)]


def get_fides_data_categories_from_taxonomy() -> List[FideslangDataCategory]:
    """Returns the list of DataCategories from the default Fides taxonomy."""
    return DEFAULT_TAXONOMY.data_category


def get_fides_data_category_superset() -> List[FideslangDataCategory]:
    """Returns the union of DataCategories from the database and the default Fides taxonomy."""
    # TODO: De-duplicate this list
    return (
        get_fides_data_categories_from_db() + get_fides_data_categories_from_taxonomy()
    )


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
    from_db = [cat.fides_key for cat in get_fides_data_categories_from_db()]
    from_taxonomy = [cat.fides_key for cat in get_fides_data_categories_from_taxonomy()]
    if all(
        [
            data_category not in from_db,
            data_category not in from_taxonomy,
        ]
    ):
        raise common_exceptions.DataCategoryNotSupported(
            f"The data category {data_category} is not supported."
        )
    return data_category

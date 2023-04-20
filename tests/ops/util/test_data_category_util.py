from fideslang import DEFAULT_TAXONOMY
import pytest

from fides.api.ops import common_exceptions
from fides.api.ops.util.data_category import (
    _validate_data_category,
    get_fides_data_category_superset,
    get_fides_data_categories_from_db,
    get_fides_data_categories_from_taxonomy,
)


def test_get_fides_data_categories_from_taxonomy():
    assert len(get_fides_data_categories_from_taxonomy()) == len(
        DEFAULT_TAXONOMY.data_category
    )
    for el in DEFAULT_TAXONOMY.data_category:
        assert el in get_fides_data_categories_from_taxonomy()


def test_get_fides_data_categories_from_db(custom_data_category):
    from_db = get_fides_data_categories_from_db()
    assert custom_data_category.to_fideslang_obj() in from_db


def test_get_fides_data_category_superset(custom_data_category):
    superset = get_fides_data_category_superset()
    assert custom_data_category.to_fideslang_obj() in superset

    for el in DEFAULT_TAXONOMY.data_category:
        assert el in superset


def test_validate_data_category_rejects_unknown_categories(db):
    unknown_data_category = "unknown.test.category"
    with pytest.raises(common_exceptions.DataCategoryNotSupported):
        _validate_data_category(unknown_data_category)


def test_validate_data_category_allows_custom_categories(db, custom_data_category):
    assert (
        _validate_data_category(custom_data_category.fides_key)
        == custom_data_category.fides_key
    )

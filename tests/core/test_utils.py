# pylint: disable=missing-docstring, redefined-outer-name
from typing import Generator

import pytest
from fideslang.models import DatasetCollection, DatasetField

from fidesctl.core import utils
from fidesctl.core.config import get_config


@pytest.fixture()
def test_nested_collection_fields() -> Generator:
    nested_collection_fields = DatasetCollection(
        name="test_collection",
        fields=[
            DatasetField(
                name="top_level_field_1",
            ),
            DatasetField(
                name="top_level_field_2",
                fields=[
                    DatasetField(
                        name="first_nested_level",
                        fields=[
                            DatasetField(
                                name="second_nested_level",
                                fields=[DatasetField(name="third_nested_level")],
                            )
                        ],
                    )
                ],
            ),
        ],
    )

    yield nested_collection_fields


@pytest.mark.unit
def test_get_db_engine() -> None:
    conn_str = get_config().api.sync_database_url
    engine = utils.get_db_engine(conn_str)
    assert str(engine.url) == conn_str


@pytest.mark.unit
def test_nested_fields_unpacked(
    test_nested_collection_fields: DatasetCollection,
) -> None:
    """
    Tests unpacking fields from a data collection results in the
    correct number of fields being returned to be evaluated.
    """
    collection = test_nested_collection_fields
    collected_field_names = []
    for field in utils.get_all_level_fields(collection.fields):
        collected_field_names.append(field.name)
    assert len(collected_field_names) == 5


@pytest.mark.unit
@pytest.mark.parametrize(
    "fides_key, sanitized_fides_key",
    [("foo", "foo"), ("@foo#", "_foo_"), (":_foo)bar!123$", "__foo_bar_123_")],
)
def test_sanitize_fides_key(fides_key: str, sanitized_fides_key: str) -> None:
    assert sanitized_fides_key == utils.sanitize_fides_key(fides_key)


@pytest.mark.unit
@pytest.mark.parametrize(
    "fides_key, sanitized_fides_key",
    [("foo", "foo"), ("@foo#", "_foo_"), (":_foo)bar!123$", "__foo_bar_123_")],
)
def test_check_fides_key(fides_key: str, sanitized_fides_key: str) -> None:
    assert sanitized_fides_key == utils.check_fides_key(fides_key)

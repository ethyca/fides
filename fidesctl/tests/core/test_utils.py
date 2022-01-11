import os

import pytest

from fidesctl.core import utils, config

from fideslang.models import DatasetCollection, DatasetField


@pytest.fixture()
def test_nested_collection_fields():
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
def test_get_db_engine():
    conn_str = config.get_config().api.database_url
    engine = utils.get_db_engine(conn_str)
    assert str(engine.url) == conn_str


@pytest.mark.unit
def test_nested_fields_unpacked(test_nested_collection_fields):
    """
    Tests unpacking fields from a data collection results in the
    correct number of fields being returned to be evaluated.
    """
    collection = test_nested_collection_fields
    collected_field_names = []
    for field in utils.get_all_level_fields(collection.fields):
        collected_field_names.append(field.name)
    assert len(collected_field_names) == 5

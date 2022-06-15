# pylint: disable=missing-docstring, redefined-outer-name
from pathlib import PosixPath
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
def test_get_manifest_list(tmp_path: PosixPath) -> None:
    """Test that the correct number of yml files are returned."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    test_files = ["foo.yml", "foo.yaml"]

    for file in test_files:
        test_file = test_dir / file
        print(test_file)
        test_file.write_text("content")

    manifest_list = utils.get_manifest_list(str(test_dir))
    assert len(manifest_list) == 2

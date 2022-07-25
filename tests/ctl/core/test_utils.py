# pylint: disable=missing-docstring, redefined-outer-name
import os
from pathlib import PosixPath
from typing import Generator

import pytest
from fideslang.models import DatasetCollection, DatasetField

from fidesctl.ctl.core import utils
from fidesctl.ctl.core.config import get_config


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
    conn_str = get_config().database.sync_database_uri
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


@pytest.mark.unit
class TestGitIsDirty:
    """
    These tests can't use the standard pytest tmpdir
    because the files need to be within the git repo
    to be properly tested.

    They will therefore also break if the real dir
    used for testing is deleted.
    """

    def test_not_dirty(self) -> None:
        assert not utils.git_is_dirty("tests/ctl/data/example_sql/")

    def test_new_file_is_dirty(self) -> None:
        test_file = "tests/ctl/data/example_sql/new_file.txt"
        with open(test_file, "w") as file:
            file.write("test file")
        assert utils.git_is_dirty()
        os.remove(test_file)

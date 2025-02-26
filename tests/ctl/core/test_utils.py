# pylint: disable=missing-docstring, redefined-outer-name
import os
from pathlib import PosixPath
from typing import Generator

import pytest
import requests
from fideslang.models import DatasetCollection, DatasetField

from fides.common import utils as common_utils
from fides.config import get_config
from fides.core import utils as core_utils


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
def test_get_db_engine(test_config_path) -> None:
    conn_str = get_config(test_config_path).database.sync_database_uri
    engine = core_utils.get_db_engine(conn_str)
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
    for field in core_utils.get_all_level_fields(
        collection.model_dump(mode="json")["fields"]
    ):
        collected_field_names.append(field["name"])
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

    manifest_list = core_utils.get_manifest_list(str(test_dir))
    assert len(manifest_list) == 2


@pytest.mark.parametrize(
    "fides_key, sanitized_fides_key",
    [("foo", "foo"), ("@foo#", "_foo_"), (":_foo)bar!123$", "__foo_bar_123_")],
)
def test_sanitize_fides_key(fides_key: str, sanitized_fides_key: str) -> None:
    assert sanitized_fides_key == core_utils.sanitize_fides_key(fides_key)


@pytest.mark.unit
@pytest.mark.parametrize(
    "fides_key, sanitized_fides_key",
    [("foo", "foo"), ("@foo#", "_foo_"), (":_foo)bar!123$", "__foo_bar_123_")],
)
def test_check_fides_key(fides_key: str, sanitized_fides_key: str) -> None:
    assert sanitized_fides_key == core_utils.check_fides_key(fides_key)


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
        assert not core_utils.git_is_dirty("tests/ctl/data/example_sql/")

    def test_new_file_is_dirty(self) -> None:
        test_file = "tests/ctl/data/example_sql/new_file.txt"
        with open(test_file, "w") as file:
            file.write("test file")
        assert core_utils.git_is_dirty()
        os.remove(test_file)


@pytest.mark.unit
def test_repeatable_unique_key() -> None:
    expected_unique_fides_key = "test_dataset_87ccd73621"
    unique_fides_key = core_utils.generate_unique_fides_key(
        "test_dataset", "test_host", "test_name"
    )
    assert unique_fides_key == expected_unique_fides_key


@pytest.mark.integration
class TestCheckResponseAuth:
    def test_check_response_auth_sys_exit(self) -> None:
        """
        Verify that a SystemExit is raised when expected.

        Note that this must be an endpoint that requires
        authentication as it is looking for 401/403!
        """
        response = requests.get("/api/v1/cryptography/encryption/key")
        with pytest.raises(SystemExit):
            common_utils.check_response_auth(response)

    def test_check_response_auth_ok(self) -> None:
        """Verify that a response object is returned if no auth errors."""
        response = requests.get("/health")
        assert common_utils.check_response_auth(response)

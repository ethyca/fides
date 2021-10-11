import pytest
import yaml

from fideslang import manifests


# Helpers
@pytest.fixture()
def sample_manifest():
    yield manifests.load_yaml_into_dict("tests/data/sample_manifest.yml")


@pytest.fixture()
def ingestion_manifest_directory(
    populated_manifest_dir, populated_nested_manifest_dir, request
):
    """
    Allows for parameterization of manifests to ingest by returning
    the corresponding fixture
    """
    return {
        "populated_manifest_dir": populated_manifest_dir,
        "populated_nested_manifest_dir": populated_nested_manifest_dir,
    }[request.param]


# Unit
@pytest.mark.unit
def test_load_yaml_into_dict(sample_manifest):
    """
    Make sure that the yaml loaded from the sample manifest matches
    what is expected.
    """
    expected_result = {
        "id": 0,
        "name": "sample2",
        "version": "0.0.1",
        "description": "some description",
        "fields": [
            {"name": "myemail", "pii": "work_email"},
            {"name": "myotheremail", "pii": "personal_email"},
            {"name": "prefs", "pii": "preferences"},
        ],
        "raw": "none",
        "purpose": "security",
    }
    assert expected_result == sample_manifest


@pytest.mark.unit
def test_write_manifest(tmp_path):
    test_resource = {"foo": "bar", "bar": "baz"}
    expected_result = {"test": [{"foo": "bar", "bar": "baz"}]}
    test_path = str(tmp_path) + "/test.yml"
    manifests.write_manifest(test_path, test_resource, "test")

    with open(test_path, "r") as manifest:
        actual_result = yaml.safe_load(manifest)

    assert actual_result == expected_result


@pytest.mark.unit
def test_union_manifests(test_manifests):
    expected_result = {
        "dataset": [
            {
                "name": "Test Dataset 1",
                "description": "Test Dataset 1",
                "fides_key": "some_dataset",
                "organization_fides_key": 1,
                "datasetType": {},
                "datasetLocation": "somedb:3306",
                "datasetTables": [],
            },
            {
                "name": "Test Dataset 2",
                "description": "Test Dataset 2",
                "fides_key": "another_dataset",
                "organization_fides_key": 1,
                "datasetType": {},
                "datasetLocation": "somedb:3306",
                "datasetTables": [],
            },
        ],
        "system": [
            {
                "name": "Test System 1",
                "organization_fides_key": 1,
                "systemType": "mysql",
                "description": "Test System 1",
                "fides_key": "some_system",
            },
            {
                "name": "Test System 2",
                "organization_fides_key": 1,
                "systemType": "mysql",
                "description": "Test System 2",
                "fides_key": "another_system",
            },
        ],
    }
    actual_result = manifests.union_manifests(test_manifests.values())
    print(expected_result)
    print(actual_result)
    assert expected_result == actual_result


@pytest.mark.unit
@pytest.mark.parametrize(
    "ingestion_manifest_directory",
    ["populated_manifest_dir", "populated_nested_manifest_dir"],
    indirect=["ingestion_manifest_directory"],
)
def test_ingest_manifests(ingestion_manifest_directory):
    actual_result = manifests.ingest_manifests(str(ingestion_manifest_directory))

    # Battery of assertions for consistency
    assert sorted(actual_result) == ["dataset", "system"]
    assert len(actual_result["dataset"]) == 2
    assert len(actual_result["system"]) == 2
    assert sorted(actual_result["dataset"], key=lambda x: x["name"]) == [
        {
            "name": "Test Dataset 1",
            "organization_fides_key": 1,
            "datasetType": {},
            "datasetLocation": "somedb:3306",
            "description": "Test Dataset 1",
            "fides_key": "some_dataset",
            "datasetTables": [],
        },
        {
            "name": "Test Dataset 2",
            "description": "Test Dataset 2",
            "organization_fides_key": 1,
            "datasetType": {},
            "datasetLocation": "somedb:3306",
            "fides_key": "another_dataset",
            "datasetTables": [],
        },
    ]
    assert sorted(actual_result["system"], key=lambda x: x["name"]) == [
        {
            "name": "Test System 1",
            "organization_fides_key": 1,
            "systemType": "mysql",
            "description": "Test System 1",
            "fides_key": "some_system",
        },
        {
            "name": "Test System 2",
            "organization_fides_key": 1,
            "systemType": "mysql",
            "description": "Test System 2",
            "fides_key": "another_system",
        },
    ]

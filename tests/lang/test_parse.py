# pylint: disable=missing-docstring, redefined-outer-name
import pytest

import fideslang as models
from fideslang import parse


@pytest.mark.unit
def test_parse_manifest() -> None:
    expected_result = models.DataCategory(
        organization_fides_key=1,
        fides_key="some_resource",
        name="Test resource 1",
        description="Test Description",
    )
    test_dict = {
        "organization_fides_key": 1,
        "fides_key": "some_resource",
        "name": "Test resource 1",
        "description": "Test Description",
    }
    actual_result = parse.parse_dict("data_category", test_dict)
    assert actual_result == expected_result


@pytest.mark.unit
def test_parse_manifest_no_fides_key_validation_error() -> None:
    with pytest.raises(SystemExit):
        test_dict = {
            "organization_fides_key": 1,
            "name": "Test resource 1",
            "description": "Test Description",
        }
        parse.parse_dict("data_category", test_dict)
    assert True


@pytest.mark.unit
def test_parse_manifest_resource_type_error() -> None:
    with pytest.raises(SystemExit):
        test_dict = {
            "organization_fides_key": 1,
            "fides_key": "some_resource",
            "name": "Test resource 1",
            "description": "Test Description",
        }
        parse.parse_dict("data-category", test_dict)
    assert True


@pytest.mark.unit
def test_load_manifests_into_taxonomy() -> None:
    manifest_dict = {
        "data_category": [
            {
                "name": "User Data",
                "fides_key": "user",
                "description": "Test top-level category",
            },
            {
                "name": "User Provided Data",
                "fides_key": "user.provided",
                "parent_key": "user",
                "description": "Test sub-category",
            },
        ]
    }

    expected_taxonomy = models.Taxonomy(
        data_category=[
            models.DataCategory(
                name="User Data",
                fides_key="user",
                description="Test top-level category",
            ),
            models.DataCategory(
                name="User Provided Data",
                fides_key="user.provided",
                parent_key="user",
                description="Test sub-category",
            ),
        ]
    )
    assert parse.load_manifests_into_taxonomy(manifest_dict) == expected_taxonomy

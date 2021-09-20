import pytest
from pydantic import ValidationError

import fideslang as models
from fideslang import parse


@pytest.mark.unit
def test_parse_manifest():
    expected_result = models.DataCategory(
        organizationId=1,
        fides_key="some_resource",
        name="Test resource 1",
        clause="Test Clause",
        description="Test Description",
    )
    test_dict = {
        "organizationId": 1,
        "fides_key": "some_resource",
        "name": "Test resource 1",
        "clause": "Test Clause",
        "description": "Test Description",
    }
    actual_result = parse.parse_manifest("data_category", test_dict)
    assert actual_result == expected_result


@pytest.mark.unit
def test_parse_manifest_validation_error():
    with pytest.raises(SystemExit):
        test_dict = {
            "organizationId": 1,
            "name": "Test resource 1",
            "clause": "Test Clause",
            "description": "Test Description",
        }
        parse.parse_manifest("data_category", test_dict)
    assert True


@pytest.mark.unit
def test_parse_manifest_key_error():
    with pytest.raises(SystemExit):
        test_dict = {
            "organizationId": 1,
            "fides_key": "some_resource",
            "name": "Test resource 1",
            "clause": "Test Clause",
            "description": "Test Description",
        }
        parse.parse_manifest("data-category", test_dict)
    assert True


@pytest.mark.unit
def test_load_manifests_into_taxonomy():
    manifest_dict = {
        "data_category": [
            {
                "name": "User Provided Data",
                "fides_key": "user_provided_data",
                "description": "Data provided or created directly by a user of the system.",
            },
            {
                "name": "Credentials",
                "fides_key": "credentials",
                "description": "User provided authentication data.",
            },
        ]
    }

    expected_taxonomy = models.Taxonomy(
        data_category=[
            models.DataCategory(
                name="User Provided Data",
                fides_key="user_provided_data",
                description="Data provided or created directly by a user of the system.",
            ),
            models.DataCategory(
                name="Credentials",
                fides_key="credentials",
                description="User provided authentication data.",
            ),
        ]
    )
    assert parse.load_manifests_into_taxonomy(manifest_dict) == expected_taxonomy

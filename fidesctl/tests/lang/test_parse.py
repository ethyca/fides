import pytest

import fidesctl.lang as models
from fidesctl.lang import parse


@pytest.mark.unit
def test_parse_manifest():
    expected_result = models.DataCategory(
        organizationId=1,
        fidesKey="some_object",
        name="Test Object 1",
        clause="Test Clause",
        description="Test Description",
    )
    test_dict = {
        "organizationId": 1,
        "fidesKey": "some_object",
        "name": "Test Object 1",
        "clause": "Test Clause",
        "description": "Test Description",
    }
    actual_result = parse.parse_manifest("data-category", test_dict)
    assert actual_result == expected_result

from fidesctl.core import models, parse


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

"""Unit tests for the Commands module."""
import pytest

from fidesctl.core import apply, models


# Helpers
@pytest.fixture()
def server_object_list():
    yield [
        {"fidesKey": "testKey", "id": 1, "name": "Some Object"},
        {"fidesKey": "anotherTestKey", "id": 2, "name": "Another Object"},
    ]


@pytest.fixture()
def server_object_key_pairs():
    yield {"testKey": 1, "anotherTestKey": 2}


# Unit
@pytest.mark.unit
def test_sort_create_update_unchanged_create():
    object_1 = models.DataCategory(
        organizationId=1,
        fidesKey="some_object",
        name="Test Object 1",
        clause="Test Clause",
        description="Test Description",
    )
    object_2 = models.DataCategory(
        organizationId=1,
        fidesKey="another_system",
        name="Test System 2",
        clause="Test Clause",
        description="Test Description",
    )
    expected_create_result = [object_2]
    manifest_object_list = [object_2]
    server_object_list = [object_1]

    (
        create_result,
        update_result,
        unchanged_result,
    ) = apply.sort_create_update_unchanged(manifest_object_list, server_object_list)
    assert create_result == expected_create_result
    assert update_result == []
    assert unchanged_result == []


@pytest.mark.unit
def test_sort_create_update_unchanged_update():
    object_1 = models.DataCategory(
        id=1,
        organizationId=1,
        fidesKey="some_object",
        name="Test Object 1",
        clause="Test Clause",
        description="Test Description",
    )
    object_2 = models.DataCategory(
        organizationId=1,
        fidesKey="some_object",
        name="Test System 2",
        clause="Test Clause",
        description="Test Description",
    )
    expected_update_result = [object_2]
    manifest_object_list = [object_2]
    server_object_list = [object_1]

    (
        create_result,
        update_result,
        unchanged_result,
    ) = apply.sort_create_update_unchanged(manifest_object_list, server_object_list)
    assert [] == create_result
    assert expected_update_result == update_result
    assert [] == unchanged_result


@pytest.mark.unit
def test_sort_create_update_unchanged_unchanged():
    object_1 = models.DataCategory(
        id=1,
        organizationId=1,
        fidesKey="some_object",
        name="Test Object 1",
        clause="Test Clause",
        description="Test Description",
    )
    object_2 = models.DataCategory(
        organizationId=1,
        fidesKey="some_object",
        name="Test Object 1",
        clause="Test Clause",
        description="Test Description",
    )
    expected_unchanged_result = [object_2]
    manifest_object_list = [object_2]
    server_object_list = [object_1]

    (
        create_result,
        update_result,
        unchanged_result,
    ) = apply.sort_create_update_unchanged(manifest_object_list, server_object_list)
    assert [] == create_result
    assert [] == update_result
    assert expected_unchanged_result == unchanged_result


@pytest.mark.unit
def test_execute_create_update_unchanged_empty():
    apply.execute_create_update_unchanged(
        url="test", headers={"test": "test"}, object_type="test"
    )
    assert True

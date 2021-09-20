"""Unit tests for the Commands module."""
import pytest

from fidesctl.core import apply
import fideslang as models


# Helpers
@pytest.fixture()
def server_resource_list():
    yield [
        {"fides_key": "testKey", "id": 1, "name": "Some resource"},
        {"fides_key": "anotherTestKey", "id": 2, "name": "Another resource"},
    ]


@pytest.fixture()
def server_resource_key_pairs():
    yield {"testKey": 1, "anotherTestKey": 2}


# Unit
@pytest.mark.unit
def test_sort_create_update_unchanged_create():
    resource_1 = models.DataCategory(
        organizationId=1,
        fides_key="some_resource",
        name="Test resource 1",
        clause="Test Clause",
        description="Test Description",
    )
    resource_2 = models.DataCategory(
        organizationId=1,
        fides_key="another_system",
        name="Test System 2",
        clause="Test Clause",
        description="Test Description",
    )
    expected_create_result = [resource_2]
    manifest_resource_list = [resource_2]
    server_resource_list = [resource_1]

    (
        create_result,
        update_result,
        unchanged_result,
    ) = apply.sort_create_update_unchanged(manifest_resource_list, server_resource_list)
    assert create_result == expected_create_result
    assert update_result == []
    assert unchanged_result == []


@pytest.mark.unit
def test_sort_create_update_unchanged_update():
    resource_1 = models.DataCategory(
        id=1,
        organizationId=1,
        fides_key="some_resource",
        name="Test resource 1",
        clause="Test Clause",
        description="Test Description",
    )
    resource_2 = models.DataCategory(
        organizationId=1,
        fides_key="some_resource",
        name="Test System 2",
        clause="Test Clause",
        description="Test Description",
    )
    expected_update_result = [resource_2]
    manifest_resource_list = [resource_2]
    server_resource_list = [resource_1]

    (
        create_result,
        update_result,
        unchanged_result,
    ) = apply.sort_create_update_unchanged(manifest_resource_list, server_resource_list)
    assert [] == create_result
    assert expected_update_result == update_result
    assert [] == unchanged_result


@pytest.mark.unit
def test_sort_create_update_unchanged_unchanged():
    resource_1 = models.DataCategory(
        id=1,
        organizationId=1,
        fides_key="some_resource",
        name="Test resource 1",
        clause="Test Clause",
        description="Test Description",
    )
    resource_2 = models.DataCategory(
        organizationId=1,
        fides_key="some_resource",
        name="Test resource 1",
        clause="Test Clause",
        description="Test Description",
    )
    expected_unchanged_result = [resource_2]
    manifest_resource_list = [resource_2]
    server_resource_list = [resource_1]

    (
        create_result,
        update_result,
        unchanged_result,
    ) = apply.sort_create_update_unchanged(manifest_resource_list, server_resource_list)
    assert [] == create_result
    assert [] == update_result
    assert expected_unchanged_result == unchanged_result


@pytest.mark.unit
def test_execute_create_update_unchanged_empty():
    apply.execute_create_update_unchanged(
        url="test", headers={"test": "test"}, resource_type="test"
    )
    assert True

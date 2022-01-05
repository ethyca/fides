"""Unit tests for the Commands module."""
import pytest

from fidesctl.core import apply
import fideslang as models

from fideslang.models import Dataset, DatasetCollection, DatasetField


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


@pytest.fixture()
def test_unnested_fields():
    unnested_dataset = Dataset(
        fides_key="nested_test_dataset",
        organization_fides_key="default_organization",
        name="A dataset for testing nested data",
        description="A sample of unnested data for comparison all fields are collected",
        collections=[
            DatasetCollection(
                name="users",
                description="some nested and unnested user information",
                data_categories=[],
                data_qualifier="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                fields=[
                    DatasetField(
                        name="email",
                        description="User email address, no nested fields",
                        data_categories=[],
                        fields=None,
                    ),
                    DatasetField(
                        name="name",
                        description="User name, with nested fields",
                        data_categories=[],
                        fields=None,
                    ),
                ],
            )
        ],
    )

    yield unnested_dataset


@pytest.fixture()
def test_nested_fields():
    nested_dataset = Dataset(
        fides_key="nested_test_dataset",
        organization_fides_key="default_organization",
        name="A dataset for testing nested data",
        description="A sample of nested and unnested data to ensure all fields are collected",
        collections=[
            DatasetCollection(
                name="users",
                description="some nested and unnested user information",
                data_categories=[],
                data_qualifier="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                fields=[
                    DatasetField(
                        name="email",
                        description="User email address, no nested fields",
                        data_categories=[],
                        fields=None,
                    ),
                    DatasetField(
                        name="name",
                        description="User name, with nested fields",
                        data_categories=[],
                        fields=[
                            DatasetField(
                                name="first_name",
                                description="User first name",
                                data_categories=[],
                                fields=None,
                            ),
                            DatasetField(
                                name="last_name",
                                description="User last name",
                                data_categories=[],
                                fields=None,
                            ),
                            DatasetField(
                                name="other_info",
                                description="Other nested information",
                                data_categories=[],
                                fields=[
                                    DatasetField(
                                        name="other_nested_field",
                                        description="another nested field",
                                        data_categories=[],
                                        fields=None,
                                    ),
                                    DatasetField(
                                        name="another_other_nested_field",
                                        description="anoth other nested field",
                                        data_categories=[],
                                        fields=None,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    yield nested_dataset


# Unit
@pytest.mark.unit
def test_sort_create_update_unchanged_create():
    resource_1 = models.DataCategory(
        organization_fides_key=1,
        fides_key="some_resource",
        name="Test resource 1",
        description="Test Description",
    )
    resource_2 = models.DataCategory(
        organization_fides_key=1,
        fides_key="another_system",
        name="Test System 2",
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
        organization_fides_key=1,
        fides_key="some_resource",
        name="Test resource 1",
        description="Test Description",
    )
    resource_2 = models.DataCategory(
        organization_fides_key=1,
        fides_key="some_resource",
        name="Test System 2",
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
        organization_fides_key=1,
        fides_key="some_resource",
        name="Test resource 1",
        description="Test Description",
    )
    resource_2 = models.DataCategory(
        organization_fides_key=1,
        fides_key="some_resource",
        name="Test resource 1",
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


@pytest.mark.unit
def test_returns_all_nested_fields(test_unnested_fields, test_nested_fields):

    expected_update_result = [test_nested_fields]
    manifest_resource_list = [test_nested_fields]
    server_resource_list = [test_unnested_fields]
    (
        create_result,
        update_result,
        unchanged_result,
    ) = apply.sort_create_update_unchanged(manifest_resource_list, server_resource_list)

    nested_collection_fields = update_result[0].dict()["collections"][0]["fields"]
    nested_field_count = 0
    for field in nested_collection_fields:
        if "fields" in field and field["fields"] is not None:
            nested_field_count += 1
    # minimally tested here for now
    # this should likely be recursive and check for the exact number of nested fields or levels of nesting

    assert nested_field_count == 1

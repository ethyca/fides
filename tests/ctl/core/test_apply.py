# pylint: disable=missing-docstring, redefined-outer-name
"""Unit tests for the Commands module."""
from typing import Dict, Generator, List

import fideslang as models
import pytest

from fides.core.push import get_orphan_datasets, sort_create_update


# Helpers
@pytest.fixture()
def server_resource_list() -> Generator:
    yield [
        {"fides_key": "testKey", "id": 1, "name": "Some resource"},
        {"fides_key": "anotherTestKey", "id": 2, "name": "Another resource"},
    ]


@pytest.fixture()
def server_resource_key_pairs() -> Generator:
    yield {"testKey": 1, "anotherTestKey": 2}


@pytest.fixture()
def system_with_dataset_reference() -> Generator:
    yield [
        models.System(
            organization_fides_key="1",
            fides_key="test_system",
            system_type="test",
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="test_privacy_declaration",
                    data_categories=[],
                    data_use="test_data_use",
                    data_subjects=[],
                    dataset_references=["test_dataset"],
                ),
            ],
        ),
    ]


# Unit
@pytest.mark.unit
def test_sort_create_update_create() -> None:
    resource_1 = models.DataCategory(
        organization_fides_key="1",
        fides_key="some_resource",
        name="Test resource 1",
        description="Test Description",
    )
    resource_2 = models.DataCategory(
        organization_fides_key="1",
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
    ) = sort_create_update(manifest_resource_list, server_resource_list)
    assert create_result == expected_create_result
    assert update_result == []


@pytest.mark.unit
def test_sort_create_update_update() -> None:
    resource_1 = models.DataCategory(
        id=1,
        organization_fides_key="1",
        fides_key="some_resource",
        name="Test resource 1",
        description="Test Description",
    )
    resource_2 = models.DataCategory(
        organization_fides_key="1",
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
    ) = sort_create_update(manifest_resource_list, server_resource_list)
    assert [] == create_result
    assert expected_update_result == update_result


@pytest.mark.parametrize(
    "taxonomies, expected_length",
    [
        (
            {
                "dataset": [
                    models.Dataset(
                        organization_fides_key="1",
                        fides_key="test_dataset",
                        collections=[],
                    ),
                ],
            },
            0,
        ),
        (
            {
                "dataset": [
                    models.Dataset(
                        organization_fides_key="1",
                        fides_key="test_dataset_unused",
                        collections=[],
                    ),
                ],
            },
            1,
        ),
        (
            {
                "dataset": [
                    models.Dataset(
                        organization_fides_key="1",
                        fides_key="test_dataset",
                        collections=[],
                    ),
                    models.Dataset(
                        organization_fides_key="1",
                        fides_key="test_dataset_unused",
                        collections=[],
                    ),
                ],
            },
            1,
        ),
        (
            {
                "dataset": [
                    models.Dataset(
                        organization_fides_key="1",
                        fides_key="test_dataset",
                        collections=[],
                    ),
                    models.Dataset(
                        organization_fides_key="1",
                        fides_key="test_dataset_unused",
                        collections=[],
                    ),
                    models.Dataset(
                        organization_fides_key="1",
                        fides_key="test_dataset_also_unused",
                        collections=[],
                    ),
                ],
            },
            2,
        ),
    ],
)
@pytest.mark.unit
def test_validate_dataset_usage(
    taxonomies: Dict, expected_length: int, system_with_dataset_reference: List
) -> None:
    """
    Tests different scenarios for referenced datasets
    """
    taxonomies["system"] = system_with_dataset_reference
    taxonomy = models.Taxonomy.model_validate(taxonomies)
    missing_datasets = get_orphan_datasets(taxonomy)
    assert len(missing_datasets) == expected_length

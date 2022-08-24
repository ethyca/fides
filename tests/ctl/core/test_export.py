# pylint: disable=missing-docstring, redefined-outer-name
from typing import Generator

import pytest
from fideslang.models import (
    Dataset,
    DatasetCollection,
    DatasetField,
    DataSubject,
    DataUse,
    Organization,
    PrivacyDeclaration,
    System,
)

from fides.ctl.core import export
from fides.ctl.core.config import FidesctlConfig


@pytest.fixture()
def test_sample_system_taxonomy() -> Generator:
    yield {
        "system": [
            System(
                fides_key="test_system",
                system_type="test",
                system_name="test system",
                system_description="system used for testing exports",
                privacy_declarations=[
                    PrivacyDeclaration(
                        name="privacy_declaration_1",
                        data_categories=[
                            "user.contact.email",
                            "user.contact.name",
                        ],
                        data_use="provide.service",
                        data_qualifier="aggregated.anonymized",
                        data_subjects=["customer"],
                        dataset_references=["users_dataset"],
                    )
                ],
            )
        ],
        "data_subject": [DataSubject(fides_key="customer", name="customer")],
        "data_use": [
            DataUse(fides_key="provide.service", name="System", parent_key="provide")
        ],
    }


@pytest.fixture()
def test_sample_dataset_taxonomy() -> Generator:
    yield [
        Dataset(
            fides_key="test_dataset",
            name="test dataset",
            description="dataset for testing",
            dataset_categories=[],
            collections=[
                DatasetCollection(
                    name="test_collection",
                    data_categories=[],
                    fields=[
                        DatasetField(
                            name="test_field_1",
                            data_categories=["test_category_1"],
                            data_qualifier="aggregated.anonymized",
                            retention="No retention policy",
                        ),
                        DatasetField(
                            name="test_field_2",
                            data_categories=["test_category_2", "test_category_3"],
                            data_qualifier="aggregated.anonymized",
                        ),
                        DatasetField(
                            name="test_field_3",
                            data_categories=["test_category_3"],
                            data_qualifier="aggregated.anonymized",
                        ),
                        DatasetField(
                            name="test_field_4",
                            data_categories=["test_category_2"],
                            data_qualifier="aggregated.anonymized",
                        ),
                    ],
                )
            ],
        )
    ]


@pytest.mark.unit
def test_system_records_to_export(
    test_sample_system_taxonomy: Generator, test_config: FidesctlConfig
) -> None:
    """
    Asserts that unique records are returned properly (including
    the header row)
    """

    output_list = export.generate_system_records(test_sample_system_taxonomy)
    print(output_list)
    assert len(output_list) == 3


@pytest.mark.unit
def test_dataset_records_to_export(test_sample_dataset_taxonomy: Generator) -> None:
    """
    Asserts that unique records are returned properly (including
    the header row)
    """

    output_list = export.generate_dataset_records(test_sample_dataset_taxonomy)

    assert len(output_list) == 4


@pytest.mark.unit
def test_organization_records_to_export() -> None:
    """
    Asserts the default organization is successfully exported
    """

    output_list = export.generate_contact_records(
        [Organization(fides_key="default_organization")]
    )
    assert len(output_list) == 5

# pylint: disable=missing-docstring, redefined-outer-name
from typing import Dict, Generator

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

from fides.core import export
from fides.core.config import FidesConfig


@pytest.fixture()
def test_sample_system_taxonomy() -> Generator[Dict, None, None]:
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
                        dataset_references=["test_dataset"],
                    )
                ],
            )
        ],
        "data_subject": [DataSubject(fides_key="customer", name="customer")],
        "data_use": [
            DataUse(fides_key="provide.service", name="System", parent_key="provide")
        ],
        "organization": [
            Organization(
                fides_key="default_organization",
                security_policy="https://www.google.com/",
            )
        ],
    }


@pytest.fixture()
def test_sample_system_taxonomy_with_custom_fields():
    data = {
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
                        dataset_references=["test_dataset"],
                    )
                ],
            ).dict(),
        ],
        "data_subject": [DataSubject(fides_key="customer", name="customer").dict()],
        "data_use": [
            DataUse(
                fides_key="provide.service", name="System", parent_key="provide"
            ).dict()
        ],
        "organization": [
            Organization(
                fides_key="default_organization",
                security_policy="https://www.google.com/",
            ).dict()
        ],
    }

    data["system"][0]["custom_system_field"] = "custom system field"
    data["data_subject"][0]["custom_data_subject"] = "custom data subject"
    data["data_use"][0]["custom_data_use"] = "custom data use"

    yield data


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
    test_sample_system_taxonomy: Generator, test_config: FidesConfig
) -> None:
    """
    Asserts that unique records are returned properly (including
    the header row)
    """

    output_list, _ = export.generate_system_records(test_sample_system_taxonomy)
    assert len(output_list) == 3


@pytest.mark.usefixtures("test_config")
def test_system_records_to_export_with_custom_fields(
    test_sample_system_taxonomy_with_custom_fields,
):
    output_list, _ = export.generate_system_records(
        test_sample_system_taxonomy_with_custom_fields
    )
    assert len(output_list) == 3


@pytest.mark.unit
def test_system_records_to_export_sans_privacy_declaration(
    test_sample_system_taxonomy: Generator, test_config: FidesConfig
) -> None:
    """
    Asserts that unique records for systems without a privacy declaration
    are returned properly (including the header row)
    """
    test_sample_system_taxonomy["system"][0].privacy_declarations = []
    output_list, _ = export.generate_system_records(test_sample_system_taxonomy)
    print(output_list)
    assert len(output_list) == 2


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


@pytest.mark.unit
def test_joined_datamap_export_system_only(
    test_sample_system_taxonomy: Dict,
    test_config: FidesConfig,
) -> None:
    """
    Asserts the correct number of rows are exported for a basic system
    """
    sample_taxonomy: Dict = test_sample_system_taxonomy
    sample_taxonomy["dataset"] = []
    output_list = export.build_joined_dataframe(test_sample_system_taxonomy)
    assert len(output_list) == 2


@pytest.mark.unit
def test_joined_datamap_export_system_dataset_overlap(
    test_sample_system_taxonomy: Dict,
    test_sample_dataset_taxonomy: Generator,
    test_config: FidesConfig,
) -> None:
    """
    Asserts the correct number of rows are exported for a system with a dataset
    """
    sample_taxonomy: Dict = test_sample_system_taxonomy
    sample_taxonomy["dataset"] = test_sample_dataset_taxonomy
    output_list, _ = export.build_joined_dataframe(sample_taxonomy)
    assert len(output_list) == 5


@pytest.mark.unit
def test_joined_datamap_export_system_dataset_common(
    test_sample_system_taxonomy: Dict,
    test_config: FidesConfig,
) -> None:
    """
    Asserts the duplicate rows are removed from an export
    """
    sample_taxonomy: Dict = test_sample_system_taxonomy
    sample_taxonomy["dataset"] = [
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
                            data_categories=["user.contact.email"],
                            data_qualifier="aggregated.anonymized",
                            retention="No retention policy",
                        ),
                        DatasetField(
                            name="test_field_2",
                            data_categories=["user.contact.name"],
                            data_qualifier="aggregated.anonymized",
                        ),
                    ],
                )
            ],
        )
    ]
    output_list = export.build_joined_dataframe(sample_taxonomy)
    assert len(output_list) == 2


@pytest.mark.unit
def test_joined_datamap_export_system_multiple_declarations_overlap(
    test_sample_system_taxonomy: Dict,
    test_config: FidesConfig,
) -> None:
    """
    Asserts the correct number of rows are exported for a complex system
    """
    sample_taxonomy: Dict = test_sample_system_taxonomy
    new_data_subject = DataSubject(fides_key="prospect", name="prospect")
    new_declaration = PrivacyDeclaration(
        name="privacy_declaration_2",
        data_categories=[
            "user.contact.email",
            "user.contact.name",
        ],
        data_use="provide.service",
        data_qualifier="aggregated.anonymized",
        data_subjects=["prospect"],
    )
    sample_taxonomy["data_subject"].append(new_data_subject)
    sample_taxonomy["system"][0].privacy_declarations.append(new_declaration)
    sample_taxonomy["dataset"] = []
    output_list, _ = export.build_joined_dataframe(sample_taxonomy)
    assert len(output_list) == 4

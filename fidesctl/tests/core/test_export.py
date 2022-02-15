from os import path

import pytest

from fidesctl.core import export
from fideslang.models import (
    Dataset,
    DatasetCollection,
    DatasetField,
    PrivacyDeclaration,
    System,
)


@pytest.fixture()
def test_sample_system_taxonomy():
    yield [
        System(
            fides_key="test_system",
            system_type="test",
            system_name="test system",
            system_description="system used for testing exports",
            privacy_declarations=[
                PrivacyDeclaration(
                    name="privacy_declaration_1",
                    data_categories=["account.contact.email", "account.contact.name"],
                    data_use="provide.system",
                    data_qualifier="aggregated.anonymized",
                    data_subjects=["customer"],
                    dataset_references=["users_dataset"],
                )
            ],
        )
    ]


@pytest.fixture()
def test_sample_dataset_taxonomy():
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
def test_system_records_to_export(test_sample_system_taxonomy, test_config):
    """
    Asserts that unique records are returned properly (including
    the header row)
    """
    output_list = export.generate_system_records(
        test_sample_system_taxonomy,
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
    )
    print(output_list)
    assert len(output_list) == 3


@pytest.mark.unit
def test_dataset_data_category_rows(test_sample_dataset_taxonomy):

    dataset_name = test_sample_dataset_taxonomy[0].name
    dataset_description = test_sample_dataset_taxonomy[0].description
    dataset_third_country_transfers = test_sample_dataset_taxonomy[
        0
    ].third_country_transfers
    dataset_fides_key = test_sample_dataset_taxonomy[0].fides_key
    test_field = test_sample_dataset_taxonomy[0].collections[0].fields[1]

    dataset_rows = export.generate_data_category_rows(
        dataset_name,
        dataset_description,
        test_field.data_qualifier,
        test_field.data_categories,
        test_field.retention,
        dataset_third_country_transfers,
        dataset_fides_key,
    )

    assert len(dataset_rows) == 2


@pytest.mark.unit
def test_dataset_records_to_export(test_sample_dataset_taxonomy):
    """
    Asserts that unique records are returned properly (including
    the header row)
    """

    output_list = export.generate_dataset_records(test_sample_dataset_taxonomy)

    assert len(output_list) == 4


@pytest.mark.unit
def test_csv_export(tmpdir):
    """
    Asserts that the csv is successfully created
    """

    output_list = [("column_1", "column_2"), ("foo", "bar")]
    resource_exported = "test"

    exported_filename = export.export_to_csv(
        list_to_export=output_list,
        resource_exported=resource_exported,
        manifests_dir=f"{tmpdir}",
    )

    exported_file = tmpdir.join(exported_filename)

    assert path.exists(exported_file)

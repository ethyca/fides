from os import path

import pytest

import pandas as pd

from fidesctl.core import export_helpers
from fideslang.models import (
    Dataset,
    DatasetCollection,
    DatasetField,
)


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
def test_dataset_data_category_rows(test_sample_dataset_taxonomy):

    dataset_name = test_sample_dataset_taxonomy[0].name
    dataset_description = test_sample_dataset_taxonomy[0].description
    dataset_third_country_transfers = test_sample_dataset_taxonomy[
        0
    ].third_country_transfers
    dataset_fides_key = test_sample_dataset_taxonomy[0].fides_key
    test_field = test_sample_dataset_taxonomy[0].collections[0].fields[1]

    dataset_rows = export_helpers.generate_data_category_rows(
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
def test_csv_export(tmpdir):
    """
    Asserts that the csv is successfully created
    """

    output_list = [("column_1", "column_2"), ("foo", "bar")]
    resource_exported = "test"

    exported_filename = export_helpers.export_to_csv(
        list_to_export=output_list,
        resource_exported=resource_exported,
        manifests_dir=f"{tmpdir}",
    )

    exported_file = tmpdir.join(exported_filename)

    assert path.exists(exported_file)


@pytest.mark.unit
def test_xlsx_export(tmpdir):
    """
    Asserts that the xlsx template is successfully copied and appended to
    """
    output_columns = [
        "dataset.name",
        "system.name",
        "system.administrating_department",
        "system.privacy_declaration.data_use.name",
        "system.joint_controller",
        "system.privacy_declaration.data_subjects.name",
        "dataset.data_categories",
        "system.privacy_declaration.data_use.recipients",
        "system.link_to_processor_contract",
        "third_country_combined",
        "system.third_country_safeguards",
        "dataset.retention",
        "organization.link_to_security_policy",
        "system.data_responsibility_title",
        "system.privacy_declaration.data_use.legal_basis",
        "system.privacy_declaration.data_use.special_category",
        "system.privacy_declaration.data_use.legitimate_interest",
        "system.privacy_declaration.data_use.legitimate_interest_impact_assessment",
        "system.privacy_declaration.data_subjects.rights_available",
        "system.privacy_declaration.data_subjects.automated_decisions_or_profiling",
    ]

    organization_df = pd.DataFrame()
    joined_system_dataset_df = pd.DataFrame(columns=output_columns)

    exported_filename = export_helpers.export_datamap_to_excel(
        organization_df=organization_df,
        joined_system_dataset_df=joined_system_dataset_df,
        manifests_dir=f"{tmpdir}",
    )

    exported_file = tmpdir.join(exported_filename)

    assert path.exists(exported_file)

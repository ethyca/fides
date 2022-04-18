from os import path

import pandas as pd
import pytest
from fideslang.models import (
    DataProtectionImpactAssessment,
    Dataset,
    DatasetCollection,
    DatasetField,
    DataSubjectRights,
)

from fidesctl.core import export_helpers


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
        "unioned_data_categories",
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
        "dataset.name",
        "system.data_protection_impact_assessment.is_required",
        "system.data_protection_impact_assessment.progress",
        "system.data_protection_impact_assessment.link",
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


@pytest.mark.parametrize(
    "data_subject_rights",
    [
        {"strategy": "ALL"},
        {"strategy": "NONE"},
        {"strategy": "INCLUDE", "values": ["Informed", "Erasure"]},
        {
            "strategy": "EXCLUDE",
            "values": [
                "Access",
                "Rectification",
                "Portability",
                "Restrict Processing",
                "Withdraw Consent",
                "Object",
                "Object to Automated Processing",
            ],
        },
    ],
)
def test_calculate_data_subject_rights(data_subject_rights: dict):
    """Tests different strategy options for returning data subject rights."""
    rights = DataSubjectRights(**data_subject_rights)
    rights_dict = rights.dict()
    return_str_value = export_helpers.calculate_data_subject_rights(rights_dict)

    assert return_str_value is not None
    if data_subject_rights["strategy"] in ["INCLUDE", "EXCLUDE"]:
        assert return_str_value == "Informed, Erasure"


@pytest.mark.unit
def test_get_formatted_data_protection_impact_assessment():
    "Tests that only optional None values are formatted as N/A for exporting."
    formatted_dict = export_helpers.get_formatted_data_protection_impact_assessment(
        DataProtectionImpactAssessment().dict()
    )

    assert formatted_dict["is_required"] is False
    assert formatted_dict["progress"] == "N/A"
    assert formatted_dict["link"] == "N/A"

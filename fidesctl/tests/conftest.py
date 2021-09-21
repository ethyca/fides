"""Common fixtures to be used across tests."""
from typing import Any, Dict

import pytest
import yaml

import fideslang as models
from fidesctl.core.config import get_config


@pytest.fixture()
def test_config_path():
    yield "tests/test_config.toml"


@pytest.fixture()
def test_config(test_config_path):
    yield get_config(test_config_path)


@pytest.fixture()
def resources_dict():
    """
    Yields an resource containing sample representations of different
    Fides resources.
    """
    resources_dict: Dict[str, Any] = {
        "data_category": models.DataCategory(
            organization_fides_key=1,
            fides_key="customer_content_test_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
        ),
        "data_qualifier": models.DataQualifier(
            organization_fides_key=1,
            fides_key="test_data_qualifier",
            name="aggregated_data",
            clause="testDataClause",
            description="Test Data Qualifier",
        ),
        "dataset": models.Dataset(
            organization_fides_key=1,
            fides_key="test_sample_db_dataset",
            name="Sample DB Dataset",
            description="This is a Sample Database Dataset",
            dataset_type="MySQL",
            location="US East",
            fields=[
                models.DatasetField(
                    name="Food_Preference",
                    description="User's favorite food",
                    path="some.path",
                ),
                models.DatasetField(
                    name="First_Name",
                    description="A First Name Field",
                    path="another.path",
                    data_categories=["derived_data"],
                    data_qualifier="identified_data",
                ),
                models.DatasetField(
                    name="Email",
                    description="User's Email",
                    path="another.another.path",
                    data_categories=["account_data"],
                    data_qualifier="identified_data",
                ),
            ],
        ),
        "data_subject": models.DataSubject(
            organization_fides_key=1,
            fides_key="customer_content_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
        ),
        "data_use": models.DataUse(
            organization_fides_key=1,
            fides_key="customer_content_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
        ),
        "organization": models.Organization(
            fides_key="test_organization",
            name="Test Organization",
            description="Test Organization",
        ),
        "policy": models.Policy(
            organization_fides_key=1,
            fides_key="test_policy",
            name="Test Policy",
            version="1.3",
            description="Test Policy",
            rules=[],
        ),
        "policy_rule": models.PolicyRule(
            organization_fides_key=1,
            policyId=1,
            fides_key="test_policy",
            name="Test Policy",
            description="Test Policy",
            data_categories=models.PrivacyRule(inclusion="NONE", values=[]),
            data_uses=models.PrivacyRule(inclusion="NONE", values=["provide"]),
            data_subjects=models.PrivacyRule(inclusion="ANY", values=[]),
            data_qualifier="unlinked_pseudonymized_data",
            action="REJECT",
        ),
        "registry": models.Registry(
            organization_fides_key=1,
            fides_key="test_registry",
            name="Test Registry",
            description="Test Regsitry",
            systems=[],
        ),
        "system": models.System(
            organization_fides_key=1,
            registryId=1,
            fides_key="test_system",
            system_type="SYSTEM",
            name="Test System",
            description="Test Policy",
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="provide",
                    data_subjects=[],
                    data_qualifier="aggregated_data",
                    dataset_references=[],
                )
            ],
            system_dependencies=[],
        ),
    }
    yield resources_dict


@pytest.fixture()
def test_manifests():
    test_manifests = {
        "manifest_1": {
            "dataset": [
                {
                    "name": "Test Dataset 1",
                    "organization_fides_key": 1,
                    "datasetType": {},
                    "datasetLocation": "somedb:3306",
                    "description": "Test Dataset 1",
                    "fides_key": "some_dataset",
                    "datasetTables": [],
                }
            ],
            "system": [
                {
                    "name": "Test System 1",
                    "organization_fides_key": 1,
                    "systemType": "mysql",
                    "description": "Test System 1",
                    "fides_key": "some_system",
                }
            ],
        },
        "manifest_2": {
            "dataset": [
                {
                    "name": "Test Dataset 2",
                    "description": "Test Dataset 2",
                    "organization_fides_key": 1,
                    "datasetType": {},
                    "datasetLocation": "somedb:3306",
                    "fides_key": "another_dataset",
                    "datasetTables": [],
                }
            ],
            "system": [
                {
                    "name": "Test System 2",
                    "organization_fides_key": 1,
                    "systemType": "mysql",
                    "description": "Test System 2",
                    "fides_key": "another_system",
                }
            ],
        },
    }
    yield test_manifests


@pytest.fixture()
def populated_manifest_dir(test_manifests, tmp_path):
    for manifest in test_manifests.keys():
        with open(f"{tmp_path}/{manifest}.yml", "w") as manifest_file:
            yaml.dump(test_manifests[manifest], manifest_file)

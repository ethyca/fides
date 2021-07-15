"""Common fixtures to be used across tests."""
import os
from typing import Any, Dict

import pytest
import yaml

from fidesctl.core import models


@pytest.fixture()
def server_url():
    yield os.getenv("FIDES_SERVER_URL")


@pytest.fixture()
def objects_dict():
    """
    Yields an object containing sample representations of different
    Fides objects.
    """
    objects_dict: Dict[str, Any] = {
        "data-category": models.DataCategory(
            organizationId=1,
            fidesKey="customer_content_test_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
        ),
        "data-qualifier": models.DataQualifier(
            organizationId=1,
            fidesKey="test_data_qualifier",
            name="aggregated_data",
            clause="testDataClause",
            description="Test Data Qualifier",
        ),
        "dataset": models.Dataset(
            organizationId=1,
            fidesKey="test_sample_db_dataset",
            name="Sample DB Dataset",
            description="This is a Sample Database Dataset",
            datasetType="MySQL",
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
                    dataCategories=["derived_data"],
                    dataQualifier="identified_data",
                ),
                models.DatasetField(
                    name="Email",
                    description="User's Email",
                    path="another.another.path",
                    dataCategories=["account_data"],
                    dataQualifier="identified_data",
                ),
            ],
        ),
        "data-subject": models.DataSubject(
            organizationId=1,
            fidesKey="customer_content_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
        ),
        "data-use": models.DataUse(
            organizationId=1,
            fidesKey="customer_content_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
        ),
        "organization": models.Organization(
            fidesKey="test_organization",
            name="Test Organization",
            description="Test Organization",
        ),
        "policy": models.Policy(
            organizationId=1,
            fidesKey="test_policy",
            name="Test Policy",
            version="1.3",
            description="Test Policy",
            rules=[],
        ),
        "policy-rule": models.PolicyRule(
            organizationId=1,
            policyId=1,
            fidesKey="test_policy",
            name="Test Policy",
            description="Test Policy",
            dataCategories=models.PrivacyRule(inclusion="NONE", values=[]),
            dataUses=models.PrivacyRule(inclusion="NONE", values=["provide"]),
            dataSubjects=models.PrivacyRule(inclusion="ANY", values=[]),
            dataQualifier="unlinked_pseudonymized_data",
            action="REJECT",
        ),
        "registry": models.Registry(
            organizationId=1,
            fidesKey="test_registry",
            name="Test Registry",
            description="Test Regsitry",
            systems=[],
        ),
        "system": models.System(
            organizationId=1,
            registryId=1,
            fidesKey="test_system",
            systemType="SYSTEM",
            name="Test System",
            description="Test Policy",
            privacyDeclarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    dataCategories=[],
                    dataUse="provide",
                    dataSubjects=[],
                    dataQualifier="aggregated_data",
                    datasetReferences=[],
                )
            ],
            systemDependencies=[],
        ),
        "user": models.User(
            organizationId=1,
            userName="ethyca",
            firstName="privacy",
            lastName="engineering",
            role="ADMIN",
            apiKey="some_key",
        ),
    }
    yield objects_dict


@pytest.fixture()
def test_manifests():
    test_manifests = {
        "manifest_1": {
            "dataset": [
                {
                    "name": "Test Dataset 1",
                    "organizationId": 1,
                    "datasetType": {},
                    "datasetLocation": "somedb:3306",
                    "description": "Test Dataset 1",
                    "fidesKey": "some_dataset",
                    "datasetTables": [],
                }
            ],
            "system": [
                {
                    "name": "Test System 1",
                    "organizationId": 1,
                    "systemType": "mysql",
                    "description": "Test System 1",
                    "fidesKey": "some_system",
                }
            ],
        },
        "manifest_2": {
            "dataset": [
                {
                    "name": "Test Dataset 2",
                    "description": "Test Dataset 2",
                    "organizationId": 1,
                    "datasetType": {},
                    "datasetLocation": "somedb:3306",
                    "fidesKey": "another_dataset",
                    "datasetTables": [],
                }
            ],
            "system": [
                {
                    "name": "Test System 2",
                    "organizationId": 1,
                    "systemType": "mysql",
                    "description": "Test System 2",
                    "fidesKey": "another_system",
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

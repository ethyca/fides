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
            location="ethyca_mysql_db.ethyca_schema.ethyca_table",
            tables=[
                models.DatasetTable(
                    name="sample_db_table_1",
                    description="Sample DB Table Description",
                    fields=[
                        models.DatasetField(
                            name="Food Preference",
                            description="User's favorite food",
                        ),
                        models.DatasetField(
                            name="first_name",
                            description="A First Name Field",
                            dataCategories=["derived_data"],
                            dataQualifier="identified_data",
                        ),
                        models.DatasetField(
                            name="email",
                            description="User's Email",
                            dataCategories=["account_data"],
                            dataQualifier="identified_data",
                        ),
                    ],
                ),
            ],
        ),
        "data-subject": models.DataSubjectCategory(
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
            dataCategories=models.DataRule(inclusion="NONE", values=[]),
            dataUses=models.DataRule(inclusion="NONE", values=["provide"]),
            dataSubjectCategories=models.DataRule(inclusion="ANY", values=[]),
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
            fidesSystemType="SYSTEM",
            fidesOrganizationKey="Ethyca",
            name="Test System",
            description="Test Policy",
            declarations=[
                models.DataDeclaration(
                    name="declaration-name",
                    dataCategories=[],
                    dataUse="provide",
                    dataSubjectCategories=[],
                    dataQualifier="aggregated_data",
                )
            ],
            systemDependencies=[],
            datasets=["sample_db_dataset"],
        ),
        "user": models.User(
            organizationId=1,
            fidesKey="ethyca",
            userName="ethyca",
            firstName="privacy",
            lastName="engineering",
            role="ADMIN",
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
                    "fidesSystemType": "mysql",
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
                    "fidesSystemType": "mysql",
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

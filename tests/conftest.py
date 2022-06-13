# pylint: disable=missing-docstring, redefined-outer-name
"""Common fixtures to be used across tests."""
import os
from typing import Dict, Generator, Union

import pytest
import yaml
from fideslang import models
from starlette.testclient import TestClient

from fidesapi import main
from fidesctl.core import api
from fidesctl.core.config import FidesctlConfig, get_config

TEST_CONFIG_PATH = "tests/test_config.toml"
TEST_INVALID_CONFIG_PATH = "tests/test_invalid_config.toml"


@pytest.fixture(scope="session")
def test_config_path() -> Generator:
    yield TEST_CONFIG_PATH


@pytest.fixture(scope="session")
def test_invalid_config_path() -> Generator:
    """
    This config file contains url/connection strings that are invalid.

    This ensures that the CLI isn't calling out to those resources
    directly during certain tests.
    """
    yield TEST_INVALID_CONFIG_PATH


@pytest.fixture(scope="session")
def test_config(test_config_path: str) -> Generator:
    yield get_config(test_config_path)


@pytest.fixture(scope="session")
def test_client() -> Generator:
    """Starlette test client fixture. Easier to use mocks with when testing out API calls"""
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def setup_db(test_config: FidesctlConfig) -> Generator:
    "Sets up the database for testing."
    yield api.db_action(test_config.cli.server_url, "reset")


@pytest.fixture(scope="session")
def resources_dict() -> Generator:
    """
    Yields a resource containing sample representations of different
    Fides resources.
    """
    resources_dict: Dict[
        str,
        Union[
            models.DataCategory,
            models.DataQualifier,
            models.Dataset,
            models.DataSubject,
            models.DataUse,
            models.Evaluation,
            models.Organization,
            models.Policy,
            models.PolicyRule,
            models.Registry,
            models.System,
        ],
    ] = {
        "data_category": models.DataCategory(
            organization_fides_key=1,
            fides_key="user.provided.identifiable.custom",
            parent_key="user.provided.identifiable",
            name="Custom Data Category",
            description="Custom Data Category",
        ),
        "data_qualifier": models.DataQualifier(
            organization_fides_key=1,
            fides_key="custom_data_qualifier",
            name="Custom Data Qualifier",
            description="Custom Data Qualifier",
        ),
        "dataset": models.Dataset(
            organization_fides_key=1,
            fides_key="test_sample_db_dataset",
            name="Sample DB Dataset",
            description="This is a Sample Database Dataset",
            collections=[
                models.DatasetCollection(
                    name="user",
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
                            data_categories=["user.provided.identifiable.name"],
                            data_qualifier="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                        ),
                        models.DatasetField(
                            name="Email",
                            description="User's Email",
                            path="another.another.path",
                            data_categories=[
                                "user.provided.identifiable.contact.email"
                            ],
                            data_qualifier="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                        ),
                    ],
                )
            ],
        ),
        "data_subject": models.DataSubject(
            organization_fides_key=1,
            fides_key="custom_subject",
            name="Custom Data Subject",
            description="Custom Data Subject",
        ),
        "data_use": models.DataUse(
            organization_fides_key=1,
            fides_key="custom_data_use",
            name="Custom Data Use",
            description="Custom Data Use",
        ),
        "evaluation": models.Evaluation(
            fides_key="test_evaluation", status="PASS", details=["foo"], message="bar"
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
            name="Test Policy",
            data_categories=models.PrivacyRule(matches="NONE", values=[]),
            data_uses=models.PrivacyRule(matches="NONE", values=["provide.system"]),
            data_subjects=models.PrivacyRule(matches="ANY", values=[]),
            data_qualifier="aggregated.anonymized.unlinked_pseudonymized.pseudonymized",
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
def test_manifests() -> Generator:
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
def populated_manifest_dir(test_manifests: Dict, tmp_path: str) -> str:
    manifest_dir = f"{tmp_path}/populated_manifest"
    os.mkdir(manifest_dir)
    for manifest in test_manifests.keys():
        with open(f"{manifest_dir}/{manifest}.yml", "w") as manifest_file:
            yaml.dump(test_manifests[manifest], manifest_file)
    return manifest_dir


@pytest.fixture()
def populated_nested_manifest_dir(test_manifests: Dict, tmp_path: str) -> str:
    manifest_dir = f"{tmp_path}/populated_nested_manifest"
    os.mkdir(manifest_dir)
    for manifest in test_manifests.keys():
        nested_manifest_dir = f"{manifest_dir}/{manifest}"
        os.mkdir(nested_manifest_dir)
        with open(f"{nested_manifest_dir}/{manifest}.yml", "w") as manifest_file:
            yaml.dump(test_manifests[manifest], manifest_file)
    return manifest_dir

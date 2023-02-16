# pylint: disable=invalid-name, missing-docstring, redefined-outer-name

"""Common fixtures to be used across tests."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Generator, Union

import pytest
import requests
import yaml
from fideslang import models
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import ObjectDeletedError
from starlette.testclient import TestClient

from fides.api import main
from fides.api.ctl.database.session import engine, sync_engine, sync_session
from fides.api.ctl.sql_models import FidesUser, FidesUserPermissions
from fides.core import api
from fides.core.config import FidesConfig, get_config
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.lib.models.client import ClientDetail
from fides.lib.oauth.jwt import generate_jwe
from fides.lib.oauth.scopes import PRIVACY_REQUEST_READ, SCOPES
from tests.conftest import create_citext_extension

TEST_CONFIG_PATH = "tests/ctl/test_config.toml"
TEST_INVALID_CONFIG_PATH = "tests/ctl/test_invalid_config.toml"
TEST_DEPRECATED_CONFIG_PATH = "tests/ctl/test_deprecated_config.toml"


orig_requests_get = requests.get
orig_requests_post = requests.post
orig_requests_put = requests.put
orig_requests_patch = requests.patch
orig_requests_delete = requests.delete


@pytest.fixture(scope="session")
def monkeysession():
    """monkeypatch fixture at the session level instead of the function level"""
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(autouse=True, scope="session")
def monkeypatch_requests(test_client, monkeysession) -> None:
    """The requests library makes requests against the running webserver
    which talks to the application db.  This monkeypatching operation
    makes `requests` calls from src/fides/core/api.py in a test
    context talk to the test db instead"""
    monkeysession.setattr(requests, "get", test_client.get)
    monkeysession.setattr(requests, "post", test_client.post)
    monkeysession.setattr(requests, "put", test_client.put)
    monkeysession.setattr(requests, "patch", test_client.patch)
    monkeysession.setattr(requests, "delete", test_client.delete)


@pytest.fixture(scope="session")
def test_config_path() -> Generator:
    yield TEST_CONFIG_PATH


@pytest.fixture(scope="session")
def test_deprecated_config_path() -> Generator:
    yield TEST_DEPRECATED_CONFIG_PATH


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


@pytest.fixture(scope="function")
def test_config_dev_mode_disabled() -> Generator:
    original_value = CONFIG.dev_mode
    CONFIG.dev_mode = False
    yield CONFIG
    CONFIG.dev_mode = original_value


@pytest.fixture(scope="session")
def test_client() -> Generator:
    """Starlette test client fixture. Easier to use mocks with when testing out API calls"""
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def setup_db(test_config: FidesConfig, test_client, monkeypatch_requests) -> Generator:
    "Sets up the database for testing."
    assert CONFIG.test_mode
    assert (
        requests.post == test_client.post
    )  # Sanity check to make sure monkeypatch_requests fixture has run
    yield api.db_action(test_config.cli.server_url, "reset")


@pytest.fixture(scope="function")
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
            fides_key="user.custom",
            parent_key="user",
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
                            data_categories=["user.name"],
                            data_qualifier="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                        ),
                        models.DatasetField(
                            name="Email",
                            description="User's Email",
                            path="another.another.path",
                            data_categories=["user.contact.email"],
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
            data_uses=models.PrivacyRule(matches="NONE", values=["provide.service"]),
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


@pytest.fixture
def db() -> Generator:
    create_citext_extension(sync_engine)

    session = sync_session()

    yield session
    session.close()


@pytest.fixture(scope="session")
@pytest.mark.asyncio
async def async_session(test_client) -> AsyncSession:
    assert CONFIG.test_mode
    assert requests.post == test_client.post

    create_citext_extension(sync_engine)

    async_engine = create_async_engine(
        CONFIG.database.async_database_uri,
        echo=False,
    )

    session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        yield session
        session.close()
        async_engine.dispose()


def generate_auth_header_for_user(
    user: FidesUser, scopes: list[str], test_config: FidesConfig
) -> Dict[str, str]:
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), test_config.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


@pytest.fixture(autouse=True)
def clear_get_config_cache() -> None:
    get_config.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def event_loop() -> Generator:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

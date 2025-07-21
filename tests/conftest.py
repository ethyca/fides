import asyncio
import copy
import json
import os
import time
import types
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List
from unittest.mock import create_autospec
from uuid import uuid4

import boto3
import google.auth.credentials
import pytest
import requests
import yaml
from fastapi import Query
from fastapi.testclient import TestClient
from fideslang import DEFAULT_TAXONOMY, models
from fideslang.models import System as SystemSchema
from google.api_core.exceptions import NotFound
from google.cloud import storage
from httpx import AsyncClient
from loguru import logger
from moto import mock_aws
from pytest import MonkeyPatch
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fides.api.common_exceptions import PrivacyRequestExit
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
    JWE_PAYLOAD_SYSTEMS,
)
from fides.api.db.base_class import Base
from fides.api.db.crud import create_resource
from fides.api.db.ctl_session import sync_engine
from fides.api.db.database import seed_db
from fides.api.db.seed import load_default_organization, load_default_taxonomy
from fides.api.db.system import create_system
from fides.api.main import app
from fides.api.models.privacy_request import (
    EXITED_EXECUTION_LOG_STATUSES,
    RequestTask,
    generate_request_callback_pre_approval_jwe,
    generate_request_callback_resume_jwe,
)
from fides.api.models.sql_models import DataCategory as DataCategoryDbModel
from fides.api.models.sql_models import DataUse, PrivacyDeclaration, sql_model_map
from fides.api.oauth.jwt import generate_jwe
from fides.api.oauth.roles import APPROVER, CONTRIBUTOR, OWNER, VIEWER_AND_APPROVER
from fides.api.schemas.messaging.messaging import MessagingServiceType
from fides.api.task.graph_runners import access_runner, consent_runner, erasure_runner
from fides.api.tasks import celery_app
from fides.api.tasks.scheduled.scheduler import async_scheduler, scheduler
from fides.api.util.cache import get_cache
from fides.api.util.collection_util import Row
from fides.common.api.scope_registry import SCOPE_REGISTRY, USER_READ_OWN
from fides.config import get_config
from fides.config.config_proxy import ConfigProxy
from tests.fixtures.application_fixtures import *
from tests.fixtures.bigquery_fixtures import *
from tests.fixtures.datahub_fixtures import *
from tests.fixtures.detection_discovery_fixtures import *
from tests.fixtures.dynamodb_fixtures import *
from tests.fixtures.email_fixtures import *
from tests.fixtures.fides_connector_example_fixtures import *
from tests.fixtures.google_cloud_sql_mysql_fixtures import *
from tests.fixtures.google_cloud_sql_postgres_fixtures import *
from tests.fixtures.integration_fixtures import *
from tests.fixtures.manual_fixtures import *
from tests.fixtures.manual_webhook_fixtures import *
from tests.fixtures.mariadb_fixtures import *
from tests.fixtures.messaging_fixtures import *
from tests.fixtures.mongodb_fixtures import *
from tests.fixtures.mssql_fixtures import *
from tests.fixtures.mysql_fixtures import *
from tests.fixtures.okta_fixtures import *
from tests.fixtures.postgres_fixtures import *
from tests.fixtures.rds_mysql_fixtures import *
from tests.fixtures.rds_postgres_fixtures import *
from tests.fixtures.redshift_fixtures import *
from tests.fixtures.saas import *
from tests.fixtures.saas_erasure_order_fixtures import *
from tests.fixtures.saas_example_fixtures import *
from tests.fixtures.scylladb_fixtures import *
from tests.fixtures.snowflake_fixtures import *
from tests.fixtures.timescale_fixtures import *

ROOT_PATH = Path().absolute()
CONFIG = get_config()
TEST_CONFIG_PATH = "tests/ctl/test_config.toml"
TEST_INVALID_CONFIG_PATH = "tests/ctl/test_invalid_config.toml"
TEST_DEPRECATED_CONFIG_PATH = "tests/ctl/test_deprecated_config.toml"


@pytest.fixture
def s3_client(storage_config):
    """Creates a mock S3 client for testing."""
    with mock_aws():
        session = boto3.Session(
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
            region_name="us-east-1",
        )
        s3 = session.client("s3")
        s3.create_bucket(Bucket=storage_config.details[StorageDetails.BUCKET.value])
        yield s3


@pytest.fixture
def mock_s3_client(s3_client, monkeypatch):
    """Fixture to mock the S3 client for attachment tests"""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr(
        "fides.api.service.storage.s3.get_s3_client", mock_get_s3_client
    )
    return s3_client


@pytest.fixture(scope="session")
def db(api_client, config):
    """Return a connection to the test DB"""
    # Create the test DB engine
    assert config.test_mode
    assert requests.post != api_client.post
    engine = get_db_engine(
        database_uri=config.database.sqlalchemy_test_database_uri,
    )

    create_citext_extension(engine)

    if not scheduler.running:
        scheduler.start()
    if not async_scheduler.running:
        async_scheduler.start()

    SessionLocal = get_db_session(config, engine=engine)
    the_session = SessionLocal()
    # Setup above...

    yield the_session
    # Teardown below...
    the_session.close()
    engine.dispose()


@pytest.fixture(scope="session")
def test_client():
    """Starlette test client fixture. Easier to use mocks with when testing out API calls"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def async_session():
    assert CONFIG.test_mode

    create_citext_extension(sync_engine)

    async_engine = create_async_engine(
        f"{CONFIG.database.async_database_uri}?prepared_statement_cache_size=0",
        echo=False,
    )

    session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        yield session
        session.close()
        async_engine.dispose()


# TODO: THIS IS A HACKY WORKAROUND.
# This is specific for this test: test_get_resource_with_custom_field
# this was added to account for weird error that only happens during a
# long testing session. Something causes a config/schema change with
# the DB. Giving the test a dedicated session fixes the issue and
# matches how runtime works.
# It does look like there MAY be a small bug that is unlikely to ever
# occur during runtime. What surfaced the "benign" failure is the
# `connection_configs` relationship on the `System` model. We are
# unsure of which upstream test causes the error.
# https://github.com/MagicStack/asyncpg/blob/2f20bae772d71122e64f424cc4124e2ebdd46a58/asyncpg/exceptions/_base.py#L120-L124
# <class 'asyncpg.exceptions.InvalidCachedStatementError'>: cached statement plan is invalid due to a database schema or configuration change (SQLAlchemy asyncpg dialect will now invalidate all prepared caches in response to this exception)
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def async_session_temp(test_client):
    assert CONFIG.test_mode

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


@pytest.fixture(scope="session")
def api_client():
    """Return a client used to make API requests"""

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
async def async_api_client():
    """Return an async client used to make API requests"""
    async with AsyncClient(
        app=app, base_url="http://0.0.0.0:8080", follow_redirects=True
    ) as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def config():
    CONFIG.test_mode = True
    yield CONFIG


@pytest.fixture(scope="function")
def enable_tcf(config):
    assert config.test_mode
    config.consent.tcf_enabled = True
    yield config
    config.consent.tcf_enabled = False


@pytest.fixture(scope="function")
def enable_celery_worker(config):
    """This doesn't actually spin up a worker container"""
    celery_app.conf["task_always_eager"] = False
    yield config
    celery_app.conf["task_always_eager"] = True


@pytest.fixture(scope="function")
def enable_ac(config):
    assert config.test_mode
    config.consent.ac_enabled = True
    yield config
    config.consent.ac_enabled = False


@pytest.fixture(scope="function")
def enable_override_vendor_purposes(config, db):
    assert config.test_mode
    config.consent.override_vendor_purposes = True
    ApplicationConfig.create_or_update(
        db,
        data={"config_set": {"consent": {"override_vendor_purposes": True}}},
    )
    yield config
    config.consent.override_vendor_purposes = False
    ApplicationConfig.create_or_update(
        db,
        data={"config_set": {"consent": {"override_vendor_purposes": False}}},
    )


@pytest.fixture(scope="function")
def enable_override_vendor_purposes_api_set(db):
    """Enable override vendor purposes via api_set setting, not via traditional app config"""
    ApplicationConfig.create_or_update(
        db,
        data={"api_set": {"consent": {"override_vendor_purposes": True}}},
    )
    yield
    # reset back to false on teardown
    ApplicationConfig.create_or_update(
        db,
        data={"api_set": {"consent": {"override_vendor_purposes": False}}},
    )


@pytest.fixture
def loguru_caplog(caplog):
    handler_id = logger.add(caplog.handler, format="{message} | {extra}")
    yield caplog
    logger.remove(handler_id)


def create_citext_extension(engine: Engine) -> None:
    with engine.connect() as con:
        con.execute("CREATE EXTENSION IF NOT EXISTS citext;")


@pytest.fixture
def fides_toml_path():
    yield ROOT_PATH / ".fides" / "fides.toml"


@pytest.fixture
def oauth_client(db):
    """Return a client for authentication purposes."""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=SCOPE_REGISTRY,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client


@pytest.fixture
def oauth_root_client(db):
    """Return the configured root client (never persisted)"""
    return ClientDetail.get(
        db,
        object_id=CONFIG.security.oauth_root_client_id,
        config=CONFIG,
        scopes=SCOPE_REGISTRY,
    )


@pytest.fixture
def application_user(db, oauth_client):
    unique_username = f"user-{uuid4()}"
    user = FidesUser.create(
        db=db,
        data={
            "username": unique_username,
            "password": "test_password",
            "email_address": f"{unique_username}@ethyca.com",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    oauth_client.user_id = user.id
    oauth_client.save(db=db)
    yield user


@pytest.fixture
def user(db):
    try:
        user = FidesUser.create(
            db=db,
            data={
                "username": "test_fidesops_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
                "email_address": "fides.user@ethyca.com",
            },
        )
        permission = FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "roles": [APPROVER]}
        )
    except IntegrityError:
        user = db.query(FidesUser).filter_by(username="test_fidesops_user").first()
        permission = db.query(FidesUserPermissions).filter_by(user_id=user.id).first()
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[APPROVER],
        scopes=[],
        user_id=user.id,
    )

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    try:
        client.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture
def auth_header(request, oauth_client, config):
    client_id = oauth_client.id

    payload = {
        JWE_PAYLOAD_SCOPES: request.param,
        JWE_PAYLOAD_CLIENT_ID: client_id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), config.security.app_encryption_key)

    return {"Authorization": "Bearer " + jwe}


@pytest.fixture(scope="function", autouse=True)
def clear_get_config_cache() -> None:
    get_config.cache_clear()


@pytest.fixture(scope="session")
def test_config_path():
    yield TEST_CONFIG_PATH


@pytest.fixture(scope="session")
def test_deprecated_config_path():
    yield TEST_DEPRECATED_CONFIG_PATH


@pytest.fixture(scope="session")
def test_invalid_config_path():
    """
    This config file contains url/connection strings that are invalid.

    This ensures that the CLI isn't calling out to those resources
    directly during certain tests.
    """
    yield TEST_INVALID_CONFIG_PATH


@pytest.fixture(scope="session")
def test_config(test_config_path: str):
    yield get_config(test_config_path)


@pytest.fixture
def test_config_dev_mode_disabled():
    original_value = CONFIG.dev_mode
    CONFIG.dev_mode = False
    yield CONFIG
    CONFIG.dev_mode = original_value


@pytest.fixture
def resources_dict():
    """
    Yields a resource containing sample representations of different
    Fides resources.
    """
    resources_dict = {
        "data_category": models.DataCategory(
            organization_fides_key="1",
            fides_key="user.custom",
            parent_key="user",
            name="User dot Custom Data Category",
            description="Custom Data Category",
        ),
        "dataset": models.Dataset(
            organization_fides_key="1",
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
                        ),
                        models.DatasetField(
                            name="Email",
                            description="User's Email",
                            path="another.another.path",
                            data_categories=["user.contact.email"],
                        ),
                        models.DatasetField(
                            name="address",
                            description="example top level field for nesting",
                            path="table.address",
                            data_categories=["user.contact.address"],
                            fields=[
                                models.DatasetField(
                                    name="city",
                                    description="example city field",
                                    path="table.address.city",
                                    data_categories=["user.contact.address.city"],
                                ),
                                models.DatasetField(
                                    name="state",
                                    description="example state field",
                                    path="table.address.state",
                                    data_categories=["user.contact.address.state"],
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
        "data_subject": models.DataSubject(
            organization_fides_key="1",
            fides_key="custom_subject",
            name="Custom Data Subject",
            description="Custom Data Subject",
        ),
        "data_use": models.DataUse(
            organization_fides_key="1",
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
            organization_fides_key="1",
            fides_key="test_policy",
            name="Test Policy",
            version="1.3",
            description="Test Policy",
            rules=[],
        ),
        "policy_rule": models.PolicyRule(
            name="Test Policy",
            data_categories=models.PrivacyRule(matches="NONE", values=[]),
            data_uses=models.PrivacyRule(matches="NONE", values=["essential.service"]),
            data_subjects=models.PrivacyRule(matches="ANY", values=[]),
        ),
        "system": models.System(
            organization_fides_key="1",
            fides_key="test_system",
            system_type="SYSTEM",
            name="Test System",
            description="Test Policy",
            cookies=[],
            privacy_declarations=[
                models.PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="essential",
                    data_subjects=[],
                    dataset_references=[],
                    cookies=[],
                )
            ],
        ),
    }
    yield resources_dict


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def fideslang_resources(
    async_session,
    resources_dict,
    default_organization,
    default_taxonomy,
    config,
):
    """
    Loads all resources from resources_dict into the database.
    This fixture runs automatically before each test function.
    """

    # Load each resource into the database
    resources = copy.deepcopy(resources_dict)
    for resource_type, resource in resources.items():
        if resource_type in sql_model_map:
            if resource_type == "system":
                await create_system(
                    resource, async_session, config.security.oauth_root_client_id
                )
            else:
                await create_resource(
                    sql_model_map[resource_type],
                    resource.model_dump(mode="json"),
                    async_session,
                )


@pytest.fixture
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


@pytest.fixture
def populated_manifest_dir(test_manifests, tmp_path):
    manifest_dir = f"{tmp_path}/populated_manifest"
    os.mkdir(manifest_dir)
    for manifest in test_manifests.keys():
        with open(f"{manifest_dir}/{manifest}.yml", "w") as manifest_file:
            yaml.dump(test_manifests[manifest], manifest_file)
    return manifest_dir


@pytest.fixture
def populated_nested_manifest_dir(test_manifests, tmp_path):
    manifest_dir = f"{tmp_path}/populated_nested_manifest"
    os.mkdir(manifest_dir)
    for manifest in test_manifests.keys():
        nested_manifest_dir = f"{manifest_dir}/{manifest}"
        os.mkdir(nested_manifest_dir)
        with open(f"{nested_manifest_dir}/{manifest}.yml", "w") as manifest_file:
            yaml.dump(test_manifests[manifest], manifest_file)
    return manifest_dir


@pytest.fixture(scope="session")
def cache():
    yield get_cache()


@pytest.fixture
def root_auth_header(oauth_root_client):
    """Return an auth header for the root client"""
    payload = {
        JWE_PAYLOAD_SCOPES: oauth_root_client.scopes,
        JWE_PAYLOAD_CLIENT_ID: oauth_root_client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


def generate_auth_header_for_user(user, scopes):
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


@pytest.fixture
def generate_auth_header(oauth_client):
    return _generate_auth_header(oauth_client, CONFIG.security.app_encryption_key)


@pytest.fixture
def generate_auth_header_ctl_config(oauth_client):
    return _generate_auth_header(oauth_client, CONFIG.security.app_encryption_key)


def _generate_auth_header(oauth_client, app_encryption_key):
    client_id = oauth_client.id

    def _build_jwt(scopes):
        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), app_encryption_key)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


@pytest.fixture
def generate_policy_webhook_auth_header():
    def _build_jwt(webhook):
        jwe = generate_request_callback_resume_jwe(webhook)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


@pytest.fixture
def generate_pre_approval_webhook_auth_header():
    def _build_jwt(webhook):
        jwe = generate_request_callback_pre_approval_jwe(webhook)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


@pytest.fixture(scope="session")
def integration_config():
    yield load_toml("tests/ops/integration_test_config.toml")


@pytest.fixture(scope="session")
def celery_config():
    return {"task_always_eager": False}


@pytest.fixture(scope="session")
def celery_enable_logging():
    """Turns on celery output logs."""
    return True


@pytest.fixture(autouse=True, scope="session")
def celery_use_virtual_worker(celery_session_worker):
    """
    This is a catch-all fixture that forces all of our
    tests to use a virtual celery worker if a registered
    task is executed within the scope of the test.
    """
    yield celery_session_worker


@pytest.fixture(scope="session")
def run_privacy_request_task(celery_session_app):
    """
    This fixture is the version of the run_privacy_request task that is
    registered to the `celery_app` fixture which uses the virtualised `celery_worker`
    """
    yield celery_session_app.tasks[
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request"
    ]


class DSRThreeTestRunnerTimedOut(Exception):
    """DSR 3.0 Test Runner Timed Out"""


def wait_for_tasks_to_complete(
    db: Session, pr: PrivacyRequest, action_type: ActionType
):
    """Testing Helper for DSR 3.0 - repeatedly checks to see if all Request Tasks
    have exited so bogged down test doesn't hang"""

    def all_tasks_have_run(tasks: Query) -> bool:
        return all(tsk.status in EXITED_EXECUTION_LOG_STATUSES for tsk in tasks)

    db.commit()
    counter = 0
    while not all_tasks_have_run(
        (
            db.query(RequestTask).filter(
                RequestTask.privacy_request_id == pr.id,
                RequestTask.action_type == action_type,
            )
        )
    ):
        time.sleep(1)
        counter += 1
        if counter == 5:
            raise DSRThreeTestRunnerTimedOut()


def access_runner_tester(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
):
    """
    Function for testing the access request for either DSR 2.0 and DSR 3.0
    """
    try:
        return access_runner(
            privacy_request,
            policy,
            graph,
            connection_configs,
            identity,
            session,
            privacy_request_proceed=False,  # This allows the DSR 3.0 Access Runner to be tested in isolation, to just test running the access graph without queuing the privacy request
        )
    except PrivacyRequestExit:
        # DSR 3.0 intentionally raises a PrivacyRequestExit status while it waits for
        # RequestTasks to finish
        wait_for_tasks_to_complete(session, privacy_request, ActionType.access)
        return privacy_request.get_raw_access_results()


def erasure_runner_tester(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    access_request_data: Dict[str, List[Row]],
    session: Session,
):
    """
    Function for testing the erasure runner for either DSR 2.0 and DSR 3.0
    """
    try:
        return erasure_runner(
            privacy_request,
            policy,
            graph,
            connection_configs,
            identity,
            access_request_data,
            session,
            privacy_request_proceed=False,  # This allows the DSR 3.0 Erasure Runner to be tested in isolation
        )
    except PrivacyRequestExit:
        # DSR 3.0 intentionally raises a PrivacyRequestExit status while it waits
        # for RequestTasks to finish
        wait_for_tasks_to_complete(session, privacy_request, ActionType.erasure)
        return privacy_request.get_raw_masking_counts()


def consent_runner_tester(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
):
    """
    Function for testing the consent request for either DSR 2.0 and DSR 3.0
    """
    try:
        return consent_runner(
            privacy_request,
            policy,
            graph,
            connection_configs,
            identity,
            session,
            privacy_request_proceed=False,  # This allows the DSR 3.0 Consent Runner to be tested in isolation, to just test running the consent graph without queuing the privacy request
        )
    except PrivacyRequestExit:
        # DSR 3.0 intentionally raises a PrivacyRequestExit status while it waits for
        # RequestTasks to finish
        wait_for_tasks_to_complete(session, privacy_request, ActionType.consent)
        return privacy_request.get_consent_results()


@pytest.fixture(scope="session")
def analytics_opt_out():
    """Disable sending analytics when running tests."""
    original_value = CONFIG.user.analytics_opt_out
    CONFIG.user.analytics_opt_out = True
    yield
    CONFIG.user.analytics_opt_out = original_value


@pytest.fixture
def automatically_approved(db):
    """Do not require manual request approval"""
    original_value = CONFIG.execution.require_manual_request_approval
    CONFIG.execution.require_manual_request_approval = False
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.require_manual_request_approval = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture
def require_manual_request_approval(db):
    """Require manual request approval"""
    original_value = CONFIG.execution.require_manual_request_approval
    CONFIG.execution.require_manual_request_approval = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.require_manual_request_approval = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture
def subject_identity_verification_required(db):
    """Enable identity verification."""
    original_value = CONFIG.execution.subject_identity_verification_required
    CONFIG.execution.subject_identity_verification_required = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.subject_identity_verification_required = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def subject_identity_verification_not_required(db):
    """Disable identity verification for most tests unless overridden"""
    original_value = CONFIG.execution.subject_identity_verification_required
    CONFIG.execution.subject_identity_verification_required = False
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    yield
    CONFIG.execution.subject_identity_verification_required = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def disable_consent_identity_verification(db):
    """Fixture to set disable_consent_identity_verification for tests"""
    original_value = CONFIG.execution.disable_consent_identity_verification
    CONFIG.execution.disable_consent_identity_verification = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.disable_consent_identity_verification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def privacy_request_complete_email_notification_disabled(db):
    """Disable request completion email for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_completion_notification
    CONFIG.notifications.send_request_completion_notification = False
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    yield
    CONFIG.notifications.send_request_completion_notification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def privacy_request_receipt_notification_disabled(db):
    """Disable request receipt notification for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_receipt_notification
    CONFIG.notifications.send_request_receipt_notification = False
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    yield
    CONFIG.notifications.send_request_receipt_notification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def privacy_request_review_notification_disabled(db):
    """Disable request review notification for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_review_notification
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    CONFIG.notifications.send_request_review_notification = False
    yield
    CONFIG.notifications.send_request_review_notification = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def set_notification_service_type_to_mailgun(db):
    """Set default notification service type"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = MessagingServiceType.mailgun.value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()
    yield
    CONFIG.notifications.notification_service_type = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
    db.commit()


@pytest.fixture(scope="function")
def set_notification_service_type_to_none(db):
    """Overrides autouse fixture to remove default notification service type"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = None
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.notification_service_type = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def set_notification_service_type_to_twilio_email(db):
    """Overrides autouse fixture to set notification service type to twilio email"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = (
        MessagingServiceType.twilio_email.value
    )
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.notification_service_type = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def set_notification_service_type_to_twilio_text(db):
    """Overrides autouse fixture to set notification service type to twilio text"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = (
        MessagingServiceType.twilio_text.value
    )
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.notification_service_type = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def set_property_specific_messaging_enabled(db):
    """Overrides autouse fixture to enable property specific messaging"""
    original_value = CONFIG.notifications.enable_property_specific_messaging
    CONFIG.notifications.enable_property_specific_messaging = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.enable_property_specific_messaging = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def set_property_specific_messaging_disabled(db):
    """Disable property specific messaging for all tests unless overridden"""
    original_value = CONFIG.notifications.enable_property_specific_messaging
    CONFIG.notifications.enable_property_specific_messaging = False
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.notifications.enable_property_specific_messaging = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="session")
def config_proxy(db):
    return ConfigProxy(db)


@pytest.fixture(scope="function")
def oauth_role_client(db: Session) -> Generator:
    """Return a client that has all roles for authentication purposes
    This is not a typical state but this client will then work with any
    roles a token is given
    """
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[OWNER, APPROVER, VIEWER, VIEWER_AND_APPROVER, CONTRIBUTOR],
    )  # Intentionally adding all roles here so the client will always
    # have a role that matches a role on a token for testing
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client


def generate_role_header_for_user(user, roles) -> Dict[str, str]:
    payload = {
        JWE_PAYLOAD_ROLES: roles,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


@pytest.fixture(scope="function")
def generate_role_header(oauth_role_client) -> Callable[[Any], Dict[str, str]]:
    return _generate_auth_role_header(
        oauth_role_client, CONFIG.security.app_encryption_key
    )


def _generate_auth_role_header(
    oauth_role_client, app_encryption_key
) -> Callable[[Any], Dict[str, str]]:
    client_id = oauth_role_client.id

    def _build_jwt(roles: List[str]) -> Dict[str, str]:
        payload = {
            JWE_PAYLOAD_ROLES: roles,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), app_encryption_key)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


@pytest.fixture(scope="function")
def oauth_system_client(db: Session, system) -> Generator:
    """Return a client that has system for authentication purposes"""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        systems=[system.id],
    )  # Intentionally adding all roles here so the client will always
    # have a role that matches a role on a token for testing
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client


@pytest.fixture(scope="function")
def generate_system_manager_header(
    oauth_system_client,
) -> Callable[[Any], Dict[str, str]]:
    return _generate_system_manager_header(
        oauth_system_client, CONFIG.security.app_encryption_key
    )


def _generate_system_manager_header(
    oauth_system_client, app_encryption_key
) -> Callable[[Any], Dict[str, str]]:
    client_id = oauth_system_client.id

    def _build_jwt(systems: List[str]) -> Dict[str, str]:
        payload = {
            JWE_PAYLOAD_ROLES: [],
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SYSTEMS: systems,
        }
        jwe = generate_jwe(json.dumps(payload), app_encryption_key)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


@pytest.fixture
def owner_client(db):
    """Return a client with an "owner" role for authentication purposes."""
    client = ClientDetail(
        hashed_secret="thisisatest", salt="thisisstillatest", scopes=[], roles=[OWNER]
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client
    client.delete(db)


@pytest.fixture
def viewer_client(db):
    """Return a client with a "viewer" role for authentication purposes."""
    client = ClientDetail(
        hashed_secret="thisisatest", salt="thisisstillatest", scopes=[], roles=[VIEWER]
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client
    client.delete(db)


@pytest.fixture
def owner_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_owner_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "owner.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[OWNER],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [OWNER]})

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def approver_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_viewer_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "approver.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[APPROVER],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [APPROVER]})

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def viewer_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_viewer_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "viewer2.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[VIEWER],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [VIEWER]})

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def contributor_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_contributor_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "contributor.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[CONTRIBUTOR],
        user_id=user.id,
    )

    FidesUserPermissions.create(
        db=db, data={"user_id": user.id, "roles": [CONTRIBUTOR]}
    )

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def respondent(db):
    """Create a respondent user with USER_READ_OWN scope"""
    from fides.api.oauth.roles import RESPONDENT

    user = FidesUser.create(
        db=db,
        data={
            "username": "test_respondent_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "respondent.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[USER_READ_OWN],
        roles=[RESPONDENT],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [RESPONDENT]})

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture
def viewer_and_approver_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_viewer_and_approver_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "viewerapprover.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[VIEWER_AND_APPROVER],
        user_id=user.id,
    )

    FidesUserPermissions.create(
        db=db, data={"user_id": user.id, "roles": [VIEWER_AND_APPROVER]}
    )

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    user.delete(db)


@pytest.fixture(scope="function")
def system(db: Session) -> System:
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    privacy_declaration = PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for marketing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "marketing.advertising",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )

    db.refresh(system)
    return system


@pytest.fixture()
@pytest.mark.asyncio
async def system_async(async_session):
    """Creates a system for testing with an async session, to be used in async tests"""
    resource = SystemSchema(
        fides_key=str(uuid4()),
        organization_fides_key="default_organization",
        name="test_system_1",
        system_type="test",
        privacy_declarations=[],
    )

    system = await create_system(
        resource, async_session, CONFIG.security.oauth_root_client_id
    )
    return system


@pytest.fixture(scope="function")
def system_hidden(db: Session) -> Generator[System, None, None]:
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system set as hidden",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "hidden": True,
        },
    )

    db.refresh(system)
    yield system
    db.delete(system)


@pytest.fixture(scope="function")
def system_with_cleanup(db: Session) -> Generator[System, None, None]:
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    privacy_declaration = PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for marketing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "marketing.advertising",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )

    ConnectionConfig.create(
        db=db,
        data={
            "system_id": system.id,
            "connection_type": "bigquery",
            "name": "test_connection",
            "secrets": {"password": "test_password"},
            "access": "write",
        },
    )

    db.refresh(system)
    yield system
    db.delete(system)


@pytest.fixture(scope="function")
def system_with_dataset_references(db: Session) -> System:
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db, {"fides_key": f"dataset_key-f{uuid4()}", "collections": []}
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "dataset_references": [ctl_dataset.fides_key],
        },
    )

    return system


@pytest.fixture(scope="function")
def system_with_undeclared_data_categories(db: Session) -> System:
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {"name": "first_name"},
                    ],
                }
            ],
        },
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "dataset_references": [ctl_dataset.fides_key],
        },
    )

    return system


@pytest.fixture(scope="function")
def system_with_a_single_dataset_reference(db: Session) -> System:
    first_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "loyalty",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                    ],
                }
            ],
        },
    )
    second_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "shipping_info",
                            "fields": [
                                {
                                    "name": "street",
                                    "data_categories": ["user.contact.address.street"],
                                }
                            ],
                        },
                        {
                            "name": "first_name",
                            "data_categories": ["user.name.first"],
                        },
                    ],
                },
                {
                    "name": "activity",
                    "fields": [
                        {
                            "name": "last_login",
                            "data_categories": ["user.behavior"],
                        },
                    ],
                },
            ],
        },
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "dataset_references": [first_dataset.fides_key, second_dataset.fides_key],
        },
    )

    return system


@pytest.fixture(scope="function")
def privacy_declaration_with_single_dataset_reference(
    db: Session,
) -> PrivacyDeclaration:
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {"name": "first_name"},
                    ],
                }
            ],
        },
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    privacy_declaration = PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for third party sharing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "third_party_sharing",
            "data_subjects": ["customer"],
            "dataset_references": [ctl_dataset.fides_key],
            "egress": None,
            "ingress": None,
        },
    )

    return privacy_declaration


@pytest.fixture(scope="function")
def privacy_declaration_with_multiple_dataset_references(
    db: Session,
) -> PrivacyDeclaration:
    first_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "loyalty",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                    ],
                }
            ],
        },
    )
    second_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "shipping_info",
                            "fields": [
                                {
                                    "name": "street",
                                    "data_categories": ["user.contact.address.street"],
                                }
                            ],
                        },
                        {
                            "name": "first_name",
                            "data_categories": ["user.name.first"],
                        },
                    ],
                },
                {
                    "name": "activity",
                    "fields": [
                        {
                            "name": "last_login",
                            "data_categories": ["user.behavior"],
                        },
                    ],
                },
            ],
        },
    )
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    privacy_declaration = PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for third party sharing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "third_party_sharing",
            "data_subjects": ["customer"],
            "dataset_references": [first_dataset.fides_key, second_dataset.fides_key],
            "egress": None,
            "ingress": None,
        },
    )

    return privacy_declaration


@pytest.fixture(scope="function")
def system_multiple_decs(db: Session, system: System) -> Generator[System, None, None]:
    """
    Add an additional PrivacyDeclaration onto the base System to test scenarios with
    multiple PrivacyDeclarations on a given system
    """
    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for third party sharing",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "third_party_sharing",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )

    db.refresh(system)
    yield system


@pytest.fixture(scope="function")
def system_third_party_sharing(db: Session) -> Generator[System, None, None]:
    system_third_party_sharing = System.create(
        db=db,
        data={
            "fides_key": f"system_third_party_sharing-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for third party sharing",
            "system_id": system_third_party_sharing.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "third_party_sharing",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )
    db.refresh(system_third_party_sharing)
    yield system_third_party_sharing
    db.delete(system_third_party_sharing)


@pytest.fixture(scope="function")
def system_provide_service(db: Session) -> System:
    system_provide_service = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "The source service, system, or product being provided to the user",
            "system_id": system_provide_service.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "essential.service",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )
    db.refresh(system_provide_service)
    return system_provide_service


@pytest.fixture(scope="function")
def system_provide_service_operations_support_optimization(db: Session) -> System:
    system_provide_service_operations_support_optimization = System.create(
        db=db,
        data={
            "fides_key": f"system_key-f{uuid4()}",
            "name": f"system-{uuid4()}",
            "description": "fixture-made-system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Optimize and improve support operations in order to provide the service",
            "system_id": system_provide_service_operations_support_optimization.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "essential.service.operations.improve",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "egress": None,
            "ingress": None,
        },
    )
    db.refresh(system_provide_service_operations_support_optimization)
    return system_provide_service_operations_support_optimization


@pytest.fixture
def system_manager_client(db, system):
    """Return a client assigned to a system for authentication purposes."""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[],
        systems=[system.id],
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client
    client.delete(db)


@pytest.fixture
def connection_client(db, connection_config):
    """Return a client assigned to a connection for authentication purposes."""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[],
        systems=[],
        connections=[connection_config.id],
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client
    client.delete(db)


@pytest.fixture
def owner_auth_header(owner_user):
    return generate_role_header_for_user(owner_user, owner_user.client.roles)


@pytest.fixture
def contributor_auth_header(contributor_user):
    return generate_role_header_for_user(
        contributor_user, contributor_user.client.roles
    )


@pytest.fixture
def viewer_auth_header(viewer_user):
    return generate_role_header_for_user(viewer_user, viewer_user.client.roles)


@pytest.fixture
def approver_auth_header(approver_user):
    return generate_role_header_for_user(approver_user, approver_user.client.roles)


@pytest.fixture
def viewer_and_approver_auth_header(viewer_and_approver_user):
    return generate_role_header_for_user(
        viewer_and_approver_user, viewer_and_approver_user.client.roles
    )


@pytest.mark.asyncio
@pytest.fixture(scope="function")
def seed_data(session):
    """
    Fixture to load default resources into the database before a test.
    """
    seed_db(session)


@pytest.fixture(scope="function")
def default_data_categories(db: Session):
    for data_category in DEFAULT_TAXONOMY.data_category:
        if (
            DataCategoryDbModel.get_by(db, field="name", value=data_category.name)
            is None
        ):
            DataCategoryDbModel.create(
                db=db, data=data_category.model_dump(mode="json")
            )


@pytest.fixture(scope="function")
def default_data_uses(db: Session):
    for data_use in DEFAULT_TAXONOMY.data_use:
        if DataUse.get_by(db, field="name", value=data_use.name) is None:
            DataUse.create(db=db, data=data_use.model_dump(mode="json"))


@pytest.fixture(scope="function")
def default_organization(db: Session):
    load_default_organization(db)


@pytest.fixture(scope="function")
def default_taxonomy(db: Session):
    load_default_taxonomy(db)


@pytest.fixture(scope="function", autouse=True)
async def clear_db_tables(db, async_session):
    """Clear data from tables between tests.

    If relationships are not set to cascade on delete they will fail with an
    IntegrityError if there are relationships present. This function stores tables
    that fail with this error then recursively deletes until no more IntegrityErrors
    are present.
    """
    yield

    def delete_data(tables):
        redo = []
        for table in tables:
            try:
                db.execute(table.delete())
            except IntegrityError:
                redo.append(table)
            finally:
                db.commit()

        if redo:
            delete_data(redo)

    # make sure all transactions are closed before starting deletes
    db.commit()
    await async_session.commit()

    delete_data(Base.metadata.sorted_tables)


@pytest.fixture(autouse=True, scope="session")
def monkeysession():
    """
    Monkeypatch at the session level instead of the function level.
    Automatically undoes the monkeypatching when the session finishes.
    """
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="session")
def monkeypatch_requests(test_client, monkeysession) -> None:
    """
    Some places within the application, for example `fides.core.api`, use the `requests`
    library to interact with the webserver. This fixture patches those `requests` calls
    so that all of those tests instead interact with the test instance.
    """
    monkeysession.setattr(requests, "get", test_client.get)
    monkeysession.setattr(requests, "post", test_client.post)
    monkeysession.setattr(requests, "put", test_client.put)
    monkeysession.setattr(requests, "patch", test_client.patch)
    monkeysession.setattr(requests, "delete", test_client.delete)


def pytest_configure_node(node):
    """Pytest hook automatically called for each xdist worker node configuration."""
    if hasattr(node, "workerinput") and node.workerinput:
        worker_id = node.workerinput["workerid"]
        print(
            f"[Configure Node] Configuring database and config for worker {worker_id}..."
        )

        os.environ["FIDES__DATABASE__TEST_DB"] = f"fides_test_{worker_id}"

        get_config.cache_clear()
        fides_config = get_config()
        sync_db_uri = fides_config.database.sqlalchemy_test_database_uri
        async_db_uri = fides_config.database.async_database_uri

        # Log connection strings
        print(
            f"[Configure Node] Sync DB URI: {sync_db_uri} Async DB URI: {async_db_uri}"
        )
    else:
        print(
            "[Configure Node] Skipping DB setup/config update on single node or non-xdist run."
        )


@pytest.fixture
def base_gcs_client_mock():
    """Fixture to provide a base mock for Google Cloud Storage (GCS) client.

    This fixture creates a base mock of the GCS client with proper method signatures
    and basic functionality. It uses `create_autospec` to ensure that the mock
    maintains the same interface as the real GCS client, which helps catch interface
    changes and ensures type safety.

    The fixture sets up:
    - Mock credentials with proper autospec
    - Mock client with required attributes
    - Mock batch stack for handling batch operations
    - Mock HTTP transport for handling requests
    - Basic bucket method implementation

    Usage:
        ```python
        def test_something(base_gcs_client_mock):
            # The mock client will have the same interface as the real GCS client
            bucket = base_gcs_client_mock.bucket("my-bucket")
            # Any method calls will be properly type-checked
        ```

    Why autospec is used:
    - Ensures the mock has the same interface as the real GCS client
    - Catches interface changes that would break the real code
    - Provides better error messages when methods are called incorrectly
    - Maintains type safety throughout the test
    """
    # Create mock credentials with proper autospec
    mock_credentials = create_autospec(google.auth.credentials.Credentials)
    mock_credentials.valid = True
    mock_credentials.expired = False
    mock_credentials.refresh = create_autospec(
        google.auth.credentials.Credentials.refresh, side_effect=lambda: None
    )

    # Create mock client with proper autospec
    mock_client = create_autospec(storage.Client)
    mock_client._credentials = mock_credentials
    mock_client.project = "test-project"

    # Set up batch stack
    class MockBatchStack:
        """Mock implementation of GCS batch operation stack."""

        def __init__(self):
            self._stack = []

        @property
        def top(self):
            """Returns the top batch in the stack or None if empty."""
            return self._stack[-1] if self._stack else None

        def push(self, batch):
            """Adds a new batch to the top of the stack."""
            self._stack.append(batch)

        def pop(self):
            """Removes and returns the top batch from the stack."""
            return self._stack.pop() if self._stack else None

    # Set up HTTP transport with proper autospec
    mock_http = create_autospec(requests.Session)
    mock_response = create_autospec(requests.Response)
    mock_response.status_code = 200
    mock_http.request = create_autospec(
        requests.Session.request, return_value=mock_response
    )

    # Add required attributes to mock client
    mock_client._batch_stack = MockBatchStack()
    mock_client._http_internal = mock_http
    mock_client._http = mock_http

    # Set up bucket method with proper autospec
    def mock_get_bucket(self, bucket_name, user_project=None, generation=None):
        """Creates and returns a mock bucket with the given name."""
        mock_bucket = create_autospec(storage.Bucket)
        mock_bucket.name = bucket_name
        return mock_bucket

    mock_client.bucket = types.MethodType(
        create_autospec(storage.Client.bucket, side_effect=mock_get_bucket), mock_client
    )

    return mock_client


@pytest.fixture
def mock_gcs_client(
    base_gcs_client_mock, monkeypatch, storage_config_default_gcs, attachment_file
):
    """Fixture to provide a fully configured mock GCS client for attachment testing.

    This fixture extends the base_gcs_client_mock with attachment-specific behavior,
    implementing a mock of the GCS client's functionality needed for testing
    upload and deletion of files. It uses `create_autospec` to ensure type safety and proper
    method signatures throughout the mock hierarchy.

    Key features:
    - Tracks all blobs in a bucket using a dictionary
    - Simulates blob creation, deletion, and access
    - Implements proper error handling (e.g., NotFound exceptions)
    - Supports blob listing with prefix filtering
    - Maintains proper method signatures through autospec

    The mock implements the following GCS operations:
    - Blob creation and upload
    - Blob deletion
    - Blob retrieval
    - Signed URL generation
    - Blob listing with prefix support

    Usage:
        ```python
        def test_attachment_operations(mock_gcs_client):
            # Create and upload an attachment
            bucket = mock_gcs_client.bucket("test-bucket")
            blob = bucket.blob("test-file.txt")
            blob.upload_from_file(file_obj)

            # Delete the attachment
            blob.delete()

            # Attempting to access deleted blob raises NotFound
            with pytest.raises(NotFound):
                blob.reload()
        ```

    Why autospec is used:
    - Ensures all mock methods have the same signature as real GCS methods
    - Catches interface changes that would break the real code
    - Provides better error messages for incorrect method calls
    - Maintains type safety throughout the test
    - Helps catch bugs related to method signature changes

    Dependencies:
        - base_gcs_client_mock: Provides the base GCS client mock
        - storage_config_default_gcs: Provides GCS storage configuration
        - attachment_file: Provides test file content for size calculations
    """
    # Get the file content for size calculation
    file_content = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset file pointer

    # Create a mock bucket with proper autospec
    mock_bucket = create_autospec(storage.Bucket)
    mock_bucket.name = storage_config_default_gcs.details[StorageDetails.BUCKET.value]

    # Track all blobs
    blobs = {}

    # Set up the mock bucket's blob method with proper autospec
    def mock_get_blob(self, blob_name, *args, **kwargs):
        """Retrieves a blob by name, raising NotFound if it doesn't exist."""
        # Check if blob exists
        if blob_name not in blobs:
            raise NotFound(f"Blob {blob_name} not found")

        mock_blob = blobs[blob_name]
        return mock_blob

    # Set up bucket methods with proper autospec
    mock_bucket.blob = types.MethodType(
        create_autospec(storage.Bucket.blob, side_effect=mock_get_blob), mock_bucket
    )

    def mock_list_blobs(
        self, prefix=None, delimiter=None, max_results=None, page_token=None, **kwargs
    ):
        """Lists all blobs in the bucket, optionally filtered by prefix."""
        if prefix:
            return [blob for name, blob in blobs.items() if name.startswith(prefix)]
        return list(blobs.values())

    mock_bucket.list_blobs = types.MethodType(
        create_autospec(storage.Bucket.list_blobs, side_effect=mock_list_blobs),
        mock_bucket,
    )

    # Set up the mock client's bucket method with proper autospec
    def mock_get_bucket(self, bucket_name, user_project=None, generation=None):
        """Returns the mock bucket if the name matches, otherwise raises ValueError."""
        if bucket_name != mock_bucket.name:
            raise ValueError(
                f"Expected bucket name {mock_bucket.name}, got {bucket_name}"
            )
        return mock_bucket

    # Update the base mock's bucket method with proper autospec
    base_gcs_client_mock.bucket = types.MethodType(
        create_autospec(storage.Client.bucket, side_effect=mock_get_bucket),
        base_gcs_client_mock,
    )

    # Helper function to create a new blob
    def create_mock_blob(blob_name):
        """Creates a new mock blob with all required methods and attributes."""
        mock_blob = create_autospec(storage.Blob)
        mock_blob.name = blob_name
        mock_blob.exists.return_value = True
        mock_blob.size = len(file_content)

        # Configure download_as_bytes with proper method binding
        def mock_download_as_bytes(
            self, client=None, start=None, end=None, raw_download=False, **kwargs
        ):
            """Mock implementation of download_as_bytes method.
            Cannot use autospec because it is bound to the mock_blob instance.
            """
            return file_content

        mock_blob.download_as_bytes = types.MethodType(
            mock_download_as_bytes, mock_blob
        )

        def mock_download_to_file(self, fileobj, *args, **kwargs):
            """Mock implementation of download_to_file method.
            Cannot use autospec because it is bound to the mock_blob instance.
            """
            fileobj.write(file_content)
            fileobj.seek(0)
            return None

        mock_blob.download_to_file = types.MethodType(mock_download_to_file, mock_blob)

        def mock_upload_from_file(
            self,
            file_obj,
            content_type=None,
            num_retries=None,
            client=None,
            size=None,
            **kwargs,
        ):
            """Simulates uploading a file to the blob, storing it in the blobs dictionary."""
            blobs[blob_name] = self
            return None

        def mock_generate_signed_url(self, version, expiration, method, **kwargs):
            """Generates a signed URL for the blob, raising NotFound if the blob doesn't exist."""
            if blob_name not in blobs:
                raise NotFound(f"Blob {blob_name} not found")
            return f"https://storage.googleapis.com/{mock_bucket.name}/{blob_name}"

        def mock_delete(self):
            """Deletes the blob from the blobs dictionary."""
            if blob_name in blobs:
                del blobs[blob_name]
            return None

        def mock_reload(self):
            """Simulates reloading the blob's metadata, raising NotFound if the blob doesn't exist."""
            if blob_name not in blobs:
                raise NotFound(f"Blob {blob_name} not found")
            return None

        # Create properly autospecced methods with side effects
        mock_blob.upload_from_file = types.MethodType(
            create_autospec(
                storage.Blob.upload_from_file, side_effect=mock_upload_from_file
            ),
            mock_blob,
        )
        mock_blob.generate_signed_url = types.MethodType(
            create_autospec(
                storage.Blob.generate_signed_url, side_effect=mock_generate_signed_url
            ),
            mock_blob,
        )
        mock_blob.delete = types.MethodType(
            create_autospec(storage.Blob.delete, side_effect=mock_delete), mock_blob
        )
        mock_blob.reload = types.MethodType(
            create_autospec(storage.Blob.reload, side_effect=mock_reload), mock_blob
        )
        return mock_blob

    # Override the bucket's blob method to use our blob creation
    def mock_create_blob(self, blob_name, *args, **kwargs):
        """Creates a new blob in the bucket using the create_mock_blob helper."""
        return create_mock_blob(blob_name)

    mock_bucket.blob = types.MethodType(
        create_autospec(storage.Bucket.blob, side_effect=mock_create_blob), mock_bucket
    )

    return base_gcs_client_mock

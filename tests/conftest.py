import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable
from uuid import uuid4

import pytest
import requests
import yaml
from fastapi.testclient import TestClient
from fideslang import DEFAULT_TAXONOMY, models
from httpx import AsyncClient
from loguru import logger
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
    JWE_PAYLOAD_SYSTEMS,
)
from fides.api.db.ctl_session import sync_engine
from fides.api.main import app
from fides.api.models.privacy_request import generate_request_callback_jwe
from fides.api.models.sql_models import Cookies, DataUse, PrivacyDeclaration
from fides.api.oauth.jwt import generate_jwe
from fides.api.oauth.roles import (
    APPROVER,
    CONTRIBUTOR,
    OWNER,
    VIEWER,
    VIEWER_AND_APPROVER,
)
from fides.api.schemas.messaging.messaging import MessagingServiceType
from fides.api.util.cache import get_cache
from fides.common.api.scope_registry import SCOPE_REGISTRY
from fides.config import get_config
from fides.config.config_proxy import ConfigProxy
from tests.fixtures.application_fixtures import *
from tests.fixtures.bigquery_fixtures import *
from tests.fixtures.dynamodb_fixtures import *
from tests.fixtures.email_fixtures import *
from tests.fixtures.fides_connector_example_fixtures import *
from tests.fixtures.integration_fixtures import *
from tests.fixtures.manual_fixtures import *
from tests.fixtures.manual_webhook_fixtures import *
from tests.fixtures.mariadb_fixtures import *
from tests.fixtures.mongodb_fixtures import *
from tests.fixtures.mssql_fixtures import *
from tests.fixtures.mysql_fixtures import *
from tests.fixtures.postgres_fixtures import *
from tests.fixtures.redshift_fixtures import *
from tests.fixtures.saas import *
from tests.fixtures.saas_erasure_order_fixtures import *
from tests.fixtures.saas_example_fixtures import *
from tests.fixtures.snowflake_fixtures import *
from tests.fixtures.timescale_fixtures import *

ROOT_PATH = Path().absolute()
CONFIG = get_config()
TEST_CONFIG_PATH = "tests/ctl/test_config.toml"
TEST_INVALID_CONFIG_PATH = "tests/ctl/test_invalid_config.toml"
TEST_DEPRECATED_CONFIG_PATH = "tests/ctl/test_deprecated_config.toml"


@pytest.fixture(scope="session")
def test_client():
    """Starlette test client fixture. Easier to use mocks with when testing out API calls"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
@pytest.mark.asyncio
async def async_session(test_client):
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


@pytest.fixture(scope="session", autouse=True)
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
            "first_name": "Test",
            "last_name": "User",
        },
    )
    oauth_client.user_id = user.id
    oauth_client.save(db=db)
    yield user


@pytest.fixture
def user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fidesops_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[APPROVER],
        scopes=[],
        user_id=user.id,
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [APPROVER]})

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


@pytest.fixture(autouse=True)
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
            organization_fides_key=1,
            fides_key="user.custom",
            parent_key="user",
            name="Custom Data Category",
            description="Custom Data Category",
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
                        ),
                        models.DatasetField(
                            name="Email",
                            description="User's Email",
                            path="another.another.path",
                            data_categories=["user.contact.email"],
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
            data_uses=models.PrivacyRule(matches="NONE", values=["essential.service"]),
            data_subjects=models.PrivacyRule(matches="ANY", values=[]),
        ),
        "system": models.System(
            organization_fides_key=1,
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
def generate_webhook_auth_header():
    def _build_jwt(webhook):
        jwe = generate_request_callback_jwe(webhook)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


@pytest.fixture(scope="session")
def integration_config():
    yield load_toml("tests/ops/integration_test_config.toml")


@pytest.fixture(scope="session")
def celery_config():
    return {"task_always_eager": False}


@pytest.fixture(autouse=True, scope="session")
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


@pytest.fixture(autouse=True, scope="session")
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


@pytest.fixture(autouse=True, scope="function")
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


@pytest.fixture(autouse=True, scope="function")
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


@pytest.fixture(autouse=True, scope="function")
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


@pytest.fixture(autouse=True, scope="function")
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


@pytest.fixture(scope="function", autouse=True)
def set_notification_service_type_mailgun(db):
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
def viewer_and_approver_user(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fides_viewer_and_approver_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
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

    Cookies.create(
        db=db,
        data={
            "name": "test_cookie",
            "path": "/",
            "privacy_declaration_id": privacy_declaration.id,
            "system_id": system.id,
        },
        check_name=False,
    )

    db.refresh(system)
    return system


@pytest.fixture(scope="function")
def system_multiple_decs(db: Session, system: System) -> System:
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
    return system


@pytest.fixture(scope="function")
def system_third_party_sharing(db: Session) -> System:
    system_third_party_sharing = System.create(
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
    return system_third_party_sharing


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


@pytest.fixture(scope="function", autouse=True)
def load_default_data_uses(db):
    for data_use in DEFAULT_TAXONOMY.data_use:
        # weirdly, only in some test scenarios, we already have the default taxonomy
        # loaded, in which case the create will throw an error. so we first check existence.
        if DataUse.get_by(db, field="name", value=data_use.name) is None:
            DataUse.create(db=db, data=data_use.dict())

# pylint: disable=unused-wildcard-import, wildcard-import

import asyncio
import json
from typing import Any, Callable, Dict, Generator, List

import pytest
import requests
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from toml import load as load_toml

from fides.api.main import app
from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY
from fides.api.ops.db.base import Base
from fides.api.ops.models.privacy_request import generate_request_callback_jwe
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.api.ops.util.cache import get_cache
from fides.core.api import db_action
from fides.core.config import get_config
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
)
from fides.lib.db.session import Session, get_db_engine, get_db_session
from fides.lib.models.client import ClientDetail
from fides.lib.oauth.jwt import generate_jwe
from fides.lib.oauth.roles import (
    PRIVACY_REQUEST_MANAGER,
    VIEWER_AND_PRIVACY_REQUEST_MANAGER,
)
from tests.conftest import create_citext_extension

from .fixtures.application_fixtures import *
from .fixtures.bigquery_fixtures import *
from .fixtures.email_fixtures import *
from .fixtures.fides_connector_example_fixtures import *
from .fixtures.integration_fixtures import *
from .fixtures.manual_fixtures import *
from .fixtures.manual_webhook_fixtures import *
from .fixtures.mariadb_fixtures import *
from .fixtures.mongodb_fixtures import *
from .fixtures.mssql_fixtures import *
from .fixtures.mysql_fixtures import *
from .fixtures.postgres_fixtures import *
from .fixtures.redshift_fixtures import *
from .fixtures.saas import *
from .fixtures.saas_example_fixtures import *
from .fixtures.snowflake_fixtures import *
from .fixtures.timescale_fixtures import *

CONFIG = get_config()


@pytest.fixture(scope="session", autouse=True)
def setup_db(api_client):
    """Apply migrations at beginning and end of testing session"""
    assert CONFIG.test_mode
    assert requests.post != api_client.post
    yield api_client.post(url=f"{CONFIG.cli.server_url}/v1/admin/db/reset")


@pytest.fixture(scope="session")
def db(api_client) -> Generator:
    """Return a connection to the test DB"""
    # Create the test DB engine
    assert CONFIG.test_mode
    assert requests.post != api_client.post
    engine = get_db_engine(
        database_uri=CONFIG.database.sqlalchemy_test_database_uri,
    )

    create_citext_extension(engine)

    if not scheduler.running:
        scheduler.start()
    SessionLocal = get_db_session(CONFIG, engine=engine)
    the_session = SessionLocal()
    # Setup above...

    yield the_session
    # Teardown below...
    the_session.close()
    engine.dispose()


@pytest.fixture(autouse=True)
def clear_db_tables(db):
    """Clear data from tables between tests.

    If relationships are not set to cascade on delete they will fail with an
    IntegrityError if there are relationsips present. This function stores tables
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

    db.commit()  # make sure all transactions are closed before starting deletes
    delete_data(Base.metadata.sorted_tables)


@pytest.fixture(scope="session")
def cache() -> Generator:
    yield get_cache()


@pytest.fixture(scope="session")
def api_client() -> Generator:
    """Return a client used to make API requests"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
async def async_api_client() -> Generator:
    """Return an async client used to make API requests"""
    async with AsyncClient(
        app=app, base_url="http://0.0.0.0:8080", follow_redirects=True
    ) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def event_loop() -> Generator:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def oauth_client(db: Session) -> Generator:
    """Return a client for authentication purposes"""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=SCOPE_REGISTRY,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client


@pytest.fixture(scope="function")
def oauth_role_client(db: Session) -> Generator:
    """Return a client that has all the roles for authentication purposes"""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        roles=[
            ADMIN,
            PRIVACY_REQUEST_MANAGER,
            VIEWER,
            VIEWER_AND_PRIVACY_REQUEST_MANAGER,
        ],
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client


@pytest.fixture(scope="function")
def oauth_root_client(db: Session) -> ClientDetail:
    """Return the configured root client (never persisted)"""
    return ClientDetail.get(
        db,
        object_id=CONFIG.security.oauth_root_client_id,
        config=CONFIG,
        scopes=SCOPE_REGISTRY,
    )


@pytest.fixture(scope="function")
def root_auth_header(oauth_root_client: ClientDetail) -> Dict[str, str]:
    """Return an auth header for the root client"""
    payload = {
        JWE_PAYLOAD_SCOPES: oauth_root_client.scopes,
        JWE_PAYLOAD_CLIENT_ID: oauth_root_client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


def generate_auth_header_for_user(user, scopes) -> Dict[str, str]:
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


def generate_role_header_for_user(user, roles) -> Dict[str, str]:
    payload = {
        JWE_PAYLOAD_ROLES: roles,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


@pytest.fixture(scope="function")
def generate_auth_header(oauth_client) -> Callable[[Any], Dict[str, str]]:
    return _generate_auth_header(oauth_client, CONFIG.security.app_encryption_key)


@pytest.fixture(scope="function")
def generate_role_header(oauth_role_client) -> Callable[[Any], Dict[str, str]]:
    return _generate_auth_role_header(
        oauth_role_client, CONFIG.security.app_encryption_key
    )


@pytest.fixture
def generate_auth_header_ctl_config(oauth_client) -> Callable[[Any], Dict[str, str]]:
    return _generate_auth_header(oauth_client, CONFIG.security.app_encryption_key)


def _generate_auth_header(
    oauth_client, app_encryption_key
) -> Callable[[Any], Dict[str, str]]:
    client_id = oauth_client.id

    def _build_jwt(scopes: List[str]) -> Dict[str, str]:
        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), app_encryption_key)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


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
def generate_webhook_auth_header() -> Callable[[Any], Dict[str, str]]:
    def _build_jwt(webhook: PolicyPreWebhook) -> Dict[str, str]:
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
        "fides.api.ops.service.privacy_request.request_runner_service.run_privacy_request"
    ]


@pytest.fixture(autouse=True, scope="session")
def analytics_opt_out():
    """Disable sending analytics when running tests."""
    original_value = CONFIG.user.analytics_opt_out
    CONFIG.user.analytics_opt_out = True
    yield
    CONFIG.user.analytics_opt_out = original_value


@pytest.fixture(scope="function")
def require_manual_request_approval():
    """Require manual request approval"""
    original_value = CONFIG.execution.require_manual_request_approval
    CONFIG.execution.require_manual_request_approval = True
    yield
    CONFIG.execution.require_manual_request_approval = original_value


@pytest.fixture(scope="function")
def subject_identity_verification_required():
    """Enable identity verification."""
    original_value = CONFIG.execution.subject_identity_verification_required
    CONFIG.execution.subject_identity_verification_required = True
    yield
    CONFIG.execution.subject_identity_verification_required = original_value


@pytest.fixture(autouse=True, scope="function")
def subject_identity_verification_not_required():
    """Disable identity verification for most tests unless overridden"""
    original_value = CONFIG.execution.subject_identity_verification_required
    CONFIG.execution.subject_identity_verification_required = False
    yield
    CONFIG.execution.subject_identity_verification_required = original_value


@pytest.fixture(autouse=True, scope="function")
def privacy_request_complete_email_notification_disabled():
    """Disable request completion email for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_completion_notification
    CONFIG.notifications.send_request_completion_notification = False
    yield
    CONFIG.notifications.send_request_completion_notification = original_value


@pytest.fixture(autouse=True, scope="function")
def privacy_request_receipt_notification_disabled():
    """Disable request receipt notification for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_receipt_notification
    CONFIG.notifications.send_request_receipt_notification = False
    yield
    CONFIG.notifications.send_request_receipt_notification = original_value


@pytest.fixture(autouse=True, scope="function")
def privacy_request_review_notification_disabled():
    """Disable request review notification for most tests unless overridden"""
    original_value = CONFIG.notifications.send_request_review_notification
    CONFIG.notifications.send_request_review_notification = False
    yield
    CONFIG.notifications.send_request_review_notification = original_value


@pytest.fixture(scope="function", autouse=True)
def set_notification_service_type_mailgun():
    """Set default notification service type"""
    original_value = CONFIG.notifications.notification_service_type
    CONFIG.notifications.notification_service_type = MessagingServiceType.MAILGUN.value
    yield
    CONFIG.notifications.notification_service_type = original_value

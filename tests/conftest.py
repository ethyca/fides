# pylint: disable=unused-wildcard-import, wildcard-import

import json
import logging
from typing import Any, Callable, Dict, Generator, List

import pytest
from fastapi.testclient import TestClient
from fideslib.core.config import load_toml
from fideslib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fideslib.db.session import Session, get_db_engine, get_db_session
from fideslib.models.client import ClientDetail
from fideslib.oauth.jwt import generate_jwe
from sqlalchemy.exc import IntegrityError
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from fidesops.api.v1.scope_registry import SCOPE_REGISTRY
from fidesops.core.config import config
from fidesops.db.base import Base
from fidesops.db.database import init_db
from fidesops.main import app
from fidesops.models.privacy_request import generate_request_callback_jwe
from fidesops.tasks.scheduled.scheduler import scheduler
from fidesops.util.cache import get_cache

from .fixtures.application_fixtures import *
from .fixtures.bigquery_fixtures import *
from .fixtures.integration_fixtures import *
from .fixtures.manual_fixtures import *
from .fixtures.mariadb_fixtures import *
from .fixtures.mongodb_fixtures import *
from .fixtures.mssql_fixtures import *
from .fixtures.mysql_fixtures import *
from .fixtures.postgres_fixtures import *
from .fixtures.redshift_fixtures import *
from .fixtures.saas.hubspot_fixtures import *
from .fixtures.saas.mailchimp_fixtures import *
from .fixtures.saas.outreach_fixtures import *
from .fixtures.saas.salesforce_fixtures import *
from .fixtures.saas.segment_fixtures import *
from .fixtures.saas.sentry_fixtures import *
from .fixtures.saas.stripe_fixtures import *
from .fixtures.saas.zendesk_fixtures import *
from .fixtures.saas_example_fixtures import *
from .fixtures.snowflake_fixtures import *

logger = logging.getLogger(__name__)


def migrate_test_db() -> None:
    """Apply migrations at beginning and end of testing session"""
    logger.debug("Applying migrations...")
    assert config.is_test_mode
    if config.database.enabled:
        init_db(config.database.sqlalchemy_test_database_uri)
    logger.debug("Migrations successfully applied")


@pytest.fixture(scope="session")
def db() -> Generator:
    """Return a connection to the test DB"""
    # Create the test DB enginge
    assert config.is_test_mode
    engine = get_db_engine(
        database_uri=config.database.sqlalchemy_test_database_uri,
    )

    logger.debug(f"Configuring database at: {engine.url}")
    if not database_exists(engine.url):
        logger.debug(f"Creating database at: {engine.url}")
        create_database(engine.url)
        logger.debug(f"Database at: {engine.url} successfully created")
    else:
        logger.debug(f"Database at: {engine.url} already exists")

    migrate_test_db()
    scheduler.start()
    SessionLocal = get_db_session(config, engine=engine)
    the_session = SessionLocal()
    # Setup above...
    yield the_session
    # Teardown below...
    the_session.close()
    engine.dispose()
    logger.debug(f"Dropping database at: {engine.url}")
    # We don't need to perform any extra checks before dropping the DB
    # here since we know the engine will always be connected to the test DB
    drop_database(engine.url)
    logger.debug(f"Database at: {engine.url} successfully dropped")


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


@pytest.fixture(scope="module")
def api_client() -> Generator:
    """Return a client used to make API requests"""
    with TestClient(app) as c:
        yield c


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


def generate_auth_header_for_user(user, scopes) -> Dict[str, str]:
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), config.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


@pytest.fixture(scope="function")
def generate_auth_header(oauth_client) -> Callable[[Any], Dict[str, str]]:
    return _generate_auth_header(oauth_client)


def _generate_auth_header(oauth_client) -> Callable[[Any], Dict[str, str]]:
    client_id = oauth_client.id

    def _build_jwt(scopes: List[str]) -> Dict[str, str]:
        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), config.security.app_encryption_key)
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
    yield load_toml(["fidesops-integration.toml"])


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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request"
    ]


@pytest.fixture(autouse=True, scope="session")
def analytics_opt_out():
    """Disable sending analytics when running tests."""
    original_value = config.root_user.analytics_opt_out
    config.root_user.analytics_opt_out = True
    yield
    config.root_user.analytics_opt_out = original_value

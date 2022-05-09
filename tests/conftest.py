import json
import logging
import pytest

from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy_utils.functions import (
    create_database,
    database_exists,
    drop_database,
)

from fidesops.core.config import (
    config,
)
from fidesops.db.database import init_db
from fidesops.db.session import get_db_session, get_db_engine, Session
from fidesops.main import app
from fidesops.models.privacy_request import generate_request_callback_jwe
from fidesops.schemas.jwt import (
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
    JWE_ISSUED_AT,
)
from fidesops.api.v1.scope_registry import SCOPE_REGISTRY
from fidesops.tasks.scheduled.scheduler import scheduler
from fidesops.util.cache import get_cache
from fidesops.util.oauth_util import generate_jwe

from .fixtures.application_fixtures import *
from .fixtures.integration_fixtures import *
from .fixtures.mariadb_fixtures import *
from .fixtures.mongodb_fixtures import *
from .fixtures.mysql_fixtures import *
from .fixtures.mssql_fixtures import *
from .fixtures.postgres_fixtures import *
from .fixtures.redshift_fixtures import *
from .fixtures.snowflake_fixtures import *
from .fixtures.bigquery_fixtures import *
from .fixtures.saas_example_fixtures import *
from .fixtures.saas.mailchimp_fixtures import *
from .fixtures.saas.sentry_fixtures import *
from .fixtures.saas.stripe_fixtures import *
from .fixtures.saas.hubspot_fixtures import *
from .fixtures.saas.segment_fixtures import *

logger = logging.getLogger(__name__)


def migrate_test_db() -> None:
    """Apply migrations at beginning and end of testing session"""
    logger.debug("Applying migrations...")
    assert config.is_test_mode
    init_db(config.database.SQLALCHEMY_TEST_DATABASE_URI)
    logger.debug("Migrations successfully applied")


@pytest.fixture(scope="session")
def db() -> Generator:
    """Return a connection to the test DB"""
    # Create the test DB enginge
    assert config.is_test_mode
    engine = get_db_engine(
        database_uri=config.database.SQLALCHEMY_TEST_DATABASE_URI,
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
    SessionLocal = get_db_session(engine=engine)
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
    client.delete(db)


def generate_auth_header_for_user(user, scopes):
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload))
    return {"Authorization": "Bearer " + jwe}


@pytest.fixture(scope="function")
def generate_auth_header(oauth_client):
    return _generate_auth_header(oauth_client)


def _generate_auth_header(oauth_client):
    client_id = oauth_client.id

    def _build_jwt(scopes: List[str]):
        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload))
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


@pytest.fixture(scope="function")
def generate_webhook_auth_header():
    def _build_jwt(webhook: PolicyPreWebhook):
        jwe = generate_request_callback_jwe(webhook)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


@pytest.fixture(scope="session")
def integration_config():
    yield load_toml("fidesops-integration.toml")

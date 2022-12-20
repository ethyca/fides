# pylint: disable=missing-function-docstring, redefined-outer-name

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from sqlalchemy_utils.functions import create_database, database_exists
from starlette.testclient import TestClient

from fides.ctl.core.config import get_config
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.lib.db.base import Base  # type: ignore[attr-defined]
from fides.lib.db.session import get_db_engine, get_db_session
from fides.lib.models.client import ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions
from fides.lib.oauth.api.routes.user_endpoints import router
from fides.lib.oauth.jwt import generate_jwe
from fides.lib.oauth.scopes import PRIVACY_REQUEST_READ, SCOPES

logger = logging.getLogger(__name__)

ROOT_PATH = Path().absolute()


@pytest.fixture(scope="session")
def config():
    config = get_config()
    config.is_test_mode = True
    yield config


@pytest.fixture
def db(config):
    """Yield a connection to the test DB."""
    # Included so that `AccessManualWebhook` can be located when
    # `ConnectionConfig` is instantiated.
    from fides.api.ops.models.manual_webhook import (  # pylint: disable=unused-import
        AccessManualWebhook,
    )

    # Create the test DB engine
    assert config.is_test_mode
    engine = get_db_engine(
        database_uri=config.database.sqlalchemy_database_uri,
    )

    if not database_exists(engine.url):
        logger.debug("Creating database at: %s", engine.url)
        create_database(engine.url)

    # Create the database tables
    Base.metadata.create_all(engine)

    SessionLocal = get_db_session(config, engine=engine)
    session = SessionLocal()
    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

    engine.dispose()


@pytest.fixture(autouse=True, scope="session")
def env_vars():
    os.environ["TESTING"] = "True"


@pytest.fixture(scope="session")
def client():
    """Starlette test client to use in testing API routes."""
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def fides_toml_path():
    yield ROOT_PATH / ".fides" / "fides.toml"


@pytest.fixture
def oauth_client(db):
    """Return a client for authentication purposes."""
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=SCOPES,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    yield client
    client.delete(db)


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
        scopes=SCOPES,
        user_id=user.id,
    )

    FidesUserPermissions.create(
        db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
    )

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user


@pytest.fixture(scope="function")
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

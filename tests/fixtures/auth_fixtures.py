import json
from datetime import datetime
from typing import Any, Callable, Dict, Generator
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.privacy_request import (
    generate_request_callback_pre_approval_jwe,
    generate_request_callback_resume_jwe,
)
from fides.api.oauth.jwt import generate_jwe
from fides.api.oauth.roles import (
    APPROVER,
    CONTRIBUTOR,
    OWNER,
    VIEWER,
    VIEWER_AND_APPROVER,
)
from fides.common.scope_registry import SCOPE_REGISTRY
from fides.config import get_config
from tests.helpers.auth import (
    _generate_auth_header,
    _generate_auth_role_header,
    _generate_system_manager_header,
)

CONFIG = get_config()


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


@pytest.fixture
def generate_auth_header(oauth_client):
    return _generate_auth_header(oauth_client, CONFIG.security.app_encryption_key)


@pytest.fixture
def generate_auth_header_ctl_config(oauth_client):
    return _generate_auth_header(oauth_client, CONFIG.security.app_encryption_key)


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


@pytest.fixture(scope="function")
def generate_role_header(oauth_role_client) -> Callable[[Any], Dict[str, str]]:
    return _generate_auth_role_header(
        oauth_role_client, CONFIG.security.app_encryption_key
    )


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

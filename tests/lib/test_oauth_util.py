# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name

import json
from datetime import datetime

import pytest
from fastapi.security import SecurityScopes

from fides.api.ops.api.v1.scope_registry import PRIVACY_REQUEST_READ
from fides.api.ops.util.oauth_util import (
    _has_correct_scopes,
    _has_direct_scopes,
    _has_scope_via_role,
    get_root_client,
    has_permissions,
    verify_oauth_client,
)
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
)
from fides.lib.exceptions import AuthorizationError
from fides.lib.oauth.jwt import generate_jwe
from fides.lib.oauth.oauth_util import extract_payload, is_token_expired
from fides.lib.oauth.roles import ADMIN, VIEWER
from fides.lib.oauth.scopes import DATASET_CREATE_OR_UPDATE, USER_DELETE, USER_READ


@pytest.fixture
def encryption_key():
    yield "d9a74e98829dbf57c4ca36e1788a48d2"


def test_jwe_create_and_extract(encryption_key) -> None:
    payload = {"hello": "hi there"}
    jwe_string = generate_jwe(json.dumps(payload), encryption_key)
    payload_from_svc = json.loads(extract_payload(jwe_string, encryption_key))
    assert payload_from_svc["hello"] == payload["hello"]


@pytest.mark.parametrize(
    "issued_at, token_duration_min, expected",
    [
        (datetime(2020, 1, 1), 1, True),
        (datetime.now(), 60, False),
        (None, 60, True),
    ],
)
def test_is_token_expired(issued_at, token_duration_min, expected):
    assert is_token_expired(issued_at, token_duration_min) is expected


async def test_verify_oauth_malformed_oauth_client(db):
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes([USER_READ]),
            authorization="invalid",
            db=db,
        )


async def test_verify_oauth_client_no_issued_at(db, config, user):
    payload = {
        JWE_PAYLOAD_SCOPES: [USER_READ],
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: None,
        "token_duration_min": 1,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes([USER_READ]),
            token,
            db=db,
        )


async def test_verify_oauth_client_expired(db, config, user):
    scope = [USER_READ]
    payload = {
        JWE_PAYLOAD_SCOPES: scope,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime(2020, 1, 1).isoformat(),
        "token_duration_min": 1,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes(scope),
            token,
            db=db,
        )


async def test_verify_oauth_client_no_client_id(db, config):
    scope = [USER_READ]
    payload = {
        JWE_PAYLOAD_SCOPES: scope,
        JWE_PAYLOAD_CLIENT_ID: None,
        JWE_ISSUED_AT: datetime.now().isoformat(),
        "token_duration_min": 60,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes(scope),
            token,
            db=db,
        )


async def test_verify_oauth_client_no_client(db, config, user):
    scopes = [USER_READ]
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
        "token_duration_min": 60,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    user.client.delete(db)
    assert user.client is None
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes(scopes),
            token,
            db=db,
        )


async def test_verify_oauth_client_wrong_security_scope(db, config, user):
    payload = {
        JWE_PAYLOAD_SCOPES: [USER_DELETE],
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
        "token_duration_min": 60,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes([USER_READ]),
            token,
            db=db,
        )


async def test_verify_oauth_client_wrong_client_scope(db, config, user):
    scopes = [USER_READ]
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
        "token_duration_min": 60,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    user.client.scopes = [USER_DELETE]
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes(scopes),
            token,
            db=db,
        )


class TestVerifyOauthClientRoles:
    async def test_verify_oauth_client_roles(self, db, config, admin_user):
        """Test token has the correct role and the client also has the matching role"""
        payload = {
            JWE_PAYLOAD_ROLES: [ADMIN],
            JWE_PAYLOAD_CLIENT_ID: admin_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        client = await verify_oauth_client(
            SecurityScopes([USER_READ]),
            token,
            db=db,
        )
        assert client == admin_user.client

    async def test_no_roles_on_client(self, db, config, user):
        """Test token has the correct role but that role is not on the client"""
        payload = {
            JWE_PAYLOAD_ROLES: [ADMIN],
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        with pytest.raises(AuthorizationError):
            await verify_oauth_client(
                SecurityScopes([USER_READ]),
                token,
                db=db,
            )

    async def test_no_roles_on_client_but_has_scopes_coverage(self, db, config, user):
        """Test roles on token are outdated but token still has scopes coverage"""
        payload = {
            JWE_PAYLOAD_ROLES: [ADMIN],
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SCOPES: [USER_READ],
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        client = await verify_oauth_client(
            SecurityScopes([USER_READ]),
            token,
            db=db,
        )
        assert client == user.client

    async def test_token_does_not_have_role_with_coverage(
        self, db, config, viewer_user
    ):
        """Test token only has a viewer role, which is not enough to view the particular endpoint
        as it is missing DATASET_CREATE_OR_UPDATE scopes
        """
        payload = {
            JWE_PAYLOAD_ROLES: [VIEWER],
            JWE_PAYLOAD_CLIENT_ID: viewer_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SCOPES: [USER_READ],
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )

        with pytest.raises(AuthorizationError):
            await verify_oauth_client(
                SecurityScopes([DATASET_CREATE_OR_UPDATE]),
                token,
                db=db,
            )


class TestHasCorrectScopes:
    def test_missing_scopes(self):
        assert not _has_correct_scopes(
            user_scopes=[DATASET_CREATE_OR_UPDATE, USER_READ],
            endpoint_scopes=SecurityScopes([PRIVACY_REQUEST_READ]),
        )

    def test_has_correct_scopes(self):
        assert _has_correct_scopes(
            user_scopes=[DATASET_CREATE_OR_UPDATE, USER_READ, PRIVACY_REQUEST_READ],
            endpoint_scopes=SecurityScopes([PRIVACY_REQUEST_READ]),
        )


class TestHasDirectScopes:
    def test_token_does_not_have_any_scopes(self, viewer_client):
        assert not _has_direct_scopes(
            token_data={},
            client=viewer_client,
            endpoint_scopes=SecurityScopes([PRIVACY_REQUEST_READ]),
        )

    def test_missing_scopes(self, oauth_client):
        token_data = {
            JWE_PAYLOAD_SCOPES: [DATASET_CREATE_OR_UPDATE, USER_READ],
        }
        assert not _has_direct_scopes(
            token_data=token_data,
            client=oauth_client,
            endpoint_scopes=SecurityScopes([PRIVACY_REQUEST_READ]),
        )

    def test_has_direct_scopes_but_client_outdated(self, viewer_client):
        token_data = {
            JWE_PAYLOAD_SCOPES: [
                DATASET_CREATE_OR_UPDATE,
                USER_READ,
                PRIVACY_REQUEST_READ,
            ],
        }
        assert not _has_direct_scopes(
            token_data=token_data,
            client=viewer_client,
            endpoint_scopes=SecurityScopes([PRIVACY_REQUEST_READ]),
        )

    def test_has_direct_scopes_and_token_valid(self, oauth_client):
        token_data = {
            JWE_PAYLOAD_SCOPES: [
                DATASET_CREATE_OR_UPDATE,
                USER_READ,
                PRIVACY_REQUEST_READ,
            ],
        }
        assert _has_direct_scopes(
            token_data=token_data,
            client=oauth_client,
            endpoint_scopes=SecurityScopes([PRIVACY_REQUEST_READ]),
        )


class TestHasScopeViaRole:
    def test_token_does_not_have_any_roles(self, viewer_client):
        assert not _has_scope_via_role(
            token_data={},
            client=viewer_client,
            endpoint_scopes=SecurityScopes([PRIVACY_REQUEST_READ]),
        )

    def test_inadequate_roles(self, viewer_client):
        token_data = {
            JWE_PAYLOAD_ROLES: [VIEWER],
        }
        assert not _has_scope_via_role(
            token_data=token_data,
            client=viewer_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    def test_has_adequate_role_but_client_outdated(self, viewer_client):
        token_data = {
            JWE_PAYLOAD_ROLES: [ADMIN],
        }
        assert not _has_scope_via_role(
            token_data=token_data,
            client=viewer_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    def test_has_adequate_role_and_token_valid(self, admin_client):
        token_data = {
            JWE_PAYLOAD_ROLES: [ADMIN],
        }
        assert _has_scope_via_role(
            token_data=token_data,
            client=admin_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )


class TestHasPermissions:
    def test_has_no_permissions(self, oauth_client):
        token_data = {}
        assert not has_permissions(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    def test_has_direct_scope(self, oauth_client):
        token_data = {
            JWE_PAYLOAD_SCOPES: [DATASET_CREATE_OR_UPDATE, USER_READ],
        }
        assert _has_direct_scopes(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )
        assert not _has_scope_via_role(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )
        assert has_permissions(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    def test_has_scope_via_role(self, admin_client):
        token_data = {
            JWE_PAYLOAD_ROLES: [ADMIN],
        }
        assert not _has_direct_scopes(
            token_data,
            admin_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )
        assert _has_scope_via_role(
            token_data,
            admin_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

        assert has_permissions(
            token_data,
            admin_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    async def test_has_scope_directly_and_via_role(self):
        root_client = await get_root_client()
        token_data = {
            JWE_PAYLOAD_ROLES: [ADMIN],
            JWE_PAYLOAD_SCOPES: [DATASET_CREATE_OR_UPDATE, USER_READ],
        }
        assert _has_direct_scopes(
            token_data,
            root_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )
        assert _has_scope_via_role(
            token_data,
            root_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

        assert has_permissions(
            token_data,
            root_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    async def test_has_no_direct_scopes_or_via_role(self):
        root_client = await get_root_client()
        token_data = {
            JWE_PAYLOAD_ROLES: [VIEWER],
            JWE_PAYLOAD_SCOPES: [USER_READ],
        }
        assert not _has_direct_scopes(
            token_data,
            root_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )
        assert not _has_scope_via_role(
            token_data,
            root_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

        assert not has_permissions(
            token_data,
            root_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name

import json
from datetime import datetime

import pytest
from fastapi.security import SecurityScopes

from fides.api.common_exceptions import AuthorizationError
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
)
from fides.api.models.client import ClientDetail
from fides.api.oauth.jwt import generate_jwe
from fides.api.oauth.roles import (
    APPROVER,
    CONTRIBUTOR,
    OWNER,
    ROLES_TO_SCOPES_MAPPING,
    VIEWER,
    VIEWER_AND_APPROVER,
    not_contributor_scopes,
)
from fides.api.oauth.utils import (
    _has_direct_scopes,
    _has_scope_via_role,
    default_has_permissions,
    default_has_permissions_async,
    extract_payload,
    get_async_permission_checker,
    get_permission_checker,
    get_root_client,
    has_permissions,
    has_scope_subset,
    is_token_expired,
    verify_oauth_client,
    verify_oauth_client_async,
)
from fides.common.api.scope_registry import (
    DATASET_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
    SCOPE_REGISTRY,
    USER_DELETE,
    USER_PERMISSION_READ,
    USER_READ,
)
from fides.config import CONFIG


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
    async def test_token_does_not_have_roles(self, db, config):
        """Test that roles aren't required to be on the token - scopes can still be assigned directly"""
        client, _ = ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=[PRIVACY_REQUEST_REVIEW],
            user_id=None,
        )

        payload = {
            JWE_PAYLOAD_SCOPES: [PRIVACY_REQUEST_REVIEW],
            JWE_PAYLOAD_CLIENT_ID: client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        verified_client = await verify_oauth_client(
            SecurityScopes([PRIVACY_REQUEST_REVIEW]),
            token,
            db=db,
        )
        assert client == verified_client

    async def test_verify_oauth_client_roles(self, db, config, owner_user):
        """Test token has a valid role and the client also has the matching role
        Scopes aren't directly assigned but the user inherits the USER_READ scope
        via the OWNER role.
        """
        payload = {
            JWE_PAYLOAD_ROLES: [OWNER],
            JWE_PAYLOAD_CLIENT_ID: owner_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        client = await verify_oauth_client(
            SecurityScopes([PRIVACY_REQUEST_REVIEW]),
            token,
            db=db,
        )
        assert client == owner_user.client

    async def test_no_roles_on_client(self, db, config, user):
        """Test token has a role with the correct scopes but that role is not on the client"""
        payload = {
            JWE_PAYLOAD_ROLES: [OWNER],
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        with pytest.raises(AuthorizationError):
            await verify_oauth_client(
                SecurityScopes([PRIVACY_REQUEST_REVIEW]),
                token,
                db=db,
            )

    async def test_no_roles_on_client_but_has_scopes_coverage(self, db, config, user):
        """Test roles on token are outdated but token still has scopes coverage"""
        user.client.scopes = [PRIVACY_REQUEST_REVIEW]
        user.client.save(db)
        payload = {
            JWE_PAYLOAD_ROLES: [OWNER],
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SCOPES: [PRIVACY_REQUEST_REVIEW],
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        client = await verify_oauth_client(
            SecurityScopes([PRIVACY_REQUEST_REVIEW]),
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
        assert not has_scope_subset(
            user_scopes=[DATASET_CREATE_OR_UPDATE, USER_READ],
            endpoint_scopes=SecurityScopes([PRIVACY_REQUEST_READ]),
        )

    def test_has_correct_scopes(self):
        assert has_scope_subset(
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
            JWE_PAYLOAD_ROLES: [OWNER],
        }
        assert not _has_scope_via_role(
            token_data=token_data,
            client=viewer_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    def test_has_adequate_role_and_token_valid(self, owner_client):
        token_data = {
            JWE_PAYLOAD_ROLES: [OWNER],
        }
        assert _has_scope_via_role(
            token_data=token_data,
            client=owner_client,
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

    def test_has_scope_via_role(self, owner_client):
        token_data = {
            JWE_PAYLOAD_ROLES: [OWNER],
        }
        assert not _has_direct_scopes(
            token_data,
            owner_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )
        assert _has_scope_via_role(
            token_data,
            owner_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

        assert has_permissions(
            token_data,
            owner_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    async def test_has_scope_directly_and_via_role(self):
        root_client = await get_root_client()
        token_data = {
            JWE_PAYLOAD_ROLES: [OWNER],
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


class TestRolesToScopesMapping:
    def test_contributor_role(self):
        for scope in not_contributor_scopes:  # Sanity check
            assert not scope in ROLES_TO_SCOPES_MAPPING[CONTRIBUTOR]

    def test_owner_role(self):
        assert set(SCOPE_REGISTRY) == set(ROLES_TO_SCOPES_MAPPING[OWNER])

    def test_viewer_role(self):
        assert USER_PERMISSION_READ not in ROLES_TO_SCOPES_MAPPING[VIEWER]
        for scope in ROLES_TO_SCOPES_MAPPING[VIEWER]:
            assert not "create" in scope
            assert not "update" in scope
            assert not "delete" in scope

    def test_approver_roles(self):
        approver_scopes = set(ROLES_TO_SCOPES_MAPPING[APPROVER])
        viewer_and_approver_scopes = set(ROLES_TO_SCOPES_MAPPING[VIEWER_AND_APPROVER])
        assert approver_scopes.issubset(viewer_and_approver_scopes)
        assert not viewer_and_approver_scopes.issubset(approver_scopes)
        # Verify approver role includes privacy request create scope (added in September 2025)
        assert "privacy-request:create" in ROLES_TO_SCOPES_MAPPING[APPROVER]


# Tests for verify_oauth_client_async (async version using AsyncSession)
class TestVerifyOauthClientAsync:
    """Tests for the async version of verify_oauth_client that uses AsyncSession."""

    async def test_verify_oauth_async_malformed_oauth_client(self, async_session):
        with pytest.raises(AuthorizationError):
            await verify_oauth_client_async(
                SecurityScopes([USER_READ]),
                authorization="invalid",
                db=async_session,
            )

    async def test_verify_oauth_client_async_no_issued_at(
        self, async_session, config, user
    ):
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
            await verify_oauth_client_async(
                SecurityScopes([USER_READ]),
                token,
                db=async_session,
            )

    async def test_verify_oauth_client_async_expired(self, async_session, config, user):
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
            await verify_oauth_client_async(
                SecurityScopes(scope),
                token,
                db=async_session,
            )

    async def test_verify_oauth_client_async_no_client_id(self, async_session, config):
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
            await verify_oauth_client_async(
                SecurityScopes(scope),
                token,
                db=async_session,
            )

    async def test_verify_oauth_client_async_no_client(
        self, db, async_session, config, user
    ):
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
            await verify_oauth_client_async(
                SecurityScopes(scopes),
                token,
                db=async_session,
            )

    async def test_verify_oauth_client_async_wrong_security_scope(
        self, async_session, config, user
    ):
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
            await verify_oauth_client_async(
                SecurityScopes([USER_READ]),
                token,
                db=async_session,
            )

    async def test_verify_oauth_client_async_wrong_client_scope(
        self, async_session, config, user
    ):
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
            await verify_oauth_client_async(
                SecurityScopes(scopes),
                token,
                db=async_session,
            )


class TestVerifyOauthClientAsyncRoles:
    """Tests for verify_oauth_client_async with role-based authentication."""

    async def test_token_does_not_have_roles(self, db, async_session, config):
        """Test that roles aren't required to be on the token - scopes can still be assigned directly"""
        client, _ = ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=[PRIVACY_REQUEST_REVIEW],
            user_id=None,
        )

        payload = {
            JWE_PAYLOAD_SCOPES: [PRIVACY_REQUEST_REVIEW],
            JWE_PAYLOAD_CLIENT_ID: client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        verified_client = await verify_oauth_client_async(
            SecurityScopes([PRIVACY_REQUEST_REVIEW]),
            token,
            db=async_session,
        )
        assert client.id == verified_client.id

    async def test_verify_oauth_client_async_roles(
        self, async_session, config, owner_user
    ):
        """Test token has a valid role and the client also has the matching role
        Scopes aren't directly assigned but the user inherits the USER_READ scope
        via the OWNER role.
        """
        payload = {
            JWE_PAYLOAD_ROLES: [OWNER],
            JWE_PAYLOAD_CLIENT_ID: owner_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        client = await verify_oauth_client_async(
            SecurityScopes([PRIVACY_REQUEST_REVIEW]),
            token,
            db=async_session,
        )
        assert client.id == owner_user.client.id

    async def test_no_roles_on_client(self, async_session, config, user):
        """Test token has a role with the correct scopes but that role is not on the client"""
        payload = {
            JWE_PAYLOAD_ROLES: [OWNER],
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        with pytest.raises(AuthorizationError):
            await verify_oauth_client_async(
                SecurityScopes([PRIVACY_REQUEST_REVIEW]),
                token,
                db=async_session,
            )

    async def test_no_roles_on_client_but_has_scopes_coverage(
        self, db, async_session, config, user
    ):
        """Test roles on token are outdated but token still has scopes coverage"""
        user.client.scopes = [PRIVACY_REQUEST_REVIEW]
        user.client.save(db)
        payload = {
            JWE_PAYLOAD_ROLES: [OWNER],
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SCOPES: [PRIVACY_REQUEST_REVIEW],
        }
        token = generate_jwe(
            json.dumps(payload),
            config.security.app_encryption_key,
        )
        client = await verify_oauth_client_async(
            SecurityScopes([PRIVACY_REQUEST_REVIEW]),
            token,
            db=async_session,
        )
        assert client.id == user.client.id

    async def test_token_does_not_have_role_with_coverage(
        self, async_session, config, viewer_user
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
            await verify_oauth_client_async(
                SecurityScopes([DATASET_CREATE_OR_UPDATE]),
                token,
                db=async_session,
            )


class TestPermissionCheckerDI:
    """Tests for the dependency-injected permission checker pattern.

    The permission checker is provided via ``get_permission_checker()`` (a FastAPI
    dependency) or passed explicitly as the ``permission_checker`` parameter to
    ``has_permissions()``. There is no global mutable state.
    """

    def test_get_permission_checker_returns_default(self):
        """get_permission_checker returns default_has_permissions."""
        checker = get_permission_checker()
        assert checker is default_has_permissions

    def test_default_behavior_without_custom_checker(self, oauth_client):
        """Without a custom checker, has_permissions uses default logic."""
        token_data = {
            JWE_PAYLOAD_SCOPES: [DATASET_CREATE_OR_UPDATE, USER_READ],
        }
        assert has_permissions(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    def test_custom_checker_is_called_via_parameter(self, oauth_client):
        """A custom checker passed as a parameter is invoked correctly."""
        checker_calls = []

        def custom_checker(token_data, client, endpoint_scopes, db):
            checker_calls.append(
                {
                    "db": db,
                    "token_data": token_data,
                    "client": client,
                    "scopes": endpoint_scopes.scopes,
                }
            )
            return True

        token_data = {JWE_PAYLOAD_SCOPES: [USER_READ]}
        has_permissions(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
            permission_checker=custom_checker,
        )

        assert len(checker_calls) == 1
        assert checker_calls[0]["token_data"] == token_data
        assert checker_calls[0]["client"] == oauth_client
        assert checker_calls[0]["scopes"] == [DATASET_CREATE_OR_UPDATE]

    def test_custom_checker_grants_permission(self, oauth_client):
        """Custom checker returning True grants permission."""

        def always_allow(token_data, client, endpoint_scopes, db):
            return True

        # Even with empty token data, custom checker grants permission
        token_data = {}
        assert has_permissions(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
            permission_checker=always_allow,
        )

    def test_custom_checker_denies_permission(self, oauth_client):
        """Custom checker returning False denies permission."""

        def always_deny(token_data, client, endpoint_scopes, db):
            return False

        # Even with valid scopes, custom checker denies permission
        token_data = {
            JWE_PAYLOAD_SCOPES: [DATASET_CREATE_OR_UPDATE, USER_READ],
        }
        assert not has_permissions(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
            permission_checker=always_deny,
        )

    def test_omitting_checker_uses_default(self, oauth_client):
        """When permission_checker is not passed, default_has_permissions is used."""
        token_data = {
            JWE_PAYLOAD_SCOPES: [DATASET_CREATE_OR_UPDATE, USER_READ],
        }

        # Custom checker would deny
        def always_deny(token_data, client, endpoint_scopes, db):
            return False

        # With custom checker: denied
        assert not has_permissions(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
            permission_checker=always_deny,
        )

        # Without custom checker (default): allowed because scopes match
        assert has_permissions(
            token_data,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )

    def test_db_parameter_passed_to_custom_checker(self, oauth_client):
        """The db parameter should be passed through to the custom checker."""
        received_db = []

        def capture_db(token_data, client, endpoint_scopes, db):
            received_db.append(db)
            return True

        mock_db = "mock_db_session"
        has_permissions(
            {},
            oauth_client,
            endpoint_scopes=SecurityScopes([USER_READ]),
            db=mock_db,
            permission_checker=capture_db,
        )

        assert len(received_db) == 1
        assert received_db[0] == mock_db

    def test_db_parameter_none_when_not_provided(self, oauth_client):
        """When db is not provided, it should be None in the custom checker."""
        received_db = []

        def capture_db(token_data, client, endpoint_scopes, db):
            received_db.append(db)
            return True

        has_permissions(
            {},
            oauth_client,
            endpoint_scopes=SecurityScopes([USER_READ]),
            permission_checker=capture_db,
        )

        assert len(received_db) == 1
        assert received_db[0] is None

    def test_checker_composes_with_default(self, oauth_client):
        """A custom checker can call default_has_permissions internally for composition."""

        def composing_checker(token_data, client, endpoint_scopes, db):
            # First check default logic
            if default_has_permissions(token_data, client, endpoint_scopes, db):
                return True
            # Then add custom logic (e.g., RBAC lookup)
            return token_data.get("custom_rbac_allowed", False)

        # Case 1: default logic allows (scopes match)
        token_data_with_scopes = {
            JWE_PAYLOAD_SCOPES: [DATASET_CREATE_OR_UPDATE, USER_READ],
        }
        assert has_permissions(
            token_data_with_scopes,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
            permission_checker=composing_checker,
        )

        # Case 2: default logic denies, custom RBAC allows
        token_data_rbac = {"custom_rbac_allowed": True}
        assert has_permissions(
            token_data_rbac,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
            permission_checker=composing_checker,
        )

        # Case 3: both deny
        token_data_empty = {}
        assert not has_permissions(
            token_data_empty,
            oauth_client,
            endpoint_scopes=SecurityScopes([DATASET_CREATE_OR_UPDATE]),
            permission_checker=composing_checker,
        )


class TestAsyncPermissionChecker:
    """Tests for the async permission checker dependency."""

    def test_get_async_permission_checker_returns_default(self):
        """get_async_permission_checker returns default_has_permissions_async."""
        checker = get_async_permission_checker()
        assert checker is default_has_permissions_async

    @pytest.mark.asyncio
    async def test_default_async_checker_delegates_to_sync(self, oauth_client):
        """The default async checker produces the same result as the sync default."""
        token_data = {
            JWE_PAYLOAD_SCOPES: [DATASET_CREATE_OR_UPDATE, USER_READ],
        }
        scopes = SecurityScopes([DATASET_CREATE_OR_UPDATE])

        sync_result = default_has_permissions(token_data, oauth_client, scopes)
        async_result = await default_has_permissions_async(
            token_data, oauth_client, scopes
        )

        assert sync_result == async_result
        assert async_result is True

    @pytest.mark.asyncio
    async def test_default_async_checker_denies_missing_scopes(self, oauth_client):
        """The default async checker denies when scopes are missing."""
        token_data = {JWE_PAYLOAD_SCOPES: [USER_READ]}
        result = await default_has_permissions_async(
            token_data,
            oauth_client,
            SecurityScopes([DATASET_CREATE_OR_UPDATE]),
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_async_checker_receives_db(self, oauth_client):
        """A custom async checker receives the db parameter."""
        received_db = []

        async def capture_db(token_data, client, endpoint_scopes, db):
            received_db.append(db)
            return True

        mock_async_session = "mock_async_session"
        result = await capture_db(
            {},
            oauth_client,
            SecurityScopes([USER_READ]),
            mock_async_session,
        )

        assert result is True
        assert len(received_db) == 1
        assert received_db[0] == mock_async_session

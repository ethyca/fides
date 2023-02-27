import json
from datetime import datetime

import pytest
from fastapi.security import SecurityScopes
from fideslang.models import System as SystemSchema

from fides.api.ops.api.v1.scope_registry import POLICY_CREATE_OR_UPDATE, SYSTEM_UPDATE
from fides.api.ops.util.system_manager_oauth_util import (
    SystemAuthContainer,
    _get_system_from_fides_key,
    _get_system_from_request_body,
    _has_scope_as_system_manager,
    verify_oauth_client_for_system_from_request_body,
)
from fides.core.config import CONFIG
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SYSTEMS,
)
from fides.lib.exceptions import AuthorizationError
from fides.lib.oauth.jwt import generate_jwe
from fides.lib.oauth.roles import ADMIN, VIEWER


class TestHasSystemPermissions:
    """Users can have permissions to work with the given system through multiple avenues:
    They might have a broad role that contains the proper scope, they might have the correct scope
    directly, or being system manager of the particular system might grant them the correct scopes.

    It doesn't matter how you get the correct scope; you can have the scope through multiple avenues
    as well.  As long as you have the right scope, you can work with the given resource.
    """

    async def test_admin_role_can_always_update_system(self, admin_user, db, system):
        payload = {
            JWE_PAYLOAD_ROLES: [ADMIN],
            JWE_PAYLOAD_CLIENT_ID: admin_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            CONFIG.security.app_encryption_key,
        )  # Note token doesn't have system on it, but the user is an admin

        response = await verify_oauth_client_for_system_from_request_body(
            security_scopes=SecurityScopes(scopes=[SYSTEM_UPDATE]),
            authorization=token,
            db=db,
            system_auth_data=SystemAuthContainer(
                original_data=system.fides_key, system=system
            ),
        )

        assert response == system.fides_key

    async def test_viewer_role_alone_cannot_update_system(
        self, viewer_user, db, system
    ):
        payload = {
            JWE_PAYLOAD_ROLES: [VIEWER],
            JWE_PAYLOAD_CLIENT_ID: viewer_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        token = generate_jwe(
            json.dumps(payload),
            CONFIG.security.app_encryption_key,
        )  # Note token doesn't have system on it, and user is only a viewer

        with pytest.raises(AuthorizationError):
            await verify_oauth_client_for_system_from_request_body(
                security_scopes=SecurityScopes(scopes=[SYSTEM_UPDATE]),
                authorization=token,
                db=db,
                system_auth_data=SystemAuthContainer(
                    original_data=system.fides_key, system=system
                ),
            )

    async def test_viewer_is_also_system_manager(self, system_manager, db, system):
        payload = {
            JWE_PAYLOAD_ROLES: [VIEWER],
            JWE_PAYLOAD_CLIENT_ID: system_manager.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SYSTEMS: [system.id],
        }
        token = generate_jwe(
            json.dumps(payload),
            CONFIG.security.app_encryption_key,
        )

        resp = await verify_oauth_client_for_system_from_request_body(
            security_scopes=SecurityScopes(scopes=[SYSTEM_UPDATE]),
            authorization=token,
            db=db,
            system_auth_data=SystemAuthContainer(
                original_data=system.fides_key, system=system
            ),
        )

        assert resp == system.fides_key

    async def test_system_manager_no_system_found(self, system_manager, db, system):
        payload = {
            JWE_PAYLOAD_ROLES: [VIEWER],
            JWE_PAYLOAD_CLIENT_ID: system_manager.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SYSTEMS: [system.id],
        }
        token = generate_jwe(
            json.dumps(payload),
            CONFIG.security.app_encryption_key,
        )

        with pytest.raises(AuthorizationError):
            await verify_oauth_client_for_system_from_request_body(
                security_scopes=SecurityScopes(scopes=[SYSTEM_UPDATE]),
                authorization=token,
                db=db,
                system_auth_data=SystemAuthContainer(
                    original_data=system.fides_key, system=None
                ),
            )

    async def test_system_manager_systems_not_on_token(
        self, system_manager, db, system
    ):
        payload = {
            JWE_PAYLOAD_ROLES: [VIEWER],
            JWE_PAYLOAD_CLIENT_ID: system_manager.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SYSTEMS: [],
        }
        token = generate_jwe(
            json.dumps(payload),
            CONFIG.security.app_encryption_key,
        )

        with pytest.raises(AuthorizationError):
            await verify_oauth_client_for_system_from_request_body(
                security_scopes=SecurityScopes(scopes=[SYSTEM_UPDATE]),
                authorization=token,
                db=db,
                system_auth_data=SystemAuthContainer(
                    original_data=system.fides_key, system=system
                ),
            )

    async def test_system_manager_client_cannot_issue_systems(
        self, system_manager, db, system
    ):
        system_manager.client.systems = []
        system_manager.client.save(db=db)

        payload = {
            JWE_PAYLOAD_ROLES: [VIEWER],
            JWE_PAYLOAD_CLIENT_ID: system_manager.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SYSTEMS: [system.id],
        }
        token = generate_jwe(
            json.dumps(payload),
            CONFIG.security.app_encryption_key,
        )

        with pytest.raises(AuthorizationError):
            await verify_oauth_client_for_system_from_request_body(
                security_scopes=SecurityScopes(scopes=[SYSTEM_UPDATE]),
                authorization=token,
                db=db,
                system_auth_data=SystemAuthContainer(
                    original_data=system.fides_key, system=system
                ),
            )

    async def test_system_manager_does_not_have_proper_scope_for_given_endpoint(
        self, system_manager, db, system
    ):
        payload = {
            JWE_PAYLOAD_ROLES: [VIEWER],
            JWE_PAYLOAD_CLIENT_ID: system_manager.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SYSTEMS: [system.id],
        }
        token = generate_jwe(
            json.dumps(payload),
            CONFIG.security.app_encryption_key,
        )

        with pytest.raises(AuthorizationError):
            await verify_oauth_client_for_system_from_request_body(
                security_scopes=SecurityScopes(scopes=[POLICY_CREATE_OR_UPDATE]),
                authorization=token,
                db=db,
                system_auth_data=SystemAuthContainer(
                    original_data=system.fides_key, system=system
                ),
            )


class TestHasScopeAsSystemManager:
    def test_no_system_found(self, system, system_manager):
        """
        Assert system manager doesn't have permissions if the system in the request can't be found
        """
        token_data = {JWE_PAYLOAD_SYSTEMS: [system.id]}
        assert not _has_scope_as_system_manager(
            token_data,
            system_manager.client,
            SecurityScopes(scopes=[SYSTEM_UPDATE]),
            system=None,
        )

    def test_systems_are_not_on_the_user_token(self, system_manager):
        """
        Assert system manager doesn't have permissions if the system id is not on the token
        """
        assert not _has_scope_as_system_manager(
            {},
            system_manager.client,
            SecurityScopes(scopes=[SYSTEM_UPDATE]),
            system=None,
        )

    def test_client_does_not_have_system_id(self, db, system, system_manager):
        """
        Assert system manager doesn't have permissions if the client is no longer allowed to issue
        tokens with this system
        """
        system_manager.client.systems = []
        system_manager.client.save(db=db)

        token_data = {JWE_PAYLOAD_SYSTEMS: [system.id]}

        assert not _has_scope_as_system_manager(
            token_data,
            system_manager.client,
            SecurityScopes(scopes=[SYSTEM_UPDATE]),
            system=system,
        )

    def test_system_manager_does_not_have_scopes_for_this_endpoint(
        self, system, system_manager
    ):
        """
        Assert the current endpoint isn't covered by system manager scopes
        """
        token_data = {JWE_PAYLOAD_SYSTEMS: [system.id]}
        assert not _has_scope_as_system_manager(
            token_data,
            system_manager.client,
            SecurityScopes(scopes=[POLICY_CREATE_OR_UPDATE]),
            system=system,
        )

    def test_system_has_scope_as_system_manager(self, system, system_manager):
        """
        Assert system manager has permissions if the system exists, the system is on the token,
        the client is still allowed to issue tokens with that system, and system manager scopes include
        the scope on the endpoint
        """
        token_data = {JWE_PAYLOAD_SYSTEMS: [system.id]}
        assert _has_scope_as_system_manager(
            token_data,
            system_manager.client,
            SecurityScopes(scopes=[SYSTEM_UPDATE]),
            system=system,
        )


class GetSystemFromRequestBody:
    def test_get_system_from_request_body(self, db, system):
        system_schema = SystemSchema(
            fides_key=system.fides_key,
            system_type="Service",
            data_responsibility_title="Processor",
        )

        resp = _get_system_from_request_body(system_schema, db)

        assert resp.system == system
        assert resp.original_data == system_schema

    def test_get_system_from_fides_key(self, db, system):
        resp = _get_system_from_fides_key(system.fides_key, db)

        assert resp.system == system
        assert resp.original_data == system.fides_key

    def test_get_system_from_request_body_not_found(self, db):
        system_schema = SystemSchema(
            fides_key="unknown_fides_key",
            system_type="Service",
            data_responsibility_title="Processor",
        )

        resp = _get_system_from_request_body(system_schema, db)

        assert resp.system is None
        assert resp.original_data == system_schema

    def test_get_system_from_fides_key_not_found(self, db):
        resp = _get_system_from_fides_key("unknown_fides_key", db)

        assert resp.system is None
        assert resp.original_data == "unknown_fides_key"

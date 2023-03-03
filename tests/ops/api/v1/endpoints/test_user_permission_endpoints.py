import json

import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.ops.api.v1.scope_registry import (
    PRIVACY_REQUEST_READ,
    SAAS_CONFIG_READ,
    SCOPE_REGISTRY,
    USER_PERMISSION_CREATE,
    USER_PERMISSION_READ,
    USER_PERMISSION_UPDATE,
)
from fides.api.ops.api.v1.urn_registry import USER_PERMISSIONS, V1_URL_PREFIX
from fides.core.config import CONFIG
from fides.lib.models.client import ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions
from fides.lib.oauth.roles import OWNER, VIEWER
from tests.conftest import generate_auth_header_for_user, generate_role_header_for_user


class TestCreateUserPermissions:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + USER_PERMISSIONS

    def test_create_user_permissions_not_authenticated(self, url, api_client):
        response = api_client.post(url, headers={}, json={})
        assert HTTP_401_UNAUTHORIZED == response.status_code

    def test_create_user_permissions_wrong_scope(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header([SAAS_CONFIG_READ])
        response = api_client.post(url, headers=auth_header, json={})
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_create_user_permissions_invalid_scope(
        self,
        db,
        api_client,
        generate_auth_header,
        user,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"user_id": user.id, "scopes": ["not a real scope"]}

        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert "Invalid Scope(s) {'not a real scope'}" in response.json()["detail"]
        user.delete(db)

    def test_create_user_permissions_invalid_user_id(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user_id = "bogus_user_id"
        body = {"user_id": user_id, "scopes": [PRIVACY_REQUEST_READ]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user_id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user_id)
        assert HTTP_404_NOT_FOUND == response.status_code
        assert permissions is None

    def test_create_user_permissions_add_scopes_no_client_to_update(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user.id)
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body["id"] == permissions.id
        assert permissions.scopes == [PRIVACY_REQUEST_READ]
        assert not user.client
        user.delete(db)

    def test_create_user_permissions_add_scopes(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )
        client = ClientDetail(
            hashed_secret="thisisatest",
            salt="thisisstillatest",
            scopes=[],
            roles=[VIEWER],
            user_id=user.id,
        )
        db.add(client)
        db.commit()

        body = {"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user.id)
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body["id"] == permissions.id
        assert permissions.scopes == [PRIVACY_REQUEST_READ]
        assert (
            user.client.roles == []
        ), "Roles not specified in request so they were overridden"
        user.delete(db)

    def test_create_user_permissions_add_bad_role(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )
        body = {"user_id": user.id, "roles": ["nonexistent role"]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            "value is not a valid enumeration member"
            in response_body["detail"][0]["msg"]
        )

    def test_create_user_permissions_add_roles(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )
        client = ClientDetail(
            hashed_secret="thisisatest",
            salt="thisisstillatest",
            scopes=[PRIVACY_REQUEST_READ],
            roles=[],
            user_id=user.id,
        )
        db.add(client)
        db.commit()

        body = {"user_id": user.id, "roles": [VIEWER]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user.id)
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body["id"] == permissions.id
        assert permissions.scopes == []
        assert permissions.roles == [VIEWER]
        assert client.scopes == [], "No scopes in body so they were overridden"
        user.delete(db)

    def test_create_roles_on_permission_object_and_client(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )
        client = ClientDetail(
            hashed_secret="thisisatest",
            salt="thisisstillatest",
            scopes=[],
            roles=[VIEWER],
            user_id=user.id,
        )
        db.add(client)
        db.commit()

        body = {"user_id": user.id, "roles": [OWNER]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user.id)
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body["id"] == permissions.id
        assert permissions.scopes == []
        assert permissions.roles == [OWNER]
        db.refresh(client)
        assert client.roles == [OWNER]
        user.delete(db)


class TestEditUserPermissions:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + USER_PERMISSIONS

    def test_edit_user_permissions_not_authenticated(self, url, api_client):
        response = api_client.put(url, headers={}, json={})
        assert HTTP_401_UNAUTHORIZED == response.status_code

    def test_edit_user_permissions_wrong_scope(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header([SAAS_CONFIG_READ])
        response = api_client.put(url, headers=auth_header, json={})
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_edit_user_permissions_invalid_scope(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"scopes": ["not a real scope"]}

        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert "Invalid Scope(s) {'not a real scope'}" in response.json()["detail"]
        user.delete(db)

    def test_edit_user_permissions_invalid_user_id(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        invalid_user_id = "bogus_user_id"
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )
        body = {"id": permissions.id, "scopes": [PRIVACY_REQUEST_READ]}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{invalid_user_id}/permission",
            headers=auth_header,
            json=body,
        )
        permissions = FidesUserPermissions.get_by(
            db, field="user_id", value=invalid_user_id
        )
        assert HTTP_404_NOT_FOUND == response.status_code
        assert permissions is None
        user.delete(db)

    def test_optional_permissions_id(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "scopes": [PRIVACY_REQUEST_READ],
                "roles": [VIEWER],
            },
        )
        permissions_id = permissions.id

        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=[PRIVACY_REQUEST_READ],
            roles=[VIEWER],
            user_id=user.id,
        )

        updated_scopes = [PRIVACY_REQUEST_READ, SAAS_CONFIG_READ]
        body = {"scopes": updated_scopes}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["scopes"] == updated_scopes
        assert (
            response_body["roles"] == []
        ), "Roles removed as they were not specified in the request"
        assert response_body["id"] == permissions_id

        client: ClientDetail = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert client.scopes == updated_scopes
        assert client.roles == []

        db.refresh(permissions)
        assert permissions.scopes == updated_scopes
        assert permissions.roles == []
        assert permissions.id == permissions_id

        user.delete(db)

    def test_edit_user_scopes(self, db, api_client, generate_auth_header) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "scopes": [PRIVACY_REQUEST_READ],
                "roles": [VIEWER],
            },
        )
        permissions_id = permissions.id

        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=[PRIVACY_REQUEST_READ],
            roles=[VIEWER],
            user_id=user.id,
        )

        updated_scopes = [PRIVACY_REQUEST_READ, SAAS_CONFIG_READ]
        # Note: It is odd that we have the permissions id in the request body.
        # I've made it optional as the UI sends it.  Verify we ignore it.
        body = {"id": "invalid_id", "scopes": updated_scopes}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["scopes"] == updated_scopes
        assert (
            response_body["roles"] == []
        ), "Roles removed as they were not specified in the request"
        assert response_body["id"] == permissions_id

        client: ClientDetail = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert client.scopes == updated_scopes
        assert client.roles == []

        db.refresh(permissions)
        assert permissions.scopes == updated_scopes
        assert permissions.roles == []
        assert permissions.id == permissions_id

        user.delete(db)

    def test_edit_user_roles(self, db, api_client, generate_auth_header) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "scopes": [PRIVACY_REQUEST_READ],
                "roles": [VIEWER],
            },
        )

        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=[PRIVACY_REQUEST_READ],
            roles=[VIEWER],
            user_id=user.id,
        )

        body = {"id": permissions.id, "roles": [OWNER]}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert (
            response_body["scopes"] == []
        ), "Scopes removed as they were not specified in the request"
        assert response_body["roles"] == [OWNER]

        client: ClientDetail = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert client.scopes == []
        assert client.roles == [OWNER]

        db.refresh(permissions)
        assert permissions.scopes == []
        assert permissions.roles == [OWNER]

        user.delete(db)


class TestGetUserPermissions:
    @pytest.fixture(scope="function")
    def user(self, db) -> FidesUser:
        return FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

    @pytest.fixture(scope="function")
    def auth_user(self, db) -> FidesUser:
        return FidesUser.create(
            db=db,
            data={"username": "auth_user", "password": "test_password"},
        )

    @pytest.fixture(scope="function")
    def permissions(self, db, user) -> FidesUserPermissions:
        return FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )

    def test_get_user_permissions_not_authenticated(self, api_client, user):
        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{user.id}/permission",
        )
        assert HTTP_401_UNAUTHORIZED == response.status_code

    def test_get_user_permissions_wrong_scope(self, db, api_client, user, auth_user):
        scopes = [PRIVACY_REQUEST_READ]
        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )
        auth_header = generate_auth_header_for_user(auth_user, scopes)

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{user.id}/permission",
            headers=auth_header,
        )
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_get_user_permissions_invalid_user_id(
        self, db, api_client, auth_user
    ) -> None:
        scopes = [USER_PERMISSION_READ]
        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )
        auth_header = generate_auth_header_for_user(auth_user, scopes)
        invalid_user_id = "bogus_user_id"

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{invalid_user_id}/permission",
            headers=auth_header,
        )
        permissions = FidesUserPermissions.get_by(
            db, field="user_id", value=invalid_user_id
        )
        assert HTTP_404_NOT_FOUND == response.status_code
        assert permissions is None

    def test_get_user_permissions(
        self, db, api_client, user, auth_user, permissions
    ) -> None:
        scopes = [USER_PERMISSION_READ]
        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )
        auth_header = generate_auth_header_for_user(auth_user, scopes)

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{user.id}/permission",
            headers=auth_header,
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == permissions.id
        assert response_body["user_id"] == user.id
        assert response_body["scopes"] == [PRIVACY_REQUEST_READ]
        assert response_body["roles"] == []

    def test_get_user_with_no_permissions_as_root(
        self, db, api_client, auth_user, root_auth_header
    ):
        FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "scopes": None, "roles": None}
        )

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=root_auth_header,
        )
        resp = response.json()
        assert resp["scopes"] == []
        assert resp["roles"] == []
        assert resp["user_id"] == auth_user.id

    def test_get_current_user_permissions(self, db, api_client, auth_user) -> None:
        # Note: Does not include USER_PERMISSION_READ.
        scopes = [PRIVACY_REQUEST_READ, SAAS_CONFIG_READ]
        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )
        auth_header = generate_auth_header_for_user(auth_user, scopes)
        permissions = FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "scopes": scopes}
        )

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=auth_header,
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == permissions.id
        assert response_body["user_id"] == auth_user.id
        assert response_body["scopes"] == scopes
        assert response_body["roles"] == []

    def test_get_current_root_user_permissions(
        self, api_client, oauth_root_client, root_auth_header
    ):
        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{oauth_root_client.id}/permission",
            headers=root_auth_header,
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == oauth_root_client.id
        assert response_body["user_id"] == oauth_root_client.id
        assert response_body["scopes"] == SCOPE_REGISTRY
        assert response_body["roles"] == [OWNER]

    def test_get_root_user_permissions_by_non_root_user(
        self, db, api_client, oauth_root_client, auth_user
    ):
        # Even with user read permissions, the root user can't be queried.
        scopes = [USER_PERMISSION_READ]
        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )
        auth_header = generate_auth_header_for_user(auth_user, scopes)

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{oauth_root_client.user_id}/permission",
            headers=auth_header,
        )
        assert HTTP_404_NOT_FOUND == response.status_code

    def test_get_own_user_roles(self, db, api_client, auth_user):
        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            roles=[VIEWER],
            user_id=auth_user.id,
        )
        FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "roles": [VIEWER]}
        )

        auth_header = generate_role_header_for_user(auth_user, roles=[VIEWER])
        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=auth_header,
        )
        resp = response.json()
        assert resp["scopes"] == []
        assert resp["roles"] == [VIEWER]
        assert resp["user_id"] == auth_user.id

    def test_get_other_user_roles_as_root(
        self, db, api_client, auth_user, root_auth_header
    ):

        FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "roles": [VIEWER]}
        )

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=root_auth_header,
        )
        resp = response.json()
        assert resp["scopes"] == []
        assert resp["roles"] == [VIEWER]
        assert resp["user_id"] == auth_user.id

    def test_get_other_user_roles_as_viewer(
        self, db, api_client, auth_user, viewer_user
    ):
        FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "roles": [VIEWER]}
        )

        auth_header = generate_role_header_for_user(viewer_user, roles=[VIEWER])

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=auth_header,
        )
        assert response.status_code == 403

    def test_get_other_user_roles_as_owner(self, db, api_client, auth_user, owner_user):
        FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "roles": [VIEWER]}
        )

        auth_header = generate_role_header_for_user(owner_user, roles=[OWNER])

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=auth_header,
        )
        assert response.status_code == 200
        resp = response.json()
        assert resp["scopes"] == []
        assert resp["roles"] == [VIEWER]
        assert resp["user_id"] == auth_user.id

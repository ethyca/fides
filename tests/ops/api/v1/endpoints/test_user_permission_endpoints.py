import pytest
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.roles import (
    APPROVER,
    CONTRIBUTOR,
    OWNER,
    ROLES_TO_SCOPES_MAPPING,
    VIEWER,
    VIEWER_AND_APPROVER,
)
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_READ,
    SAAS_CONFIG_READ,
    SCOPE_REGISTRY,
    USER_PERMISSION_ASSIGN_OWNERS,
    USER_PERMISSION_CREATE,
    USER_PERMISSION_READ,
    USER_PERMISSION_UPDATE,
)
from fides.common.api.v1.urn_registry import USER_PERMISSIONS, V1_URL_PREFIX
from fides.config import CONFIG
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

    def test_create_user_permissions_invalid_user_id(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user_id = "bogus_user_id"
        body = {"user_id": user_id, "roles": [VIEWER]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user_id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user_id)
        assert HTTP_404_NOT_FOUND == response.status_code
        assert permissions is None

    def test_create_user_permissions_no_client_to_update(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"user_id": user.id, "roles": [APPROVER]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user.id)
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body["id"] == permissions.id
        assert permissions.roles == [APPROVER]
        assert not user.client
        user.delete(db)

    def test_create_user_permissions_add_scopes_are_ignored(
        self, db, api_client, generate_auth_header
    ) -> None:
        """Test scopes in the request body are ignored - the UI may still be passing in scopes"""
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

        body = {
            "user_id": user.id,
            "roles": [APPROVER],
            "scopes": [PRIVACY_REQUEST_READ],
        }
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user.id)
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body["id"] == permissions.id
        assert permissions.roles == [APPROVER]
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
            "Input should be 'owner', 'viewer_and_approver', 'viewer', 'approver' or 'contributor'"
            in response_body["detail"][0]["msg"]
        )

    def test_create_user_permissions_roles_are_an_empty_list(
        self, db, api_client, generate_auth_header
    ) -> None:
        """If roles are an empty list, user will have no roles"""
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"user_id": user.id, "roles": []}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user.id)
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body["roles"] == []
        assert permissions.roles == []
        user.delete(db)

    def test_create_user_permissions_no_role_key(
        self, db, api_client, generate_auth_header
    ) -> None:
        """Roles key explicitly required"""
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"user_id": user.id}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code

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
            scopes=[],
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
        assert permissions.roles == [VIEWER]

        assert client.roles == [VIEWER]
        assert client.scopes == [], "User create flow doesn't override client scopes"
        user.delete(db)

    @pytest.mark.parametrize(
        "acting_user,added_role,expected_response",
        [
            ("owner_user", APPROVER, HTTP_201_CREATED),
            ("owner_user", VIEWER_AND_APPROVER, HTTP_201_CREATED),
            ("owner_user", VIEWER, HTTP_201_CREATED),
            ("owner_user", CONTRIBUTOR, HTTP_201_CREATED),
            ("owner_user", OWNER, HTTP_201_CREATED),
            ("contributor_user", APPROVER, HTTP_201_CREATED),
            ("contributor_user", VIEWER_AND_APPROVER, HTTP_201_CREATED),
            ("contributor_user", VIEWER, HTTP_201_CREATED),
            ("contributor_user", CONTRIBUTOR, HTTP_201_CREATED),
            ("contributor_user", OWNER, HTTP_403_FORBIDDEN),
            ("viewer_user", APPROVER, HTTP_403_FORBIDDEN),
            ("viewer_user", VIEWER_AND_APPROVER, HTTP_403_FORBIDDEN),
            ("viewer_user", VIEWER, HTTP_403_FORBIDDEN),
            ("viewer_user", CONTRIBUTOR, HTTP_403_FORBIDDEN),
            ("viewer_user", OWNER, HTTP_403_FORBIDDEN),
            ("viewer_and_approver_user", APPROVER, HTTP_403_FORBIDDEN),
            (
                "viewer_and_approver_user",
                VIEWER_AND_APPROVER,
                HTTP_403_FORBIDDEN,
            ),
            ("viewer_and_approver_user", VIEWER, HTTP_403_FORBIDDEN),
            ("viewer_and_approver_user", CONTRIBUTOR, HTTP_403_FORBIDDEN),
            ("viewer_and_approver_user", OWNER, HTTP_403_FORBIDDEN),
            ("approver_user", APPROVER, HTTP_403_FORBIDDEN),
            ("approver_user", VIEWER_AND_APPROVER, HTTP_403_FORBIDDEN),
            ("approver_user", VIEWER, HTTP_403_FORBIDDEN),
            ("approver_user", CONTRIBUTOR, HTTP_403_FORBIDDEN),
            ("approver_user", OWNER, HTTP_403_FORBIDDEN),
        ],
    )
    def test_create_user_roles_permission_matrix(
        self,
        db,
        acting_user,
        added_role,
        expected_response,
        request,
        api_client,
    ):
        """Test asserting what roles can be granted to other users given your current role
        when assigning initial user permissions"""
        acting_user = request.getfixturevalue(acting_user)
        updated_user = FidesUser.create(
            db=db,
            data={"username": "new_user", "password": "test_password"},
        )

        auth_header = generate_role_header_for_user(
            acting_user, roles=acting_user.permissions.roles
        )
        body = {"user_id": updated_user.id, "roles": [added_role]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{updated_user.id}/permission",
            headers=auth_header,
            json=body,
        )
        assert response.status_code == expected_response
        updated_user.delete(db)


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
            db=db, data={"user_id": user.id, "roles": [APPROVER]}
        )
        body = {"id": permissions.id, "roles": [APPROVER]}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{invalid_user_id}/permission",
            headers=auth_header,
            json=body,
        )
        assert HTTP_404_NOT_FOUND == response.status_code

        permissions = FidesUserPermissions.get_by(
            db, field="user_id", value=invalid_user_id
        )
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
                "roles": [VIEWER],
            },
        )
        permissions_id = permissions.id

        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            roles=[VIEWER],
            user_id=user.id,
        )

        updated_roles = [CONTRIBUTOR]
        body = {"roles": updated_roles}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["roles"] == updated_roles
        assert response_body["id"] == permissions_id

        client: ClientDetail = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert client.roles == [CONTRIBUTOR]

        db.refresh(permissions)
        assert permissions.roles == [CONTRIBUTOR]
        assert permissions.id == permissions_id

        user.delete(db)

    def test_edit_user_scopes_are_ignored(
        self, db, api_client, generate_auth_header
    ) -> None:
        """Scopes in request are ignored as you can no longer edit user scopes"""
        auth_header = generate_auth_header(
            [USER_PERMISSION_UPDATE, USER_PERMISSION_ASSIGN_OWNERS]
        )
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "roles": [VIEWER],
            },
        )

        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            roles=[VIEWER],
            user_id=user.id,
        )

        body = {
            "id": permissions.id,
            "scopes": [PRIVACY_REQUEST_READ],
            "roles": [OWNER],
        }
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["roles"] == [OWNER]

        client: ClientDetail = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert (
            client.scopes == []
        ), "Assert client scopes are not updated via the user permissions update flow"
        assert client.roles == [OWNER]

        db.refresh(permissions)
        assert permissions.roles == [OWNER]

        user.delete(db)

    def test_edit_user_roles(self, db, api_client, generate_auth_header) -> None:
        auth_header = generate_auth_header(
            [USER_PERMISSION_UPDATE, USER_PERMISSION_ASSIGN_OWNERS]
        )
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "roles": [VIEWER],
            },
        )

        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            roles=[VIEWER],
            user_id=user.id,
        )

        body = {"id": permissions.id, "roles": [OWNER]}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["roles"] == [OWNER]

        client: ClientDetail = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert (
            client.scopes == []
        ), "Assert client scopes are not updated via the user permissions update flow"
        assert client.roles == [OWNER]

        db.refresh(permissions)
        assert permissions.roles == [OWNER]

        user.delete(db)

    def test_edit_user_roles_remove_role(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(
            [USER_PERMISSION_UPDATE, USER_PERMISSION_ASSIGN_OWNERS]
        )
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "roles": [OWNER],
            },
        )

        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            roles=[VIEWER],
            user_id=user.id,
        )

        body = {"id": permissions.id, "roles": []}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["roles"] == []

        client: ClientDetail = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert (
            client.scopes == []
        ), "Assert client scopes are not updated via the user permissions update flow"
        assert client.roles == []

        db.refresh(permissions)
        assert permissions.roles == []

        user.delete(db)

    def test_edit_user_roles_request_no_role_key(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(
            [USER_PERMISSION_UPDATE, USER_PERMISSION_ASSIGN_OWNERS]
        )
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "roles": [OWNER],
            },
        )

        body = {"id": permissions.id}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code

        db.refresh(permissions)
        assert permissions.roles == [OWNER]

        user.delete(db)

    def test_making_user_a_contributor_does_not_affect_their_systems(
        self, db, api_client, system_manager, generate_auth_header
    ):
        assert system_manager.systems
        assert system_manager.permissions.roles == [VIEWER]

        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        body = {"id": system_manager.permissions.id, "roles": [CONTRIBUTOR]}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{system_manager.id}/permission",
            headers=auth_header,
            json=body,
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["roles"] == [CONTRIBUTOR]

        db.refresh(system_manager)
        assert system_manager.permissions.roles == [CONTRIBUTOR]
        assert system_manager.systems

    def test_making_user_an_approver_removes_their_systems(
        self, db, api_client, system_manager, generate_auth_header
    ):
        """Approvers cannot be system managers, so downgrading this user's role removes them as a system manager"""
        assert system_manager.systems
        assert system_manager.permissions.roles == [VIEWER]

        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        body = {"id": system_manager.permissions.id, "roles": [APPROVER]}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{system_manager.id}/permission",
            headers=auth_header,
            json=body,
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["roles"] == [APPROVER]

        db.refresh(system_manager)
        assert system_manager.permissions.roles == [APPROVER]
        assert not system_manager.systems

    @pytest.mark.parametrize(
        "acting_user,updating_role,updated_user,expected_response",
        [
            ("owner_user", APPROVER, "user", HTTP_200_OK),
            ("owner_user", VIEWER_AND_APPROVER, "user", HTTP_200_OK),
            ("owner_user", VIEWER, "user", HTTP_200_OK),
            ("owner_user", CONTRIBUTOR, "user", HTTP_200_OK),
            ("owner_user", OWNER, "user", HTTP_200_OK),
            ("contributor_user", APPROVER, "user", HTTP_200_OK),
            ("contributor_user", VIEWER_AND_APPROVER, "user", HTTP_200_OK),
            ("contributor_user", VIEWER, "user", HTTP_200_OK),
            ("contributor_user", CONTRIBUTOR, "user", HTTP_200_OK),
            ("contributor_user", OWNER, "user", HTTP_403_FORBIDDEN),
            ("viewer_user", APPROVER, "user", HTTP_403_FORBIDDEN),
            ("viewer_user", VIEWER_AND_APPROVER, "user", HTTP_403_FORBIDDEN),
            ("viewer_user", VIEWER, "user", HTTP_403_FORBIDDEN),
            ("viewer_user", CONTRIBUTOR, "user", HTTP_403_FORBIDDEN),
            ("viewer_user", OWNER, "user", HTTP_403_FORBIDDEN),
            ("viewer_and_approver_user", APPROVER, "user", HTTP_403_FORBIDDEN),
            (
                "viewer_and_approver_user",
                VIEWER_AND_APPROVER,
                "user",
                HTTP_403_FORBIDDEN,
            ),
            ("viewer_and_approver_user", VIEWER, "user", HTTP_403_FORBIDDEN),
            ("viewer_and_approver_user", CONTRIBUTOR, "user", HTTP_403_FORBIDDEN),
            ("viewer_and_approver_user", OWNER, "user", HTTP_403_FORBIDDEN),
            ("approver_user", APPROVER, "user", HTTP_403_FORBIDDEN),
            ("approver_user", VIEWER_AND_APPROVER, "user", HTTP_403_FORBIDDEN),
            ("approver_user", VIEWER, "user", HTTP_403_FORBIDDEN),
            ("approver_user", CONTRIBUTOR, "user", HTTP_403_FORBIDDEN),
            ("approver_user", OWNER, "user", HTTP_403_FORBIDDEN),
        ],
    )
    def test_edit_user_roles_permission_matrix(
        self,
        acting_user,
        updating_role,
        updated_user,
        expected_response,
        request,
        api_client,
    ):
        """Test asserting what roles can be granted to other users given your current role"""
        acting_user = request.getfixturevalue(acting_user)
        updated_user = request.getfixturevalue(updated_user)

        auth_header = generate_role_header_for_user(
            acting_user, roles=acting_user.permissions.roles
        )
        body = {"id": updated_user.permissions.id, "roles": [updating_role]}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{updated_user.id}/permission",
            headers=auth_header,
            json=body,
        )
        assert response.status_code == expected_response


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
            db=db, data={"user_id": user.id, "roles": [APPROVER]}
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
        assert response_body["roles"] == [APPROVER]
        assert response_body["total_scopes"] == ROLES_TO_SCOPES_MAPPING[APPROVER]

    def test_get_user_with_no_permissions_as_root(
        self, db, api_client, auth_user, root_auth_header
    ):
        FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "roles": None}
        )

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=root_auth_header,
        )
        resp = response.json()
        assert resp["roles"] == []
        assert resp["total_scopes"] == []
        assert resp["user_id"] == auth_user.id

    def test_get_current_user_permissions(self, db, api_client, auth_user) -> None:
        # Note: Does not include USER_PERMISSION_READ.
        ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            roles=[VIEWER],
            user_id=auth_user.id,
        )
        auth_header = generate_auth_header_for_user(
            auth_user, ROLES_TO_SCOPES_MAPPING[VIEWER]
        )

        permissions = FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "roles": [VIEWER]}
        )
        assert USER_PERMISSION_READ not in ROLES_TO_SCOPES_MAPPING[VIEWER]

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=auth_header,
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == permissions.id
        assert response_body["user_id"] == auth_user.id
        assert response_body["total_scopes"] == ROLES_TO_SCOPES_MAPPING[VIEWER]
        assert response_body["roles"] == [VIEWER]

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
        assert response_body["roles"] == [OWNER]
        assert response_body["total_scopes"] == sorted(SCOPE_REGISTRY)

        # Intentionally calling twice to make sure scopes didn't change
        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{oauth_root_client.id}/permission",
            headers=root_auth_header,
        )

        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == oauth_root_client.id
        assert response_body["user_id"] == oauth_root_client.id
        assert response_body["roles"] == [OWNER]
        assert response_body["total_scopes"] == sorted(SCOPE_REGISTRY)

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
        assert resp["roles"] == [VIEWER]
        assert resp["user_id"] == auth_user.id
        assert resp["total_scopes"] == sorted(ROLES_TO_SCOPES_MAPPING[VIEWER])

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
        assert resp["roles"] == [VIEWER]
        assert resp["user_id"] == auth_user.id
        assert resp["total_scopes"] == sorted(ROLES_TO_SCOPES_MAPPING[VIEWER])

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
        assert resp["roles"] == [VIEWER]
        assert resp["user_id"] == auth_user.id
        assert resp["total_scopes"] == sorted(ROLES_TO_SCOPES_MAPPING[VIEWER])

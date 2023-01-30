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
from fides.lib.models.client import ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions
from tests.conftest import generate_auth_header_for_user


class TestCreateUserPermissions:
    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + USER_PERMISSIONS

    def test_create_user_permissions_not_authenticated(self, url, api_client):
        response = api_client.post(url, headers={}, json={})
        assert HTTP_401_UNAUTHORIZED == response.status_code

    @pytest.mark.parametrize("auth_header", [[SAAS_CONFIG_READ]], indirect=True)
    def test_create_user_permissions_wrong_scope(self, auth_header, url, api_client):
        response = api_client.post(url, headers=auth_header, json={})
        assert HTTP_403_FORBIDDEN == response.status_code

    @pytest.mark.parametrize("auth_header", [[USER_PERMISSION_CREATE]], indirect=True)
    def test_create_user_permissions_invalid_scope(
        self, auth_header, db, api_client, user, url
    ):
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"user_id": user.id, "scopes": ["not a real scope"]}

        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code

    @pytest.mark.parametrize("auth_header", [[USER_PERMISSION_CREATE]], indirect=True)
    def test_create_user_permissions_invalid_user_id(self, auth_header, db, api_client):
        user_id = "bogus_user_id"
        body = {"user_id": user_id, "scopes": [PRIVACY_REQUEST_READ]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user_id}/permission", headers=auth_header, json=body
        )
        permissions = FidesUserPermissions.get_by(db, field="user_id", value=user_id)
        assert HTTP_404_NOT_FOUND == response.status_code
        assert permissions is None

    @pytest.mark.parametrize("auth_header", [[USER_PERMISSION_CREATE]], indirect=True)
    def test_create_user_permissions(self, auth_header, db, api_client):
        user = FidesUser.create(
            db=db, data={"username": "user_1", "password": "test_password"}
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


class TestEditUserPermissions:
    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + USER_PERMISSIONS

    def test_edit_user_permissions_not_authenticated(self, url, api_client):
        response = api_client.put(url, headers={}, json={})
        assert HTTP_401_UNAUTHORIZED == response.status_code

    @pytest.mark.parametrize("auth_header", [[SAAS_CONFIG_READ]], indirect=True)
    def test_edit_user_permissions_wrong_scope(self, auth_header, url, api_client):
        response = api_client.put(url, headers=auth_header, json={})
        assert HTTP_403_FORBIDDEN == response.status_code

    @pytest.mark.parametrize("auth_header", [[USER_PERMISSION_UPDATE]], indirect=True)
    def test_edit_user_permissions_invalid_scope(self, auth_header, api_client, url):
        body = {"user_id": "bogus_user_id", "scopes": ["not a real scope"]}

        response = api_client.put(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code

    @pytest.mark.parametrize("auth_header", [[USER_PERMISSION_UPDATE]], indirect=True)
    def test_edit_user_permissions_invalid_user_id(self, auth_header, db, api_client):
        invalid_user_id = "bogus_user_id"
        user = FidesUser.create(
            db=db, data={"username": "user_1", "password": "test_password"}
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
        assert HTTP_404_NOT_FOUND == response.status_code
        permissions = FidesUserPermissions.get_by(
            db, field="user_id", value=invalid_user_id
        )
        assert permissions is None

    @pytest.mark.parametrize("auth_header", [[USER_PERMISSION_UPDATE]], indirect=True)
    def test_edit_user_permissions(self, auth_header, db, api_client, config):
        user = FidesUser.create(
            db=db, data={"username": "user_1", "password": "test_password"}
        )

        permissions = FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )

        ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
            scopes=[PRIVACY_REQUEST_READ],
            user_id=user.id,
        )

        updated_scopes = [PRIVACY_REQUEST_READ, SAAS_CONFIG_READ]
        body = {"id": permissions.id, "scopes": updated_scopes}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == permissions.id
        assert response_body["scopes"] == updated_scopes

        client = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert client.scopes == updated_scopes


class TestGetUserPermissions:
    @pytest.fixture(scope="function")
    def user(self, db):
        return FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

    @pytest.fixture(scope="function")
    def auth_user(self, db):
        return FidesUser.create(
            db=db,
            data={"username": "auth_user", "password": "test_password"},
        )

    @pytest.fixture(scope="function")
    def permissions(self, db, user):
        return FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )

    def test_get_user_permissions_not_authenticated(self, api_client, user):
        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{user.id}/permission",
        )
        assert HTTP_401_UNAUTHORIZED == response.status_code

    def test_get_user_permissions_wrong_scope(
        self, db, api_client, user, auth_user, config
    ):
        scopes = [PRIVACY_REQUEST_READ]
        ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )

        auth_header = generate_auth_header_for_user(auth_user, scopes, config)

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{user.id}/permission",
            headers=auth_header,
        )
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_get_user_permissions_invalid_user_id(
        self, db, api_client, auth_user, config
    ):
        scopes = [USER_PERMISSION_READ]
        ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )
        invalid_user_id = "bogus_user_id"

        auth_header = generate_auth_header_for_user(auth_user, scopes, config)

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
        self, db, api_client, user, auth_user, permissions, config
    ):
        scopes = [USER_PERMISSION_READ]
        ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )

        auth_header = generate_auth_header_for_user(auth_user, scopes, config)

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{user.id}/permission",
            headers=auth_header,
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == permissions.id
        assert response_body["user_id"] == user.id
        assert response_body["scopes"] == [PRIVACY_REQUEST_READ]

    def test_get_current_user_permissions(self, db, api_client, auth_user, config):
        # Note: Does not include USER_PERMISSION_READ.
        scopes = [PRIVACY_REQUEST_READ, SAAS_CONFIG_READ]
        ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )
        permissions = FidesUserPermissions.create(
            db=db, data={"user_id": auth_user.id, "scopes": scopes}
        )

        auth_header = generate_auth_header_for_user(auth_user, scopes, config)

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{auth_user.id}/permission",
            headers=auth_header,
        )
        response_body = response.json()
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == permissions.id
        assert response_body["user_id"] == auth_user.id
        assert response_body["scopes"] == scopes

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

    def test_get_root_user_permissions_by_non_root_user(
        self, db, api_client, oauth_root_client, auth_user, config
    ):
        # Even with user read permissions, the root user can't be queried
        scopes = [USER_PERMISSION_READ]
        ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
            scopes=scopes,
            user_id=auth_user.id,
        )

        auth_header = generate_auth_header_for_user(auth_user, scopes, config)

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{oauth_root_client.user_id}/permission",
            headers=auth_header,
        )
        assert HTTP_404_NOT_FOUND == response.status_code

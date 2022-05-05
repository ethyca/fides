import pytest
import json
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
)

from fidesops.api.v1.urn_registry import V1_URL_PREFIX, USER_PERMISSIONS
from fidesops.api.v1.scope_registry import (
    USER_PERMISSION_CREATE,
    USER_PERMISSION_READ,
    USER_PERMISSION_UPDATE,
    SAAS_CONFIG_READ,
    PRIVACY_REQUEST_READ,
)
from fidesops.models.client import ClientDetail
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.fidesops_user_permissions import FidesopsUserPermissions


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
        user = FidesopsUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"user_id": user.id, "scopes": ["not a real scope"]}

        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
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
        permissions = FidesopsUserPermissions.get_by(db, field="user_id", value=user_id)
        assert HTTP_404_NOT_FOUND == response.status_code
        assert permissions is None

    def test_create_user_permissions(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_CREATE])
        user = FidesopsUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        body = {"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        response = api_client.post(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        permissions = FidesopsUserPermissions.get_by(db, field="user_id", value=user.id)
        response_body = json.loads(response.text)
        assert HTTP_201_CREATED == response.status_code
        assert response_body["id"] == permissions.id
        assert permissions.scopes == [PRIVACY_REQUEST_READ]
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

        body = {"user_id": "bogus_user_id", "scopes": ["not a real scope"]}

        response = api_client.put(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code

    def test_edit_user_permissions_invalid_user_id(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        invalid_user_id = "bogus_user_id"
        user = FidesopsUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesopsUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )
        body = {"id": permissions.id, "scopes": [PRIVACY_REQUEST_READ]}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{invalid_user_id}/permission",
            headers=auth_header,
            json=body,
        )
        permissions = FidesopsUserPermissions.get_by(
            db, field="user_id", value=invalid_user_id
        )
        assert HTTP_404_NOT_FOUND == response.status_code
        assert permissions is None
        user.delete(db)

    def test_edit_user_permissions(self, db, api_client, generate_auth_header) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_UPDATE])
        user = FidesopsUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesopsUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )

        ClientDetail.create_client_and_secret(
            db, [PRIVACY_REQUEST_READ], user_id=user.id
        )

        updated_scopes = [PRIVACY_REQUEST_READ, SAAS_CONFIG_READ]
        body = {"id": permissions.id, "scopes": updated_scopes}
        response = api_client.put(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header, json=body
        )
        response_body = json.loads(response.text)
        client: ClientDetail = ClientDetail.get_by(db, field="user_id", value=user.id)
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == permissions.id
        assert response_body["scopes"] == updated_scopes
        assert client.scopes == updated_scopes

        user.delete(db)


class TestGetUserPermissions:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + USER_PERMISSIONS

    def test_get_user_permissions_not_authenticated(self, url, api_client):
        response = api_client.get(url, headers={}, json={})
        assert HTTP_401_UNAUTHORIZED == response.status_code

    def test_get_user_permissions_wrong_scope(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header([SAAS_CONFIG_READ])
        response = api_client.get(url, headers=auth_header, json={})
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_get_user_permissions_invalid_user_id(
        self, db, api_client, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_READ])
        invalid_user_id = "bogus_user_id"
        user = FidesopsUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions = FidesopsUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )
        body = {"id": permissions.id, "scopes": [PRIVACY_REQUEST_READ]}
        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{invalid_user_id}/permission",
            headers=auth_header,
            json=body,
        )
        permissions = FidesopsUserPermissions.get_by(
            db, field="user_id", value=invalid_user_id
        )
        assert HTTP_404_NOT_FOUND == response.status_code
        assert permissions is None
        user.delete(db)

    def test_get_user_permissions(self, db, api_client, generate_auth_header) -> None:
        auth_header = generate_auth_header([USER_PERMISSION_READ])
        user = FidesopsUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )
        permissions = FidesopsUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )

        response = api_client.get(
            f"{V1_URL_PREFIX}/user/{user.id}/permission", headers=auth_header
        )
        response_body = json.loads(response.text)
        assert HTTP_200_OK == response.status_code
        assert response_body["id"] == permissions.id
        assert response_body["user_id"] == user.id
        assert response_body["scopes"] == [PRIVACY_REQUEST_READ]
        user.delete(db)

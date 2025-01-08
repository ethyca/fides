import json
from datetime import datetime, timedelta
from unittest import mock
from uuid import uuid4

import pytest
from fastapi_pagination import Params
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from starlette.testclient import TestClient

from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
)
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_invite import INVITE_CODE_TTL_HOURS, FidesUserInvite
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.oauth.jwt import generate_jwe
from fides.api.oauth.roles import APPROVER, CONTRIBUTOR, OWNER, VIEWER
from fides.api.oauth.utils import extract_payload
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_READ,
    SCOPE_REGISTRY,
    STORAGE_READ,
    SYSTEM_MANAGER_DELETE,
    SYSTEM_MANAGER_READ,
    SYSTEM_MANAGER_UPDATE,
    USER_CREATE,
    USER_DELETE,
    USER_PASSWORD_RESET,
    USER_READ,
    USER_UPDATE,
)
from fides.common.api.v1.urn_registry import (
    LOGIN,
    LOGOUT,
    USER_ACCEPT_INVITE,
    USER_DETAIL,
    USERS,
    V1_URL_PREFIX,
)
from fides.config import CONFIG
from tests.conftest import generate_auth_header_for_user
from tests.ops.api.v1.endpoints.test_privacy_request_endpoints import stringify_date

page_size = Params().size


class TestCreateUser:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + USERS

    def test_create_user_not_authenticated(self, url, api_client):
        response = api_client.post(url, headers={}, json={})
        assert HTTP_401_UNAUTHORIZED == response.status_code

    def test_create_user_wrong_scope(self, url, api_client, generate_auth_header):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.post(url, headers=auth_header, json={})
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_create_user_bad_username(
        self,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {
            "username": "spaces in name",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code

    def test_username_exists(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])

        body = {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user@ethyca.com",
        }

        FidesUser.create(db=db, data=body)

        response = api_client.post(url, headers=auth_header, json=body)
        response_body = response.json()
        assert response_body["detail"] == "Username already exists."
        assert HTTP_400_BAD_REQUEST == response.status_code

    def test_create_user_bad_password(
        self,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])

        body = {
            "username": "test_user",
            "password": str_to_b64_str("short"),
            "email_address": "test.user@ethyca.com",
        }
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            response.json()["detail"][0]["msg"]
            == "Value error, Password must have at least eight characters."
        )

        body = {
            "username": "test_user",
            "password": str_to_b64_str("longerpassword"),
            "email_address": "test.user@ethyca.com",
        }
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            response.json()["detail"][0]["msg"]
            == "Value error, Password must have at least one number."
        )

        body = {
            "username": "test_user",
            "password": str_to_b64_str("longer55password"),
            "email_address": "test.user@ethyca.com",
        }
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            response.json()["detail"][0]["msg"]
            == "Value error, Password must have at least one capital letter."
        )

        body = {
            "username": "test_user",
            "password": str_to_b64_str("LoNgEr55paSSworD"),
            "email_address": "test.user@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            response.json()["detail"][0]["msg"]
            == "Value error, Password must have at least one symbol."
        )

        # Tests request_validation_exception_handler which removes the user input
        # and the pydantic url from the response. We don't want to reflect a password
        # back in the response
        assert "input" not in response.json()["detail"][0]
        assert "url" not in response.json()["detail"][0]
        assert "ctx" not in response.json()["detail"][0]

    def test_create_user_no_email(
        self,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])

        body = {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
        }
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code

    def test_create_user_bad_email(
        self,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])

        body = {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "not.an.email",
        }
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code

    def test_create_user(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=body)

        user = FidesUser.get_by(db, field="username", value=body["username"])
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body == {"id": user.id}
        assert user.permissions is not None
        assert user.permissions.roles == [
            VIEWER
        ], "User given viewer role by default on create"

    def test_underscore_in_password(
        self,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {
            "username": "test_user",
            "password": str_to_b64_str("Test_passw0rd"),
            "email_address": "test.user@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=body)

        assert HTTP_201_CREATED == response.status_code

    def test_create_user_as_root(
        self,
        db,
        api_client,
        root_auth_header,
        url,
    ) -> None:
        auth_header = root_auth_header
        body = {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=body)

        user = FidesUser.get_by(db, field="username", value=body["username"])
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body == {"id": user.id}
        assert user.permissions is not None

    def test_create_user_with_name(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user@ethyca.com",
            "first_name": "Test",
            "last_name": "User",
        }

        response = api_client.post(url, headers=auth_header, json=body)

        user = FidesUser.get_by(db, field="username", value=body["username"])
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body == {"id": user.id}
        assert user.permissions is not None

    def test_cannot_create_duplicate_user(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=body)

        user = FidesUser.get_by(db, field="username", value=body["username"])
        response_body = response.json()
        assert HTTP_201_CREATED == response.status_code
        assert response_body == {"id": user.id}
        assert user.permissions is not None

        duplicate_body = {
            "username": "TEST_USER",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user1@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=duplicate_body)
        assert HTTP_400_BAD_REQUEST == response.status_code
        assert response.json()["detail"] == "Username already exists."

        duplicate_body_2 = {
            "username": "TEST_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user2@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=duplicate_body_2)
        assert HTTP_400_BAD_REQUEST == response.status_code
        assert response.json()["detail"] == "Username already exists."

    def test_cannot_create_duplicate_user_email(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=body)

        user = FidesUser.get_by(db, field="username", value=body["username"])
        assert HTTP_201_CREATED == response.status_code
        assert response.json() == {"id": user.id}
        assert user.permissions is not None

        duplicate_body = {
            "username": "test_user2",
            "password": str_to_b64_str("TestP@ssword9"),
            "email_address": "test.user@ethyca.com",
        }

        response = api_client.post(url, headers=auth_header, json=duplicate_body)
        assert (
            response.json()["detail"] == "User with this email address already exists."
        )
        assert HTTP_400_BAD_REQUEST == response.status_code


class TestDeleteUser:
    @pytest.fixture(scope="function")
    def url(self, user) -> str:
        return f"{V1_URL_PREFIX}{USERS}/{user.id}"

    def test_delete_user_not_authenticated(self, url, api_client):
        response = api_client.delete(url, headers={})
        assert HTTP_401_UNAUTHORIZED == response.status_code

    def test_create_user_wrong_scope(self, url, api_client, generate_auth_header):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.delete(url, headers=auth_header)
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_delete_nonexistent_user(self, api_client, db, generate_auth_header):
        auth_header = generate_auth_header([USER_DELETE])
        url = f"{V1_URL_PREFIX}{USERS}/nonexistent_user"
        response = api_client.delete(url, headers=auth_header)
        assert HTTP_404_NOT_FOUND == response.status_code

    def test_delete_self(self, api_client, db):
        user = FidesUser.create(
            db=db,
            data={
                "username": "test_delete_user",
                "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
                "email_address": "test2.user@ethyca.com",
            },
        )
        saved_user_id = user.id

        FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "roles": [APPROVER]}
        )

        assert user.permissions is not None
        saved_permissions_id = user.permissions.id

        client, _ = ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=[USER_DELETE],
            user_id=user.id,
        )
        assert client.user == user
        saved_client_id = client.id

        payload = {
            JWE_PAYLOAD_SCOPES: [USER_DELETE],
            JWE_PAYLOAD_CLIENT_ID: client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        auth_header = {"Authorization": "Bearer " + jwe}

        response = api_client.delete(
            f"{V1_URL_PREFIX}{USERS}/{user.id}", headers=auth_header
        )
        assert HTTP_204_NO_CONTENT == response.status_code

        db.expunge_all()

        user_search = FidesUser.get_by(db, field="id", value=saved_user_id)
        assert user_search is None

        client_search = ClientDetail.get_by(db, field="id", value=saved_client_id)
        assert client_search is None

        permissions_search = FidesUserPermissions.get_by(
            db, field="id", value=saved_permissions_id
        )
        assert permissions_search is None

    def test_delete_user(self, api_client, db):
        user = FidesUser.create(
            db=db,
            data={
                "username": "test_delete_user",
                "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
                "email_address": "test.user@ethyca.com",
            },
        )

        FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "roles": [CONTRIBUTOR]}
        )

        other_user = FidesUser.create(
            db=db,
            data={
                "username": "user_to_delete",
                "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
                "email_address": "other.user@ethyca.com",
            },
        )

        saved_user_id = other_user.id

        FidesUserPermissions.create(
            db=db, data={"user_id": other_user.id, "roles": [APPROVER]}
        )

        assert other_user.permissions is not None
        saved_permissions_id = other_user.permissions.id

        client, _ = ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            roles=[CONTRIBUTOR],
            user_id=user.id,
        )

        other_user_client, _ = ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            roles=[APPROVER],
            user_id=other_user.id,
        )

        assert other_user_client.user == other_user
        saved_client_id = other_user_client.id

        payload = {
            JWE_PAYLOAD_ROLES: [CONTRIBUTOR],
            JWE_PAYLOAD_CLIENT_ID: client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        auth_header = {"Authorization": "Bearer " + jwe}

        response = api_client.delete(
            f"{V1_URL_PREFIX}{USERS}/{other_user.id}", headers=auth_header
        )
        assert HTTP_204_NO_CONTENT == response.status_code

        db.expunge_all()

        user_search = FidesUser.get_by(db, field="id", value=saved_user_id)
        assert user_search is None

        client_search = ClientDetail.get_by(db, field="id", value=saved_client_id)
        assert client_search is None

        permissions_search = FidesUserPermissions.get_by(
            db, field="id", value=saved_permissions_id
        )
        assert permissions_search is None

    def test_delete_user_as_root(self, api_client, db, user, root_auth_header):
        other_user = FidesUser.create(
            db=db,
            data={
                "username": "test_delete_user",
                "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
                "email_address": "test.user@ethyca.com",
            },
        )

        FidesUserPermissions.create(
            db=db, data={"user_id": other_user.id, "roles": [APPROVER]}
        )
        saved_user_id = other_user.id
        saved_permission_id = other_user.permissions.id

        user_client, _ = ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
            scopes=[USER_DELETE],
            user_id=other_user.id,
        )
        client_id = user_client.id

        response = api_client.delete(
            f"{V1_URL_PREFIX}{USERS}/{other_user.id}", headers=root_auth_header
        )
        assert HTTP_204_NO_CONTENT == response.status_code

        db.expunge_all()

        user_search = FidesUser.get_by(db, field="id", value=saved_user_id)
        assert user_search is None

        # Deleted user's client is also deleted
        client_search = ClientDetail.get_by(db, field="id", value=client_id)
        assert client_search is None

        permissions_search = FidesUserPermissions.get_by(
            db, field="id", value=saved_permission_id
        )
        assert permissions_search is None


class TestGetUsers:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + USERS

    def test_get_users_not_authenticated(
        self, api_client: TestClient, url: str
    ) -> None:
        resp = api_client.get(url, headers={})
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_get_users_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[USER_DELETE])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_get_users_no_users(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[USER_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = resp.json()
        assert len(response_body["items"]) == 0
        assert response_body["total"] == 0
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

    def test_get_users(self, api_client: TestClient, generate_auth_header, url, db):
        total_users = 25
        password = str_to_b64_str("Password123!")
        [
            FidesUser.create(
                db=db,
                data={
                    "username": f"user{i}",
                    "password": password,
                    "email_address": f"test{i}.user@ethyca.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            for i in range(total_users)
        ]

        get_auth_header = generate_auth_header(scopes=[USER_READ])
        resp = api_client.get(url, headers=get_auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = resp.json()
        assert len(response_body["items"]) == total_users
        assert response_body["total"] == total_users
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

        user_data = response_body["items"][0]
        assert user_data["username"]
        assert user_data["id"]
        assert user_data["created_at"]
        assert user_data["first_name"]
        assert user_data["last_name"]
        assert user_data["email_address"]
        assert user_data["disabled"] == False

    def test_get_filtered_users(
        self, api_client: TestClient, generate_auth_header, url, db
    ):
        total_users = 50
        password = str_to_b64_str("Password123!")
        [
            FidesUser.create(
                db=db,
                data={
                    "username": f"user{i}",
                    "password": password,
                    "email_address": f"test{i}.user@ethyca.com",
                },
            )
            for i in range(total_users)
        ]

        get_auth_header = generate_auth_header(scopes=[USER_READ])

        resp = api_client.get(f"{url}?username={15}", headers=get_auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = resp.json()
        assert len(response_body["items"]) == 1
        assert response_body["total"] == 1
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

        resp = api_client.get(f"{url}?username={5}", headers=get_auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = resp.json()
        assert len(response_body["items"]) == 5
        assert response_body["total"] == 5
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

        resp = api_client.get(f"{url}?username=not real user", headers=get_auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = resp.json()
        assert len(response_body["items"]) == 0
        assert response_body["total"] == 0
        assert response_body["page"] == 1
        assert response_body["size"] == page_size


class TestGetUser:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + USER_DETAIL

    @pytest.fixture(scope="function")
    def url_no_id(self) -> str:
        return V1_URL_PREFIX + USERS

    def test_get_user_not_authenticated(self, api_client: TestClient, url: str) -> None:
        resp = api_client.get(url, headers={})
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_get_user_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url: str
    ):
        auth_header = generate_auth_header(scopes=[USER_DELETE])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_get_user_does_not_exist(
        self, api_client: TestClient, generate_auth_header, url_no_id: str
    ) -> None:
        auth_header = generate_auth_header(scopes=[USER_READ])
        resp = api_client.get(
            f"{url_no_id}/this_is_a_nonexistent_key",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND

    def test_get_user(
        self,
        api_client: TestClient,
        generate_auth_header,
        url_no_id: str,
        application_user,
    ) -> None:
        auth_header = generate_auth_header(scopes=[USER_READ])
        resp = api_client.get(
            f"{url_no_id}/{application_user.id}",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_200_OK
        user_data = resp.json()
        assert user_data["username"] == application_user.username
        assert user_data["id"] == application_user.id
        assert user_data["created_at"] == stringify_date(application_user.created_at)
        assert user_data["first_name"] == application_user.first_name
        assert user_data["last_name"] == application_user.last_name


class TestUpdateUser:
    @pytest.fixture(scope="function")
    def url_no_id(self) -> str:
        return V1_URL_PREFIX + USERS

    def test_update_different_users_names(
        self,
        api_client,
        url_no_id,
        user,
        application_user,
    ) -> None:
        NEW_FIRST_NAME = "another"
        NEW_LAST_NAME = "name"

        auth_header = generate_auth_header_for_user(
            user=application_user,
            scopes=[USER_UPDATE],
        )
        resp = api_client.put(
            f"{url_no_id}/{user.id}",
            headers=auth_header,
            json={
                "first_name": NEW_FIRST_NAME,
                "last_name": NEW_LAST_NAME,
            },
        )
        assert resp.status_code == HTTP_200_OK
        user_data = resp.json()
        assert user_data["username"] == user.username
        assert user_data["id"] == user.id
        assert user_data["created_at"] == stringify_date(user.created_at)
        assert user_data["first_name"] == NEW_FIRST_NAME
        assert user_data["last_name"] == NEW_LAST_NAME

    def test_update_user_names(
        self,
        api_client,
        url_no_id,
        application_user,
    ) -> None:
        NEW_FIRST_NAME = "another"
        NEW_LAST_NAME = "name"

        auth_header = generate_auth_header_for_user(
            user=application_user,
            scopes=[USER_UPDATE],
        )
        resp = api_client.put(
            f"{url_no_id}/{application_user.id}",
            headers=auth_header,
            json={
                "first_name": NEW_FIRST_NAME,
                "last_name": NEW_LAST_NAME,
            },
        )
        assert resp.status_code == HTTP_200_OK
        user_data = resp.json()
        assert user_data["username"] == application_user.username
        assert user_data["id"] == application_user.id
        assert user_data["created_at"] == stringify_date(application_user.created_at)
        assert user_data["first_name"] == NEW_FIRST_NAME
        assert user_data["last_name"] == NEW_LAST_NAME

    def test_user_cannot_update_different_name_without_scope(
        self, api_client, url_no_id, user, application_user
    ) -> None:
        NEW_FIRST_NAME = "another"
        NEW_LAST_NAME = "name"

        auth_header = generate_auth_header_for_user(
            user=application_user,
            scopes=[],
        )
        resp = api_client.put(
            f"{url_no_id}/{user.id}",
            headers=auth_header,
            json={
                "first_name": NEW_FIRST_NAME,
                "last_name": NEW_LAST_NAME,
            },
        )
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_user_can_update_their_own_name_without_scope(
        self, api_client, url_no_id, application_user
    ) -> None:
        NEW_FIRST_NAME = "another"
        NEW_LAST_NAME = "name"

        auth_header = generate_auth_header_for_user(
            user=application_user,
            scopes=[],
        )
        resp = api_client.put(
            f"{url_no_id}/{application_user.id}",
            headers=auth_header,
            json={
                "first_name": NEW_FIRST_NAME,
                "last_name": NEW_LAST_NAME,
            },
        )
        assert resp.status_code == HTTP_200_OK
        user_data = resp.json()
        assert user_data["username"] == application_user.username
        assert user_data["id"] == application_user.id
        assert user_data["created_at"] == stringify_date(application_user.created_at)
        assert user_data["first_name"] == NEW_FIRST_NAME
        assert user_data["last_name"] == NEW_LAST_NAME


class TestUpdateUserPassword:
    @pytest.fixture(scope="function")
    def url_no_id(self) -> str:
        return V1_URL_PREFIX + USERS

    def test_update_different_user_password(
        self,
        api_client,
        db,
        url_no_id,
        user,
        application_user,
    ) -> None:
        OLD_PASSWORD = "oldpassword"
        NEW_PASSWORD = "Newpassword1!"
        application_user.update_password(db=db, new_password=OLD_PASSWORD)

        auth_header = generate_auth_header_for_user(user=application_user, scopes=[])
        resp = api_client.post(
            f"{url_no_id}/{user.id}/reset-password",
            headers=auth_header,
            json={
                "old_password": str_to_b64_str(OLD_PASSWORD),
                "new_password": str_to_b64_str(NEW_PASSWORD),
            },
        )
        assert resp.status_code == HTTP_401_UNAUTHORIZED
        assert (
            resp.json()["detail"]
            == "You are only authorised to update your own user data."
        )

        db.expunge(application_user)
        application_user = application_user.refresh_from_db(db=db)
        assert application_user.credentials_valid(password=OLD_PASSWORD)

    def test_update_user_password_invalid_old_password(
        self,
        api_client,
        db,
        url_no_id,
        application_user,
    ) -> None:
        OLD_PASSWORD = "oldpassword"
        NEW_PASSWORD = "Newpassword1!"
        application_user.update_password(db=db, new_password=OLD_PASSWORD)

        auth_header = generate_auth_header_for_user(user=application_user, scopes=[])
        resp = api_client.post(
            f"{url_no_id}/{application_user.id}/reset-password",
            headers=auth_header,
            json={
                "old_password": str_to_b64_str("mismatching password"),
                "new_password": str_to_b64_str(NEW_PASSWORD),
            },
        )
        assert resp.status_code == HTTP_401_UNAUTHORIZED
        assert resp.json()["detail"] == "Incorrect password."

        db.expunge(application_user)
        application_user = application_user.refresh_from_db(db=db)
        assert application_user.credentials_valid(password=OLD_PASSWORD)

    def test_update_user_password(
        self,
        api_client,
        db,
        url_no_id,
        application_user,
    ) -> None:
        OLD_PASSWORD = "oldpassword"
        NEW_PASSWORD = "Newpassword1!"
        application_user.update_password(db=db, new_password=OLD_PASSWORD)
        auth_header = generate_auth_header_for_user(user=application_user, scopes=[])
        resp = api_client.post(
            f"{url_no_id}/{application_user.id}/reset-password",
            headers=auth_header,
            json={
                "old_password": str_to_b64_str(OLD_PASSWORD),
                "new_password": str_to_b64_str(NEW_PASSWORD),
            },
        )
        assert resp.status_code == HTTP_200_OK
        db.expunge(application_user)
        application_user = application_user.refresh_from_db(db=db)
        assert application_user.credentials_valid(password=NEW_PASSWORD)

    def test_force_update_different_user_password_without_scope(
        self,
        api_client,
        db,
        url_no_id,
        user,
        application_user,
    ) -> None:
        """A user without the proper scope cannot change another user's password"""
        NEW_PASSWORD = "Newpassword1!"
        old_hashed_password = user.hashed_password

        auth_header = generate_auth_header_for_user(user=application_user, scopes=[])
        resp = api_client.post(
            f"{url_no_id}/{user.id}/force-reset-password",
            headers=auth_header,
            json={
                "new_password": str_to_b64_str(NEW_PASSWORD),
            },
        )
        assert resp.status_code == HTTP_403_FORBIDDEN

        db.expunge(user)
        user = user.refresh_from_db(db=db)
        assert (
            user.hashed_password == old_hashed_password
        ), "Password changed on the user"

    def test_force_update_different_user_password(
        self,
        api_client,
        db,
        url_no_id,
        user,
        application_user,
    ) -> None:
        """
        A user with the right scope should be able to set a new password
        for another user.
        """
        NEW_PASSWORD = "Newpassword1!"
        auth_header = generate_auth_header_for_user(
            user=application_user, scopes=[USER_PASSWORD_RESET]
        )
        resp = api_client.post(
            f"{url_no_id}/{user.id}/force-reset-password",
            headers=auth_header,
            json={
                "new_password": str_to_b64_str(NEW_PASSWORD),
            },
        )

        assert resp.status_code == HTTP_200_OK
        db.expunge(user)
        user = user.refresh_from_db(db=db)
        assert user.credentials_valid(password=NEW_PASSWORD)

    @pytest.mark.parametrize(
        "new_password, expected_error",
        [
            ("short", "Value error, Password must have at least eight characters."),
            ("longerpassword", "Value error, Password must have at least one number."),
            (
                "longer55password",
                "Value error, Password must have at least one capital letter.",
            ),
            (
                "LONGER55PASSWORD",
                "Value error, Password must have at least one lowercase letter.",
            ),
            (
                "LoNgEr55paSSworD",
                "Value error, Password must have at least one symbol.",
            ),
        ],
    )
    def test_force_update_bad_password(
        self,
        api_client,
        db,
        url_no_id,
        user,
        application_user,
        new_password,
        expected_error,
    ) -> None:
        """
        A user with the right scope should be able to set a new password
        for another user.
        """
        auth_header = generate_auth_header_for_user(
            user=application_user, scopes=[USER_PASSWORD_RESET]
        )

        resp = api_client.post(
            f"{url_no_id}/{user.id}/force-reset-password",
            headers=auth_header,
            json={
                "new_password": str_to_b64_str(new_password),
            },
        )

        assert resp.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert expected_error in resp.json()["detail"][0]["msg"]
        db.expunge(user)

    def test_force_update_non_existent_user(
        self,
        api_client,
        url_no_id,
        application_user,
    ) -> None:
        """
        Resetting on a user that does not exist should 404
        """
        NEW_PASSWORD = "Newpassword1!"
        auth_header = generate_auth_header_for_user(
            user=application_user, scopes=[USER_PASSWORD_RESET]
        )
        # arbitrary id that isn't the user's
        user_id = "fake_user_id"
        resp = api_client.post(
            f"{url_no_id}/{user_id}/force-reset-password",
            headers=auth_header,
            json={
                "new_password": str_to_b64_str(NEW_PASSWORD),
            },
        )

        assert resp.status_code == HTTP_404_NOT_FOUND


class TestUserLogin:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + LOGIN

    def test_user_does_not_exist(self, db, url, api_client):
        body = {
            "username": "does not exist",
            "password": str_to_b64_str("idonotknowmypassword"),
        }
        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_403_FORBIDDEN

        user = FidesUser.get_by(db, field="username", value=body["username"])
        assert user is None

        # The temporary resources created to parallelize operations between the invalid
        # and valid flow do not get persisted
        user = FidesUser.get_by(db, field="username", value="temp_user")
        assert user is None

        user_perms = FidesUserPermissions.get_by(db, field="id", value="temp_user_id")
        assert user_perms is None

        client_search = ClientDetail.get_by(db, field="id", value="temp_user_id")
        assert client_search is None

    def test_bad_login(self, url, user, api_client):
        body = {
            "username": user.username,
            "password": str_to_b64_str("idonotknowmypassword"),
        }
        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_403_FORBIDDEN

    def test_login_creates_client(self, db, url, user, api_client):
        # Delete existing client for test purposes
        user.client.delete(db)
        body = {
            "username": user.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        assert user.client is None  # client does not exist
        assert user.permissions is not None
        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        db.refresh(user)
        assert user.client is not None
        assert "token_data" in list(response.json().keys())
        token = response.json()["token_data"]["access_token"]
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
        assert token_data["client-id"] == user.client.id
        assert token_data["scopes"] == []  # Uses scopes on existing client

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == user.id

    def test_login_with_scopes(self, db, url, user, api_client):
        # Delete existing client for test purposes
        user.client.delete(db)
        body = {
            "username": user.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        assert user.client is None  # client does not exist
        assert user.permissions is not None
        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        db.refresh(user)
        assert user.client is not None
        assert "token_data" in list(response.json().keys())
        token = response.json()["token_data"]["access_token"]
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
        assert token_data["client-id"] == user.client.id
        assert token_data["scopes"] == []
        assert token_data["roles"] == [APPROVER]

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == user.id

    def test_login_with_roles(self, db, url, viewer_user, api_client):
        # Delete existing client for test purposes
        viewer_user.client.delete(db)
        body = {
            "username": viewer_user.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        assert viewer_user.client is None  # client does not exist
        assert viewer_user.permissions is not None
        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        db.refresh(viewer_user)
        assert viewer_user.client is not None
        assert "token_data" in list(response.json().keys())
        token = response.json()["token_data"]["access_token"]
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
        assert token_data["client-id"] == viewer_user.client.id
        assert token_data["scopes"] == []  # Uses scopes on existing client
        assert token_data["roles"] == [VIEWER]  # Uses roles on existing client

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == viewer_user.id

    def test_login_with_systems(self, db, url, system_manager, api_client, system):
        # Delete existing client for test purposes
        system_manager.client.delete(db)
        body = {
            "username": system_manager.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        assert system_manager.client is None  # client does not exist
        assert system_manager.permissions is not None
        assert system_manager.system_ids == [system.id]

        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        db.refresh(system_manager)
        assert system_manager.client is not None
        assert "token_data" in list(response.json().keys())
        token = response.json()["token_data"]["access_token"]
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
        assert token_data["client-id"] == system_manager.client.id
        assert token_data["scopes"] == []  # Uses scopes on existing client
        assert token_data["roles"] == [VIEWER]  # Uses roles on existing client
        assert token_data["systems"] == [system.id]

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == system_manager.id

    def test_login_after_system_deleted(
        self, db, url, system_manager, api_client, system
    ):
        """Test that client is updated on login just in case.  A system delete doesn't update the client.
        There could be other direct-db updates that didn't persist to the client.
        """
        assert system_manager.client
        assert system_manager.client.systems == [system.id]
        assert system_manager.system_ids == [system.id]

        system_manager.permissions.roles = [VIEWER]
        system_manager.save(db=db)

        db.delete(system)
        db.commit()

        body = {
            "username": system_manager.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        db.refresh(system_manager)
        assert system_manager.client is not None
        assert "token_data" in list(response.json().keys())
        token = response.json()["token_data"]["access_token"]
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
        assert token_data["client-id"] == system_manager.client.id
        assert token_data["scopes"] == []  # Uses scopes on existing client
        assert token_data["roles"] == [VIEWER]  # Uses roles on existing client
        assert token_data["systems"] == []

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == system_manager.id

    def test_login_with_no_permissions(self, db, url, viewer_user, api_client):
        viewer_user.permissions.roles = []
        viewer_user.save(db)  # Make sure user doesn't have roles or scopes

        assert viewer_user.permissions is not None
        body = {
            "username": viewer_user.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_403_FORBIDDEN

    def test_login_updates_last_login_date(self, db, url, user, api_client):
        body = {
            "username": user.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        db.refresh(user)
        assert user.last_login_at is not None

    def test_login_is_case_insensitive(
        self, url, user, api_client, generate_auth_header
    ):
        body = {
            "username": user.username.lower(),
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.post(V1_URL_PREFIX + LOGOUT, headers=auth_header, json={})
        assert HTTP_204_NO_CONTENT == response.status_code

        body = {
            "username": user.username.upper(),
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

    def test_login_uses_existing_client_with_scopes(self, db, url, user, api_client):
        body = {
            "username": user.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        existing_client_id = user.client.id
        user.client.scopes = [PRIVACY_REQUEST_READ]
        user.client.save(db)
        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        db.refresh(user)
        assert user.client is not None
        assert "token_data" in list(response.json().keys())
        token = response.json()["token_data"]["access_token"]
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
        assert token_data["client-id"] == existing_client_id
        assert token_data["scopes"] == [
            PRIVACY_REQUEST_READ
        ]  # Uses scopes on existing client

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == user.id

    def test_login_uses_existing_client_with_roles(self, url, owner_user, api_client):
        body = {
            "username": owner_user.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        existing_client_id = owner_user.client.id
        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        assert owner_user.client is not None
        assert "token_data" in list(response.json().keys())
        token = response.json()["token_data"]["access_token"]
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
        assert token_data["client-id"] == existing_client_id
        assert token_data["scopes"] == []
        assert token_data["roles"] == [OWNER]  # Uses roles on existing client

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == owner_user.id

    def test_login_as_root_user(self, api_client, url):
        body = {
            "username": CONFIG.security.root_username,
            "password": str_to_b64_str(CONFIG.security.root_password),
        }

        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        assert "token_data" in list(response.json().keys())
        token = response.json()["token_data"]["access_token"]
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
        assert token_data["client-id"] == CONFIG.security.oauth_root_client_id
        assert token_data["scopes"] == SCOPE_REGISTRY  # Uses all scopes
        assert token_data["roles"] == [OWNER]  # Uses owner role

        assert "user_data" in list(response.json().keys())
        data = response.json()["user_data"]
        assert data["username"] == CONFIG.security.root_username
        assert data["id"] == CONFIG.security.oauth_root_client_id


class TestUserLogout:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + LOGOUT

    def test_malformed_token_ignored(self, url, api_client):
        auth_header = {"Authorization": "Bearer invalid"}
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == HTTP_204_NO_CONTENT

    def test_user_can_logout_with_expired_token(self, db, url, api_client, user):
        client_id = user.client.id
        scopes = user.client.scopes

        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: (datetime.now() - timedelta(days=360)).isoformat(),
        }

        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == HTTP_204_NO_CONTENT

        # Verify client was deleted
        client_search = ClientDetail.get_by(db, field="id", value=client_id)
        assert client_search is None

    def test_root_user_logout(self, url, api_client):
        payload = {
            JWE_PAYLOAD_SCOPES: SCOPE_REGISTRY,
            JWE_PAYLOAD_CLIENT_ID: CONFIG.security.oauth_root_client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == HTTP_204_NO_CONTENT

    def test_user_not_deleted_on_logout(self, db, url, api_client, user):
        user_id = user.id
        client_id = user.client.id
        scopes = user.client.scopes

        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == HTTP_204_NO_CONTENT

        # Verify client was deleted
        client_search = ClientDetail.get_by(db, field="id", value=client_id)
        assert client_search is None

        # Assert user is not deleted
        user_search = FidesUser.get_by(db, field="id", value=user_id)
        db.refresh(user_search)
        assert user_search is not None

        # Assert user permissions are not deleted
        permission_search = FidesUserPermissions.get_by(
            db, field="user_id", value=user_id
        )
        assert permission_search is not None

        # Assert user does not still have client reference
        assert user_search.client is None

        # Outdated client token logout gives a 204
        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert HTTP_204_NO_CONTENT == response.status_code

    def test_logout(self, db, url, api_client, generate_auth_header, oauth_client):
        oauth_client_id = oauth_client.id
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.post(url, headers=auth_header, json={})
        assert HTTP_204_NO_CONTENT == response.status_code

        # Verify client was deleted
        client_search = ClientDetail.get_by(db, field="id", value=oauth_client_id)
        assert client_search is None

        # Even though client doesn't exist, we still return a 204
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == HTTP_204_NO_CONTENT


class TestUpdateSystemsManagedByUser:
    @pytest.fixture(scope="function")
    def url(self, viewer_user) -> str:
        return V1_URL_PREFIX + f"/user/{viewer_user.id}/system-manager"

    def test_update_system_manager_not_authenticated(
        self, api_client: TestClient, url: str
    ) -> None:
        resp = api_client.put(url, headers={})
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_update_system_manager_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.put(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_update_system_manager_user_not_found(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(
            V1_URL_PREFIX + f"/user/bad_user/system-manager",
            headers=auth_header,
            json=["bad_fides_key"],
        )
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert resp.json()["detail"] == f"No user found with id bad_user."

    def test_update_system_manager_system_not_found(
        self, api_client: TestClient, generate_auth_header, url, viewer_user
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(url, headers=auth_header, json=["bad_fides_key"])
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert (
            resp.json()["detail"]
            == f"Cannot add user {viewer_user.id} as system manager. System(s) not found."
        )

    def test_update_system_manager_dupe_systems_in_request(
        self, api_client: TestClient, generate_auth_header, url, system, viewer_user
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(
            url, headers=auth_header, json=[system.fides_key, system.fides_key]
        )
        assert resp.status_code == HTTP_400_BAD_REQUEST
        assert (
            resp.json()["detail"]
            == f"Cannot add user {viewer_user.id} as system manager. Duplicate systems in request body."
        )

    def test_users_need_permissions_object_before_they_can_be_a_system_manager(
        self, db, api_client: TestClient, generate_auth_header, system
    ):
        new_user = FidesUser.create(
            db=db,
            data={
                "username": "test_new_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
                "email_address": "test.user@ethyca.com",
            },
        )
        url = V1_URL_PREFIX + f"/user/{new_user.id}/system-manager"
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(url, headers=auth_header, json=[system.fides_key])
        assert resp.status_code == HTTP_400_BAD_REQUEST
        assert (
            resp.json()["detail"]
            == f"User {new_user.id} needs permissions before they can be assigned as system manager."
        )
        db.refresh(new_user)
        assert new_user.systems == []

    def test_users_need_roles_before_they_can_be_a_system_manager(
        self, db, api_client: TestClient, generate_auth_header, system
    ):
        new_user = FidesUser.create(
            db=db,
            data={
                "username": "test_new_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
                "email_address": "test.user@ethyca.com",
            },
        )

        FidesUserPermissions.create(db=db, data={"user_id": new_user.id, "roles": []})
        url = V1_URL_PREFIX + f"/user/{new_user.id}/system-manager"
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(url, headers=auth_header, json=[system.fides_key])
        assert resp.status_code == HTTP_400_BAD_REQUEST
        assert (
            resp.json()["detail"]
            == f"User {new_user.id} needs permissions before they can be assigned as system manager."
        )
        db.refresh(new_user)
        assert new_user.systems == []

    def test_add_an_approver_as_system_manager(
        self, db, api_client: TestClient, generate_auth_header, system, approver_user
    ):
        url = V1_URL_PREFIX + f"/user/{approver_user.id}/system-manager"

        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(url, headers=auth_header, json=[system.fides_key])
        assert resp.status_code == HTTP_400_BAD_REQUEST
        assert (
            resp.json()["detail"]
            == f"User {approver_user.id} is an approver and cannot be assigned as a system manager."
        )

        db.refresh(approver_user)
        assert approver_user.systems == []

    def test_update_system_manager(
        self, api_client: TestClient, generate_auth_header, url, system, viewer_user, db
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(url, headers=auth_header, json=[system.fides_key])
        assert resp.status_code == HTTP_200_OK
        response_body = resp.json()
        assert len(response_body) == 1
        assert response_body[0]["fides_key"] == system.fides_key

        db.refresh(viewer_user)
        assert viewer_user.systems == [system]

    def test_update_system_manager_user_is_already_a_manager(
        self, api_client: TestClient, generate_auth_header, url, system, viewer_user, db
    ) -> None:
        assert viewer_user.systems == []
        viewer_user.set_as_system_manager(db, system)
        assert viewer_user.systems == [system]

        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(url, headers=auth_header, json=[system.fides_key])
        assert resp.status_code == HTTP_200_OK
        response_body = resp.json()
        assert len(response_body) == 1
        assert response_body[0]["fides_key"] == system.fides_key

        db.refresh(viewer_user)
        assert viewer_user.systems == [system]

    @pytest.mark.usefixtures(
        "load_default_data_uses"
    )  # privacy declaration requires data uses to be present
    def test_update_system_manager_existing_system_not_in_request_which_removes_system(
        self, api_client: TestClient, generate_auth_header, url, system, viewer_user, db
    ) -> None:
        second_system = System.create(
            db=db,
            data={
                "fides_key": f"system_key-f{uuid4()}",
                "name": f"system-{uuid4()}",
                "description": "fixture-made-system",
                "organization_fides_key": "default_organization",
                "system_type": "Service",
            },
        )
        PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Collect data for marketing",
                "system_id": second_system.id,
                "data_categories": ["user.device.cookie_id"],
                "data_use": "marketing.advertising",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "egress": None,
                "ingress": None,
            },
        )
        db.refresh(second_system)

        assert viewer_user.systems == []
        viewer_user.set_as_system_manager(db, system)
        viewer_user.set_as_system_manager(db, second_system)
        assert viewer_user.systems == [system, second_system]

        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_UPDATE])
        resp = api_client.put(url, headers=auth_header, json=[])
        assert resp.status_code == HTTP_200_OK
        response_body = resp.json()
        assert len(response_body) == 0

        db.refresh(viewer_user)
        assert viewer_user.systems == []
        second_system.delete(db)


class TestGetSystemsUserManages:
    @pytest.fixture(scope="function")
    def url(self, viewer_user) -> str:
        return V1_URL_PREFIX + f"/user/{viewer_user.id}/system-manager"

    def test_get_systems_managed_by_user_not_authenticated(
        self, api_client: TestClient, url: str
    ) -> None:
        resp = api_client.get(url, headers={})
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_get_systems_managed_by_user_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        # Note no user attached to this client, so it can't check to see
        # if the user is accessing itself
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_get_systems_managed_by_self(
        self, api_client: TestClient, url, viewer_user, system, db
    ) -> None:
        """User can view their own systems even if they don't necessarily have the correct scopes"""
        viewer_user.set_as_system_manager(db, system)
        auth_header = generate_auth_header_for_user(viewer_user, [])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK
        assert len(resp.json()) == 1
        assert resp.json()[0]["fides_key"] == system.fides_key

    def test_get_systems_managed_by_other_user(
        self, api_client: TestClient, url, viewer_user, system, db
    ) -> None:
        """User need read system manager permissions to be able to view someone else's systems"""
        viewer_user.set_as_system_manager(db, system)
        another_user = FidesUser.create(
            db=db,
            data={
                "username": "another_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
                "email_address": "test.user@ethyca.com",
            },
        )
        client = ClientDetail(
            hashed_secret="thisisatest",
            salt="thisisstillatest",
            scopes=SCOPE_REGISTRY,
            user_id=another_user.id,
        )
        db.add(client)
        db.commit()

        auth_header = generate_auth_header_for_user(another_user, [])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

        client.delete(db=db)
        another_user.delete(db)

    def test_get_systems_managed_by_user_not_found(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.get(
            V1_URL_PREFIX + f"/user/bad_user/system-manager", headers=auth_header
        )
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert resp.json()["detail"] == f"No user found with id bad_user."

    def test_get_systems_managed_by_user_none_exist(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK
        assert resp.json() == []

    def test_get_systems_managed_by_user(
        self, api_client: TestClient, generate_auth_header, url, viewer_user, system, db
    ) -> None:
        viewer_user.set_as_system_manager(db, system)
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK
        assert len(resp.json()) == 1
        assert resp.json()[0]["fides_key"] == system.fides_key


class TestGetSpecificSystemUserManages:
    @pytest.fixture(scope="function")
    def url(self, viewer_user, system) -> str:
        return (
            V1_URL_PREFIX + f"/user/{viewer_user.id}/system-manager/{system.fides_key}"
        )

    def test_get_system_managed_by_user_not_authenticated(
        self, api_client: TestClient, url: str
    ) -> None:
        resp = api_client.get(url, headers={})
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_get_system_managed_by_user_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        # Note that no user is attached to this client so we can't check
        # to see if the user is accessing its own systems
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_get_system_managed_by_self(
        self, api_client: TestClient, url, viewer_user, system, db
    ) -> None:
        """User can view their own systems even if they don't necessarily have the correct scopes"""
        viewer_user.set_as_system_manager(db, system)
        auth_header = generate_auth_header_for_user(viewer_user, [])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["fides_key"] == system.fides_key

    def test_get_system_managed_by_other_user(
        self, api_client: TestClient, url, viewer_user, system, db
    ) -> None:
        """User need read system manager permissions to be able to view someone else's systems"""
        viewer_user.set_as_system_manager(db, system)
        another_user = FidesUser.create(
            db=db,
            data={
                "username": "another_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
                "email_address": "test.user@ethyca.com",
            },
        )
        client = ClientDetail(
            hashed_secret="thisisatest",
            salt="thisisstillatest",
            scopes=SCOPE_REGISTRY,
            user_id=another_user.id,
        )
        db.add(client)
        db.commit()

        auth_header = generate_auth_header_for_user(another_user, [])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

        client.delete(db=db)
        another_user.delete(db)

    def test_get_system_managed_by_user_not_found(
        self, api_client: TestClient, generate_auth_header, url, system
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.get(
            V1_URL_PREFIX + f"/user/bad_user/system-manager/{system.fides_key}",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert resp.json()["detail"] == f"No user found with id bad_user."

    def test_get_system_managed_by_user_system_does_not_exist(
        self, api_client: TestClient, generate_auth_header, url, viewer_user
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.get(
            V1_URL_PREFIX + f"/user/{viewer_user.id}/system-manager/bad_system",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert resp.json()["detail"] == f"No system found with fides_key bad_system."

    def test_get_system_not_managed_by_user(
        self, api_client: TestClient, generate_auth_header, url, viewer_user, system
    ) -> None:
        assert not viewer_user.systems
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert (
            resp.json()["detail"]
            == f"User {viewer_user.id} is not a manager of system {system.fides_key}"
        )

    def test_get_system_managed_by_user(
        self, api_client: TestClient, generate_auth_header, url, viewer_user, system, db
    ) -> None:
        viewer_user.set_as_system_manager(db, system)
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["fides_key"] == system.fides_key


class TestRemoveUserAsSystemManager:
    @pytest.fixture(scope="function")
    def url(self, viewer_user, system) -> str:
        return (
            V1_URL_PREFIX + f"/user/{viewer_user.id}/system-manager/{system.fides_key}"
        )

    def test_delete_user_as_system_manager_not_authenticated(
        self, api_client: TestClient, url: str
    ) -> None:
        resp = api_client.delete(url, headers={})
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_delete_user_as_system_manager_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_READ])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_delete_user_as_system_manager_user_not_found(
        self, api_client: TestClient, generate_auth_header, url, system
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_DELETE])
        resp = api_client.delete(
            V1_URL_PREFIX + f"/user/bad_user/system-manager/{system.fides_key}",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert resp.json()["detail"] == f"No user found with id bad_user."

    def test_delete_user_as_system_manager_from_nonexistent_system(
        self, api_client: TestClient, generate_auth_header, url, viewer_user
    ) -> None:
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_DELETE])
        resp = api_client.delete(
            V1_URL_PREFIX + f"/user/{viewer_user.id}/system-manager/bad_system",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert resp.json()["detail"] == f"No system found with fides_key bad_system."

    def test_remove_user_from_system_not_managed_by_user(
        self, api_client: TestClient, generate_auth_header, url, viewer_user, system
    ) -> None:
        assert not viewer_user.systems
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_DELETE])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert (
            resp.json()["detail"]
            == f"Cannot delete user as system manager. User {viewer_user.id} is not a manager of system {system.fides_key}."
        )

    def test_delete_user_as_system_manager(
        self, api_client: TestClient, generate_auth_header, url, viewer_user, system, db
    ) -> None:
        viewer_user.set_as_system_manager(db, system)
        auth_header = generate_auth_header(scopes=[SYSTEM_MANAGER_DELETE])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_204_NO_CONTENT

        db.refresh(viewer_user)
        assert viewer_user.systems == []


class TestAcceptUserInvite:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + USER_ACCEPT_INVITE

    def test_accept_invite_valid(
        self,
        db,
        api_client,
        url,
    ):
        user = FidesUser.create(
            db=db,
            data={
                "username": "valid_user",
            },
        )
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )
        FidesUserInvite.create(
            db=db, data={"username": "valid_user", "invite_code": "valid_code"}
        )

        response = api_client.post(
            url,
            params={"username": "valid_user", "invite_code": "valid_code"},
            json={"username": "valid_user", "new_password": "Testpassword1!"},
        )

        assert response.status_code == HTTP_200_OK

    def test_accept_invite_invalid_code(self, db, api_client, url):
        user = FidesUser.create(
            db=db,
            data={
                "username": "valid_user",
            },
        )
        FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [VIEWER]},
        )
        FidesUserInvite.create(
            db=db, data={"username": "valid_user", "invite_code": "valid_code"}
        )

        response = api_client.post(
            url,
            params={"username": "valid_user", "invite_code": "invalid_code"},
            json={"username": "valid_user", "new_password": "Testpassword1!"},
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invite code is invalid."

    @mock.patch("fides.api.api.v1.endpoints.user_endpoints.FidesUserInvite.get_by")
    def test_accept_invite_expired_code(self, mock_get_by, api_client: TestClient, url):
        # the expiration is based on the updated_at timestamp so we need to mock an expired FidesUserInvite to test this scenario
        mock_instance = mock.Mock(
            spec=FidesUserInvite,
            invite_code_valid=mock.Mock(return_value=True),
            is_expired=mock.Mock(return_value=True),
        )
        mock_get_by.return_value = mock_instance

        response = api_client.post(
            url,
            params={"username": "valid_user", "invite_code": "expired_code"},
            json={"username": "valid_user", "new_password": "Testpassword1!"},
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invite code has expired."

    def test_accept_invite_nonexistent_user(self, api_client, url):
        response = api_client.post(
            url,
            params={"username": "nonexistent_user", "invite_code": "some_code"},
            json={
                "username": "nonexistent_user",
                "new_password": "Testpassword1!",
            },
        )
        assert response.status_code == HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "User not found."

import json
from datetime import datetime
from typing import List

import pytest
from fastapi_pagination import Params
from fideslib.cryptography.cryptographic_util import str_to_b64_str
from fideslib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fideslib.models.client import ADMIN_UI_ROOT, ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions
from fideslib.oauth.jwt import generate_jwe
from fideslib.oauth.oauth_util import extract_payload
from fidesops.ops.api.v1.scope_registry import (
    PRIVACY_REQUEST_READ,
    STORAGE_READ,
    USER_CREATE,
    USER_DELETE,
    USER_PASSWORD_RESET,
    USER_READ,
    USER_UPDATE,
)
from fidesops.ops.api.v1.urn_registry import (
    LOGIN,
    LOGOUT,
    USER_DETAIL,
    USERS,
    V1_URL_PREFIX,
)
from fidesops.ops.core.config import config
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

from tests.ops.conftest import generate_auth_header_for_user

page_size = Params().size


class TestCreateUser:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
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
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {
            "username": "spaces in name",
            "password": str_to_b64_str("TestP@ssword9"),
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

        body = {"username": "test_user", "password": str_to_b64_str("TestP@ssword9")}
        user = FidesUser.create(db=db, data=body)

        response = api_client.post(url, headers=auth_header, json=body)
        response_body = json.loads(response.text)
        assert response_body["detail"] == "Username already exists."
        assert HTTP_400_BAD_REQUEST == response.status_code

        user.delete(db)

    def test_create_user_bad_password(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])

        body = {"username": "test_user", "password": str_to_b64_str("short")}
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Password must have at least eight characters."
        )

        body = {"username": "test_user", "password": str_to_b64_str("longerpassword")}
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Password must have at least one number."
        )

        body = {"username": "test_user", "password": str_to_b64_str("longer55password")}
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Password must have at least one capital letter."
        )

        body = {"username": "test_user", "password": str_to_b64_str("LoNgEr55paSSworD")}
        response = api_client.post(url, headers=auth_header, json=body)
        assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Password must have at least one symbol."
        )

    def test_create_user(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {"username": "test_user", "password": str_to_b64_str("TestP@ssword9")}

        response = api_client.post(url, headers=auth_header, json=body)

        user = FidesUser.get_by(db, field="username", value=body["username"])
        response_body = json.loads(response.text)
        assert HTTP_201_CREATED == response.status_code
        assert response_body == {"id": user.id}
        assert user.permissions is not None
        user.delete(db)

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
            "first_name": "Test",
            "last_name": "User",
        }

        response = api_client.post(url, headers=auth_header, json=body)

        user = FidesUser.get_by(db, field="username", value=body["username"])
        response_body = json.loads(response.text)
        assert HTTP_201_CREATED == response.status_code
        assert response_body == {"id": user.id}
        assert user.permissions is not None
        user.delete(db)


class TestDeleteUser:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, user) -> str:
        return f"{V1_URL_PREFIX}{USERS}/{user.id}"

    def test_delete_user_not_authenticated(self, url, api_client):
        response = api_client.delete(url, headers={})
        assert HTTP_401_UNAUTHORIZED == response.status_code

    def test_create_user_wrong_scope(self, url, api_client, generate_auth_header, db):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.delete(url, headers=auth_header)
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_delete_user_not_admin_root_or_self(
        self, url, api_client, db, generate_auth_header, user
    ):
        auth_header = generate_auth_header([USER_DELETE])
        response = api_client.delete(url, headers=auth_header)
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_delete_nonexistent_user(self, api_client, db, generate_auth_header, user):
        auth_header = generate_auth_header([USER_DELETE])
        url = f"{V1_URL_PREFIX}{USERS}/nonexistent_user"
        response = api_client.delete(url, headers=auth_header)
        assert HTTP_404_NOT_FOUND == response.status_code

    def test_delete_self(self, api_client, db, generate_auth_header):
        user = FidesUser.create(
            db=db,
            data={
                "username": "test_delete_user",
                "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
            },
        )
        saved_user_id = user.id

        FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )

        assert user.permissions is not None
        saved_permissions_id = user.permissions.id

        client, _ = ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
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
        jwe = generate_jwe(json.dumps(payload), config.security.app_encryption_key)
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

    def test_delete_user_as_root(self, api_client, db, generate_auth_header, user):
        other_user = FidesUser.create(
            db=db,
            data={
                "username": "test_delete_user",
                "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
            },
        )

        FidesUserPermissions.create(
            db=db, data={"user_id": other_user.id, "scopes": [PRIVACY_REQUEST_READ]}
        )

        user_client, _ = ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
            scopes=[USER_DELETE],
            user_id=other_user.id,
        )
        client_id = user_client.id
        saved_user_id = other_user.id
        saved_permission_id = other_user.permissions.id

        # Temporarily set the user's client to be the Admin UI Root client
        client = user.client
        client.fides_key = ADMIN_UI_ROOT
        client.save(db)

        payload = {
            JWE_PAYLOAD_SCOPES: [USER_DELETE],
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), config.security.app_encryption_key)
        auth_header = {"Authorization": "Bearer " + jwe}

        response = api_client.delete(
            f"{V1_URL_PREFIX}{USERS}/{other_user.id}", headers=auth_header
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

        # Deleted user's client is also deleted
        client_search = ClientDetail.get_by(db, field="id", value=client_id)
        assert client_search is None

        # Admin client who made the request is not deleted
        admin_client_search = ClientDetail.get_by(db, field="id", value=user.client.id)
        assert admin_client_search is not None
        admin_client_search.delete(db)


class TestGetUsers:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
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
        response_body = json.loads(resp.text)
        assert len(response_body["items"]) == 0
        assert response_body["total"] == 0
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

    def test_get_users(self, api_client: TestClient, generate_auth_header, url, db):
        create_auth_header = generate_auth_header(scopes=[USER_CREATE])
        saved_users: List[FidesUser] = []
        total_users = 25
        for i in range(total_users):
            body = {
                "username": f"user{i}@example.com",
                "password": str_to_b64_str("Password123!"),
                "first_name": "Test",
                "last_name": "User",
            }
            resp = api_client.post(url, headers=create_auth_header, json=body)
            assert resp.status_code == HTTP_201_CREATED
            user = FidesUser.get_by(db, field="username", value=body["username"])
            saved_users.append(user)

        get_auth_header = generate_auth_header(scopes=[USER_READ])
        resp = api_client.get(url, headers=get_auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = json.loads(resp.text)
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

        for i in range(total_users):
            saved_users[i].delete(db)

    def test_get_filtered_users(
        self, api_client: TestClient, generate_auth_header, url, db
    ):
        create_auth_header = generate_auth_header(scopes=[USER_CREATE])
        saved_users: List[FidesUser] = []
        total_users = 50
        for i in range(total_users):
            body = {
                "username": f"user{i}@example.com",
                "password": str_to_b64_str("Password123!"),
            }
            resp = api_client.post(url, headers=create_auth_header, json=body)
            assert resp.status_code == HTTP_201_CREATED
            user = FidesUser.get_by(db, field="username", value=body["username"])
            saved_users.append(user)

        get_auth_header = generate_auth_header(scopes=[USER_READ])

        resp = api_client.get(f"{url}?username={15}", headers=get_auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = json.loads(resp.text)
        assert len(response_body["items"]) == 1
        assert response_body["total"] == 1
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

        resp = api_client.get(f"{url}?username={5}", headers=get_auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = json.loads(resp.text)
        assert len(response_body["items"]) == 5
        assert response_body["total"] == 5
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

        resp = api_client.get(f"{url}?username=not real user", headers=get_auth_header)
        assert resp.status_code == HTTP_200_OK
        response_body = json.loads(resp.text)
        assert len(response_body["items"]) == 0
        assert response_body["total"] == 0
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

        for i in range(total_users):
            saved_users[i].delete(db)


class TestGetUser:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + USER_DETAIL

    @pytest.fixture(scope="function")
    def url_no_id(self, oauth_client: ClientDetail) -> str:
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
        assert user_data["created_at"] == application_user.created_at.isoformat()
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
        assert user_data["created_at"] == user.created_at.isoformat()
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
        assert user_data["created_at"] == application_user.created_at.isoformat()
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
        NEW_PASSWORD = "newpassword"
        application_user.update_password(db=db, new_password=OLD_PASSWORD)

        auth_header = generate_auth_header_for_user(
            user=application_user,
            scopes=[USER_PASSWORD_RESET],
        )
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

    def test_update_user_password_invalid(
        self,
        api_client,
        db,
        url_no_id,
        application_user,
    ) -> None:
        OLD_PASSWORD = "oldpassword"
        NEW_PASSWORD = "newpassword"
        application_user.update_password(db=db, new_password=OLD_PASSWORD)

        auth_header = generate_auth_header_for_user(
            user=application_user,
            scopes=[USER_PASSWORD_RESET],
        )
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
        NEW_PASSWORD = "newpassword"
        application_user.update_password(db=db, new_password=OLD_PASSWORD)
        auth_header = generate_auth_header_for_user(
            user=application_user,
            scopes=[USER_PASSWORD_RESET],
        )
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


class TestUserLogin:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + LOGIN

    def test_user_does_not_exist(self, db, url, api_client):
        body = {
            "username": "does not exist",
            "password": str_to_b64_str("idonotknowmypassword"),
        }
        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_404_NOT_FOUND

    def test_bad_login(self, db, url, user, api_client):
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
            extract_payload(token, config.security.app_encryption_key)
        )
        assert token_data["client-id"] == user.client.id
        assert token_data["scopes"] == [
            PRIVACY_REQUEST_READ
        ]  # Uses scopes on existing client

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == user.id

        user.client.delete(db)

    def test_login_updates_last_login_date(self, db, url, user, api_client):
        body = {
            "username": user.username,
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        }

        response = api_client.post(url, headers={}, json=body)
        assert response.status_code == HTTP_200_OK

        db.refresh(user)
        assert user.last_login_at is not None

    def test_login_uses_existing_client(self, db, url, user, api_client):
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
            extract_payload(token, config.security.app_encryption_key)
        )
        assert token_data["client-id"] == existing_client_id
        assert token_data["scopes"] == [
            PRIVACY_REQUEST_READ
        ]  # Uses scopes on existing client

        assert "user_data" in list(response.json().keys())
        assert response.json()["user_data"]["id"] == user.id


class TestUserLogout:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + LOGOUT

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
            + generate_jwe(json.dumps(payload), config.security.app_encryption_key)
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

        # Ensure that the client token is invalidated after logout
        # Assert a request with the outdated client token gives a 401
        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), config.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert HTTP_403_FORBIDDEN == response.status_code

    def test_logout(self, db, url, api_client, generate_auth_header, oauth_client):
        oauth_client_id = oauth_client.id
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.post(url, headers=auth_header, json={})
        assert HTTP_204_NO_CONTENT == response.status_code

        # Verify client was deleted
        client_search = ClientDetail.get_by(db, field="id", value=oauth_client_id)
        assert client_search is None

        # Gets AuthorizationError - client does not exist, this token can't be used anymore
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == HTTP_403_FORBIDDEN

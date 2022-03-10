from datetime import datetime

import json

import pytest

from fidesops.api.v1.urn_registry import V1_URL_PREFIX, USERS
from fidesops.models.client import ClientDetail, ADMIN_UI_ROOT
from fidesops.api.v1.scope_registry import STORAGE_READ, USER_CREATE, USER_DELETE
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.util.oauth_util import generate_jwe
from fidesops.schemas.jwt import (
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
    JWE_ISSUED_AT,
)


class TestCreateUser:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + USERS

    def test_create_user_not_authenticated(self, url, api_client):
        response = api_client.post(url, headers={}, json={})
        assert 401 == response.status_code

    def test_create_user_wrong_scope(self, url, api_client, generate_auth_header):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.post(url, headers=auth_header, json={})
        assert 403 == response.status_code

    def test_create_user_bad_username(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])
        body = {"username": "spaces in name", "password": "TestP@ssword9"}

        response = api_client.post(url, headers=auth_header, json=body)
        assert 422 == response.status_code

    def test_username_exists(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])

        body = {"username": "test_user", "password": "TestP@ssword9"}
        user = FidesopsUser.create(db=db, data=body)

        response = api_client.post(url, headers=auth_header, json=body)
        response_body = json.loads(response.text)
        assert response_body["detail"] == "Username already exists."
        assert 400 == response.status_code

        user.delete(db)

    def test_create_user_bad_password(
        self,
        db,
        api_client,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header([USER_CREATE])

        body = {"username": "test_user", "password": "short"}
        response = api_client.post(url, headers=auth_header, json=body)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Password must have at least eight characters."
        )

        body = {"username": "test_user", "password": "longerpassword"}
        response = api_client.post(url, headers=auth_header, json=body)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Password must have at least one number."
        )

        body = {"username": "test_user", "password": "longer55password"}
        response = api_client.post(url, headers=auth_header, json=body)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Password must have at least one capital letter."
        )

        body = {"username": "test_user", "password": "LoNgEr55paSSworD"}
        response = api_client.post(url, headers=auth_header, json=body)
        assert 422 == response.status_code
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
        body = {"username": "test_user", "password": "TestP@ssword9"}

        response = api_client.post(url, headers=auth_header, json=body)
        user = FidesopsUser.get_by(db, field="username", value=body["username"])
        response_body = json.loads(response.text)
        assert response_body == {"id": user.id}
        assert 201 == response.status_code

        user.delete(db)


class TestDeleteUser:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, user) -> str:
        return f"{V1_URL_PREFIX}{USERS}/{user.id}"

    def test_delete_user_not_authenticated(self, url, api_client):
        response = api_client.delete(url, headers={})
        assert 401 == response.status_code

    def test_create_user_wrong_scope(self, url, api_client, generate_auth_header, db):
        auth_header = generate_auth_header([STORAGE_READ])
        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    def test_delete_user_not_admin_root_or_self(
        self, url, api_client, db, generate_auth_header, user
    ):
        auth_header = generate_auth_header([USER_DELETE])
        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    def test_delete_nonexistent_user(self, api_client, db, generate_auth_header, user):
        auth_header = generate_auth_header([USER_DELETE])
        url = f"{V1_URL_PREFIX}{USERS}/nonexistent_user"
        response = api_client.delete(url, headers=auth_header)
        assert 404 == response.status_code

    def test_delete_self(self, api_client, db, generate_auth_header):
        user = FidesopsUser.create(
            db=db,
            data={
                "username": "test_delete_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            },
        )
        saved_user_id = user.id
        client, _ = ClientDetail.create_client_and_secret(
            db, [USER_DELETE], user_id=user.id
        )
        assert client.user == user
        saved_client_id = client.id

        payload = {
            JWE_PAYLOAD_SCOPES: [USER_DELETE],
            JWE_PAYLOAD_CLIENT_ID: client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload))
        auth_header = {"Authorization": "Bearer " + jwe}

        response = api_client.delete(
            f"{V1_URL_PREFIX}{USERS}/{user.id}", headers=auth_header
        )
        assert 204 == response.status_code

        db.expunge_all()

        user_search = FidesopsUser.get_by(db, field="id", value=saved_user_id)
        assert user_search is None

        client_search = ClientDetail.get_by(db, field="id", value=saved_client_id)
        assert client_search is None

    def test_delete_user_as_root(self, api_client, db, generate_auth_header, user):
        other_user = FidesopsUser.create(
            db=db,
            data={
                "username": "test_delete_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            },
        )
        user_client, _ = ClientDetail.create_client_and_secret(
            db, [USER_DELETE], user_id=other_user.id
        )
        client_id = user_client.id
        saved_user_id = other_user.id
        admin_user_id = user.id

        admin_client, _ = ClientDetail.create_client_and_secret(
            db, [USER_DELETE], fides_key=ADMIN_UI_ROOT, user_id=user.id
        )
        admin_client_id = admin_client.id
        payload = {
            JWE_PAYLOAD_SCOPES: [USER_DELETE],
            JWE_PAYLOAD_CLIENT_ID: admin_client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload))
        auth_header = {"Authorization": "Bearer " + jwe}

        response = api_client.delete(
            f"{V1_URL_PREFIX}{USERS}/{other_user.id}", headers=auth_header
        )
        assert 204 == response.status_code

        db.expunge_all()

        user_search = FidesopsUser.get_by(db, field="id", value=saved_user_id)
        assert user_search is None

        # Deleted user's client is also deleted
        client_search = ClientDetail.get_by(db, field="id", value=client_id)
        assert client_search is None

        # Admin client who made the request is not deleted
        admin_client_search = ClientDetail.get_by(
            db, field="id", value=admin_client_id
        )
        assert admin_client_search is not None
        admin_client_search.delete(db)

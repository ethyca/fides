# pylint: disable=duplicate-code, missing-function-docstring, too-many-locals

import json
import os
from datetime import datetime
from unittest.mock import patch

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

from fides.lib.core.config import get_config
from fides.lib.cryptography.cryptographic_util import str_to_b64_str
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.lib.models.client import ADMIN_UI_ROOT, ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions
from fides.lib.oauth.api.urn_registry import LOGIN, USER_DETAIL, USERS
from fides.lib.oauth.jwt import generate_jwe
from fides.lib.oauth.oauth_util import extract_payload
from fides.lib.oauth.scopes import (
    PRIVACY_REQUEST_READ,
    USER_CREATE,
    USER_DELETE,
    USER_READ,
)

page_size = Params().size


@pytest.mark.parametrize(
    "body",
    [
        {
            "username": "user",
            "password": str_to_b64_str("Password1!"),
        },
        {
            "username": "test_user",
            "password": str_to_b64_str("TestP@ssword9"),
            "first_name": "Test",
            "last_name": "User",
        },
    ],
)
@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
def test_create_user(body, client, db, auth_header):
    response = client.post(USERS, headers=auth_header, json=body)
    assert response.status_code == HTTP_201_CREATED
    user = FidesUser.get_by(db, field="username", value=body["username"])
    assert response.json()["id"] == user.id  # type: ignore
    assert user.permissions is not None  # type: ignore


@pytest.mark.parametrize(
    "password, message",
    [
        ("Short1!", "eight characters"),
        ("Nonumber*", "one number"),
        ("nocapital1!", "one capital"),
        ("NOLOWERCASE1!", "one lowercase"),
        ("Nosymbol1", "one symbol"),
    ],
)
@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
@pytest.mark.usefixtures("db")
def test_create_user_bad_password(
    password,
    message,
    client,
    auth_header,
) -> None:
    body = {"username": "test_user", "password": str_to_b64_str(password)}
    response = client.post(USERS, headers=auth_header, json=body)
    assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
    assert message in response.json()["detail"][0]["msg"]


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
def test_create_user_bad_username(
    client,
    auth_header,
) -> None:
    body = {"username": "spaces in name", "password": str_to_b64_str("TestP@ssword9")}

    response = client.post(USERS, headers=auth_header, json=body)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_create_user_not_authenticated(client):
    response = client.post(USERS, headers={}, json={})
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
def test_create_user_username_exists(
    db,
    client,
    auth_header,
) -> None:
    body = {"username": "test_user", "password": str_to_b64_str("TestP@ssword9")}
    FidesUser.create(db=db, data=body)

    response = client.post(USERS, headers=auth_header, json=body)
    assert "Username already exists" in response.json()["detail"]
    assert response.status_code == HTTP_400_BAD_REQUEST


@patch.dict(
    os.environ,
    {
        "FIDES__SECURITY__ROOT_USERNAME": "root_user",
    },
    clear=True,
)
@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
def test_create_user_username_matches_root(
    client,
    auth_header,
) -> None:
    body = {"username": "root_user", "password": str_to_b64_str("TestP@ssword9")}

    response = client.post(USERS, headers=auth_header, json=body)
    assert "detail" in response.json()
    assert "Username already exists" in response.json()["detail"]
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
def test_create_user_wrong_scope(client, auth_header):
    response = client.post(USERS, headers=auth_header, json={})
    assert HTTP_403_FORBIDDEN == response.status_code


def test_delete_user_not_authenticated(client):
    response = client.delete(USER_DETAIL, headers={})
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.usefixtures("db")
def test_delete_user_not_admin_root_or_self(client, auth_header, user):
    response = client.delete(f"{USERS}/{user.id}", headers=auth_header)
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.usefixtures("db")
def test_delete_nonexistent_user(client, auth_header):
    url = f"{USERS}/nonexistent_user"
    response = client.delete(url, headers=auth_header)
    assert response.status_code == HTTP_404_NOT_FOUND


def test_delete_self(client, db, config):
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

    assert user.permissions is not None  # type: ignore
    saved_permissions_id = user.permissions.id  # type: ignore

    client_detail, _ = ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        scopes=[USER_DELETE],
        user_id=user.id,
    )
    assert client_detail.user == user  # type: ignore
    saved_client_id = client_detail.id

    payload = {
        JWE_PAYLOAD_SCOPES: [USER_DELETE],
        JWE_PAYLOAD_CLIENT_ID: client_detail.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), config.security.app_encryption_key)
    auth_header = {"Authorization": "Bearer " + jwe}

    response = client.delete(f"{USERS}/{user.id}", headers=auth_header)
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


def test_delete_user_as_root(client, db, user, config):
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
    saved_permission_id = other_user.permissions.id  # type: ignore

    # Temporarily set the user's client to be the Admin UI Root client
    client_detail = user.client
    client_detail.fides_key = ADMIN_UI_ROOT
    client_detail.save(db)

    payload = {
        JWE_PAYLOAD_SCOPES: [USER_DELETE],
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), config.security.app_encryption_key)
    auth_header = {"Authorization": "Bearer " + jwe}

    response = client.delete(f"{USERS}/{other_user.id}", headers=auth_header)
    assert response.status_code == HTTP_204_NO_CONTENT

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


@pytest.mark.usefixtures("db")
def test_get_users_not_authenticated(client):
    resp = client.get(USERS, headers={})
    assert resp.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.usefixtures("db")
def test_get_users_wrong_scope(client, auth_header):
    response = client.get(USERS, headers=auth_header)
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.parametrize("auth_header", [[USER_READ]], indirect=True)
@pytest.mark.usefixtures("db")
def test_get_users_no_users(client, auth_header):
    response = client.get(USERS, headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == 0
    assert response.json()["total"] == 0
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size


@pytest.mark.parametrize("auth_header", [[USER_CREATE, USER_READ]], indirect=True)
def test_get_users(client, auth_header, db):
    saved_users = []
    total_users = 25
    for i in range(total_users):
        body = {
            "username": f"user{i}@example.com",
            "password": str_to_b64_str("Password123!"),
            "first_name": "Test",
            "last_name": "User",
        }
        response = client.post(USERS, headers=auth_header, json=body)
        assert response.status_code == HTTP_201_CREATED
        user = FidesUser.get_by(db, field="username", value=body["username"])
        saved_users.append(user)

    response = client.get(USERS, headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == total_users
    assert response.json()["total"] == total_users
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size

    user_data = response.json()["items"][0]
    assert user_data["username"]
    assert user_data["id"]
    assert user_data["created_at"]
    assert user_data["first_name"]
    assert user_data["last_name"]


@pytest.mark.parametrize("auth_header", [[USER_CREATE, USER_READ]], indirect=True)
def test_get_filtered_users(client, auth_header, db):
    saved_users = []
    total_users = 50
    for i in range(total_users):
        body = {
            "username": f"user{i}@example.com",
            "password": str_to_b64_str("Password123!"),
        }
        response = client.post(USERS, headers=auth_header, json=body)
        assert response.status_code == HTTP_201_CREATED
        user = FidesUser.get_by(db, field="username", value=body["username"])
        saved_users.append(user)

    response = client.get(f"{USERS}?username={15}", headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == 1
    assert response.json()["total"] == 1
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size

    response = client.get(f"{USERS}?username={5}", headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == 5
    assert response.json()["total"] == 5
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size

    response = client.get(f"{USERS}?username=not real user", headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == 0
    assert response.json()["total"] == 0
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size


@pytest.mark.usefixtures("db")
def test_get_user_not_authenticated(client):
    response = client.get(USER_DETAIL, headers={})
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.usefixtures("db")
def test_get_user_wrong_scope(client, auth_header):
    response = client.get(USER_DETAIL, headers=auth_header)
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.parametrize("auth_header", [[USER_READ]], indirect=True)
@pytest.mark.usefixtures("db")
def test_get_user_does_not_exist(client, auth_header):
    response = client.get(f"{USERS}/this_is_a_nonexistent_key", headers=auth_header)
    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.parametrize("auth_header", [[USER_READ]], indirect=True)
@pytest.mark.usefixtures("db")
def test_get_user(client, auth_header, application_user):
    response = client.get(f"{USERS}/{application_user.id}", headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert response.json()["username"] == application_user.username
    assert response.json()["id"] == application_user.id
    assert response.json()["created_at"] == application_user.created_at.isoformat()
    assert response.json()["first_name"] == application_user.first_name
    assert response.json()["last_name"] == application_user.last_name


@pytest.mark.usefixtures("db")
def test_login_user_does_not_exist(client):
    body = {
        "username": "does not exist",
        "password": str_to_b64_str("idonotknowmypassword"),
    }
    response = client.post(LOGIN, headers={}, json=body)
    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("db")
def test_bad_login(user, client):
    body = {
        "username": user.username,
        "password": str_to_b64_str("idonotknowmypassword"),
    }
    response = client.post(LOGIN, headers={}, json=body)
    assert response.status_code == HTTP_403_FORBIDDEN


def test_login_creates_client(db, user, client, config):
    user.client.delete(db)
    assert user.client is None
    assert user.permissions is not None
    body = {
        "username": user.username,
        "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
    }
    response = client.post(LOGIN, headers={}, json=body)
    db.refresh(user)

    assert response.status_code == HTTP_200_OK
    assert user.client is not None
    assert "token_data" in list(response.json().keys())
    token = response.json()["token_data"]["access_token"]
    token_data = json.loads(extract_payload(token, config.security.app_encryption_key))
    assert token_data["client-id"] == user.client.id
    assert "user_data" in list(response.json().keys())
    assert response.json()["user_data"]["id"] == user.id


@patch.dict(
    os.environ,
    {
        "FIDES__SECURITY__ROOT_USERNAME": "rootuser",
        "FIDES__SECURITY__ROOT_PASSWORD": "Rootpassword!",
    },
    clear=True,
)
def test_login_root_user(client):
    config = get_config()
    body = {
        "username": "rootuser",
        "password": str_to_b64_str("Rootpassword!"),
    }
    response = client.post(LOGIN, headers={}, json=body)

    assert response.status_code == HTTP_200_OK
    assert "token_data" in list(response.json().keys())
    token = response.json()["token_data"]["access_token"]
    token_data = json.loads(extract_payload(token, config.security.app_encryption_key))
    assert token_data["client-id"] == config.security.oauth_root_client_id
    assert token_data["scopes"] == config.security.root_user_scopes
    assert "user_data" in list(response.json().keys())
    assert response.json()["user_data"]["id"] == config.security.oauth_root_client_id


def test_login_updates_last_login_date(db, user, client):
    body = {
        "username": user.username,
        "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
    }

    response = client.post(LOGIN, headers={}, json=body)
    assert response.status_code == HTTP_200_OK

    db.refresh(user)
    assert user.last_login_at is not None


def test_login_uses_existing_client(db, user, client, config):
    body = {
        "username": user.username,
        "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
    }

    existing_client_id = user.client.id
    user.client.scopes = [PRIVACY_REQUEST_READ]
    user.client.save(db)
    response = client.post(LOGIN, headers={}, json=body)
    assert response.status_code == HTTP_200_OK

    db.refresh(user)
    assert user.client is not None
    assert "token_data" in list(response.json().keys())
    token = response.json()["token_data"]["access_token"]
    token_data = json.loads(extract_payload(token, config.security.app_encryption_key))
    assert token_data["client-id"] == existing_client_id
    assert token_data["scopes"] == [
        PRIVACY_REQUEST_READ
    ]  # Uses scopes on existing client
    assert "user_data" in list(response.json().keys())
    assert response.json()["user_data"]["id"] == user.id

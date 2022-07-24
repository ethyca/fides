# pylint: disable=invalid-name, missing-docstring, redefined-outer-name, too-many-locals

from __future__ import annotations

import json
from datetime import datetime

import pytest
from fastapi_pagination import Params
from fideslib.cryptography.cryptographic_util import str_to_b64_str
from fideslib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fideslib.oauth.api.urn_registry import LOGIN, USERS
from fideslib.oauth.jwt import generate_jwe
from fideslib.oauth.oauth_util import extract_payload
from fideslib.oauth.scopes import (
    PRIVACY_REQUEST_READ,
    STORAGE_READ,
    USER_CREATE,
    USER_DELETE,
    USER_PASSWORD_RESET,
    USER_READ,
    USER_UPDATE,
)
from sqlalchemy.orm import Session
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

from fidesctl.api.routes.util import API_PREFIX
from fidesctl.api.sql_models import ClientDetail, FidesUser, FidesUserPermissions
from fidesctl.core.config import FidesctlConfig
from tests.conftest import generate_auth_header_for_user

URL = f"{API_PREFIX}{USERS}"
LOGIN_URL = f"{API_PREFIX}{LOGIN}"
LOGOUT_URL = f"{API_PREFIX}/logout"

page_size = Params().size


@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
@pytest.mark.integration
def test_create_user(
    test_client: TestClient, auth_header: dict[str, str], db: Session
) -> None:
    body = {"username": "test_user", "password": str_to_b64_str("TestP@ssword9")}

    response = test_client.post(URL, headers=auth_header, json=body)
    user = FidesUser.get_by(db, field="username", value=body["username"])

    assert HTTP_201_CREATED == response.status_code
    assert response.json() == {"id": user.id}
    assert user.permissions is not None
    user.delete(db)


@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
@pytest.mark.integration
def test_create_user_with_name(
    db: Session, test_client: TestClient, auth_header: dict[str, str]
) -> None:
    body = {
        "username": "test_user",
        "password": str_to_b64_str("TestP@ssword9"),
        "first_name": "Test",
        "last_name": "User",
    }

    response = test_client.post(URL, headers=auth_header, json=body)

    user = FidesUser.get_by(db, field="username", value=body["username"])

    assert HTTP_201_CREATED == response.status_code
    assert response.json() == {"id": user.id}
    assert user.permissions is not None
    user.delete(db)


@pytest.mark.integration
def test_create_user_not_authenticated(test_client: TestClient) -> None:
    response = test_client.post(URL, headers={}, json={})
    assert HTTP_401_UNAUTHORIZED == response.status_code


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
@pytest.mark.integration
def test_create_user_wrong_scope(
    test_client: TestClient, auth_header: dict[str, str]
) -> None:
    response = test_client.post(URL, headers=auth_header, json={})
    assert HTTP_403_FORBIDDEN == response.status_code


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
@pytest.mark.integration
def test_create_user_bad_username(
    test_client: TestClient, auth_header: dict[str, str]
) -> None:
    body = {
        "username": "spaces in name",
        "password": str_to_b64_str("TestP@ssword9"),
    }

    response = test_client.post(URL, headers=auth_header, json=body)
    assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code


@pytest.mark.parametrize(
    "password, expected",
    [
        ("short", "at least eight characters"),
        ("longerpassword", "at least one number"),
        ("longer55pasword", "at least one capital letter"),
        ("LoNgEr55paSSword", "at least one symbol"),
    ],
)
@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
@pytest.mark.integration
def test_create_user_bad_password(
    password: str, expected: str, test_client: TestClient, auth_header: dict[str, str]
) -> None:
    body = {"username": "test_user", "password": str_to_b64_str(password)}
    response = test_client.post(URL, headers=auth_header, json=body)
    assert HTTP_422_UNPROCESSABLE_ENTITY == response.status_code
    assert expected in response.json()["detail"][0]["msg"]


@pytest.mark.parametrize("auth_header", [[USER_CREATE]], indirect=True)
@pytest.mark.integration
def test_username_exists(
    test_client: TestClient, auth_header: dict[str, str], db: Session
) -> None:
    body = {"username": "test_user", "password": str_to_b64_str("TestP@ssword9")}
    user = FidesUser.create(db=db, data=body)

    response = test_client.post(URL, headers=auth_header, json=body)
    response_body = json.loads(response.text)
    assert response_body["detail"] == "Username already exists."
    assert HTTP_400_BAD_REQUEST == response.status_code

    user.delete(db)


@pytest.mark.integration
def test_delete_user_not_authenticated(
    test_client: TestClient, user: FidesUser
) -> None:
    url = f"{URL}/{user.id}"
    response = test_client.delete(url, headers={})
    assert HTTP_401_UNAUTHORIZED == response.status_code


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.integration
def test_delete_user_not_admin_root_or_self(
    test_client: TestClient, auth_header: dict[str, str], user: FidesUser
) -> None:
    url = f"{URL}/{user.id}"
    response = test_client.delete(url, headers=auth_header)
    assert HTTP_403_FORBIDDEN == response.status_code


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.integration
def test_delete_nonexistent_user(
    test_client: TestClient, auth_header: dict[str, str], user: FidesUser
) -> None:
    url = f"{URL}/nonexistent_user"
    response = test_client.delete(url, headers=auth_header)
    assert HTTP_404_NOT_FOUND == response.status_code


@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.integration
def test_delete_self(
    test_client: TestClient,
    db: Session,
    auth_header: dict[str, str],
    test_config: FidesctlConfig,
) -> None:
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
        test_config.security.oauth_client_id_length_bytes,
        test_config.security.oauth_client_secret_length_bytes,
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
    jwe = generate_jwe(json.dumps(payload), test_config.security.app_encryption_key)
    auth_header = {"Authorization": "Bearer " + jwe}

    response = test_client.delete(f"{URL}/{user.id}", headers=auth_header)
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


@pytest.mark.integration
def test_get_users_not_authenticated(test_client: TestClient) -> None:
    resp = test_client.get(URL, headers={})
    assert resp.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.integration
def test_get_users_wrong_scope(
    test_client: TestClient, auth_header: dict[str, str]
) -> None:
    resp = test_client.get(URL, headers=auth_header)
    assert resp.status_code == HTTP_403_FORBIDDEN


@pytest.mark.usefixtures("db")
@pytest.mark.parametrize("auth_header", [[USER_READ]], indirect=True)
@pytest.mark.integration
def test_get_users_no_users(
    test_client: TestClient, auth_header: dict[str, str]
) -> None:
    response = test_client.get(URL, headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == 0
    assert response.json()["total"] == 0
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size


@pytest.mark.parametrize("auth_header", [[USER_READ, USER_CREATE]], indirect=True)
@pytest.mark.integration
def test_get_users(
    test_client: TestClient, auth_header: dict[str, str], db: Session
) -> None:
    saved_users = []
    total_users = 25
    for i in range(total_users):
        body = {
            "username": f"user{i}@example.com",
            "password": str_to_b64_str("Password123!"),
            "first_name": "Test",
            "last_name": "User",
        }
        response = test_client.post(URL, headers=auth_header, json=body)
        assert response.status_code == HTTP_201_CREATED
        user = FidesUser.get_by(db, field="username", value=body["username"])
        saved_users.append(user)

    response = test_client.get(URL, headers=auth_header)
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

    for i in range(total_users):
        saved_users[i].delete(db)


@pytest.mark.parametrize("auth_header", [[USER_READ, USER_CREATE]], indirect=True)
@pytest.mark.integration
def test_get_filtered_users(
    test_client: TestClient, auth_header: dict[str, str], db: Session
) -> None:
    saved_users = []
    total_users = 50
    for i in range(total_users):
        body = {
            "username": f"user{i}@example.com",
            "password": str_to_b64_str("Password123!"),
        }
        response = test_client.post(URL, headers=auth_header, json=body)
        assert response.status_code == HTTP_201_CREATED
        user = FidesUser.get_by(db, field="username", value=body["username"])
        saved_users.append(user)

    response = test_client.get(f"{URL}?username={15}", headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == 1
    assert response.json()["total"] == 1
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size

    response = test_client.get(f"{URL}?username={5}", headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == 5
    assert response.json()["total"] == 5
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size

    response = test_client.get(f"{URL}?username=not real user", headers=auth_header)
    assert response.status_code == HTTP_200_OK
    assert len(response.json()["items"]) == 0
    assert response.json()["total"] == 0
    assert response.json()["page"] == 1
    assert response.json()["size"] == page_size

    for i in range(total_users):
        saved_users[i].delete(db)


@pytest.mark.integration
def test_get_user_not_authenticated(test_client: TestClient, user: FidesUser) -> None:
    url = f"{URL}/{user.id}"
    response = test_client.get(url, headers={})
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("auth_header", [[USER_DELETE]], indirect=True)
@pytest.mark.integration
def test_get_user_wrong_scope(
    test_client: TestClient, auth_header: dict[str, str], user: FidesUser
) -> None:
    url = f"{URL}/{user.id}"
    response = test_client.get(url, headers=auth_header)
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.parametrize("auth_header", [[USER_READ]], indirect=True)
@pytest.mark.integration
def test_get_user_does_not_exist(
    test_client: TestClient, auth_header: dict[str, str]
) -> None:
    response = test_client.get(f"{URL}/this_is_a_nonexistent_key", headers=auth_header)
    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.parametrize("auth_header", [[USER_READ]], indirect=True)
@pytest.mark.integration
def test_get_user(
    test_client: TestClient, auth_header: dict[str, str], application_user: FidesUser
) -> None:
    response = test_client.get(
        f"{URL}/{application_user.id}",
        headers=auth_header,
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["username"] == application_user.username
    assert response.json()["id"] == application_user.id
    assert response.json()["created_at"] == application_user.created_at.isoformat()
    assert response.json()["first_name"] == application_user.first_name
    assert response.json()["last_name"] == application_user.last_name


@pytest.mark.integration
def test_update_different_users_names(
    test_client: TestClient,
    user: FidesUser,
    application_user: FidesUser,
    test_config: FidesctlConfig,
) -> None:
    new_first_name = "another"
    new_last_name = "name"

    auth_header = generate_auth_header_for_user(
        user=application_user,
        scopes=[USER_UPDATE],
        test_config=test_config,
    )

    response = test_client.put(
        f"{URL}/{user.id}",
        headers=auth_header,
        json={
            "first_name": new_first_name,
            "last_name": new_last_name,
        },
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["username"] == user.username
    assert response.json()["id"] == user.id
    assert response.json()["created_at"] == user.created_at.isoformat()
    assert response.json()["first_name"] == new_first_name
    assert response.json()["last_name"] == new_last_name


@pytest.mark.integration
def test_update_user_names(
    test_client: TestClient, application_user: FidesUser, test_config: FidesctlConfig
) -> None:
    new_first_name = "another"
    new_last_name = "name"

    auth_header = generate_auth_header_for_user(
        user=application_user, scopes=[USER_UPDATE], test_config=test_config
    )

    response = test_client.put(
        f"{URL}/{application_user.id}",
        headers=auth_header,
        json={
            "first_name": new_first_name,
            "last_name": new_last_name,
        },
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["username"] == application_user.username
    assert response.json()["id"] == application_user.id
    assert response.json()["created_at"] == application_user.created_at.isoformat()
    assert response.json()["first_name"] == new_first_name
    assert response.json()["last_name"] == new_last_name


@pytest.mark.integration
def test_update_different_user_password(
    test_client: TestClient,
    db: Session,
    user: FidesUser,
    application_user: FidesUser,
    test_config: FidesctlConfig,
) -> None:
    old_password = "oldpassword"
    new_password = "newpassword"
    application_user.update_password(db=db, new_password=old_password)
    auth_header = generate_auth_header_for_user(
        user=application_user, scopes=[USER_PASSWORD_RESET], test_config=test_config
    )
    print(f"{user.client.__dict__=}")
    response = test_client.post(
        f"{URL}/{user.id}/reset-password",
        headers=auth_header,
        json={
            "old_password": str_to_b64_str(old_password),
            "new_password": str_to_b64_str(new_password),
        },
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert (
        response.json()["detail"]
        == "You are only authorised to update your own user data."
    )

    db.expunge(application_user)
    application_user = application_user.refresh_from_db(db=db)
    assert application_user.credentials_valid(password=old_password)


@pytest.mark.integration
def test_update_user_password_invalid(
    test_client: TestClient,
    db: Session,
    application_user: FidesUser,
    test_config: FidesctlConfig,
) -> None:
    old_password = "oldpassword"
    new_password = "newpassword"
    application_user.update_password(db=db, new_password=old_password)

    auth_header = generate_auth_header_for_user(
        user=application_user, scopes=[USER_PASSWORD_RESET], test_config=test_config
    )
    resp = test_client.post(
        f"{URL}/{application_user.id}/reset-password",
        headers=auth_header,
        json={
            "old_password": str_to_b64_str("mismatching password"),
            "new_password": str_to_b64_str(new_password),
        },
    )
    assert resp.status_code == HTTP_401_UNAUTHORIZED
    assert resp.json()["detail"] == "Incorrect password."

    db.expunge(application_user)
    application_user = application_user.refresh_from_db(db=db)
    assert application_user.credentials_valid(password=old_password)


@pytest.mark.integration
def test_update_user_password(
    test_client: TestClient,
    db: Session,
    application_user: FidesUser,
    test_config: FidesctlConfig,
) -> None:
    old_password = "oldpassword"
    new_password = "newpassword"
    application_user.update_password(db=db, new_password=old_password)
    auth_header = generate_auth_header_for_user(
        user=application_user, scopes=[USER_PASSWORD_RESET], test_config=test_config
    )
    resp = test_client.post(
        f"{URL}/{application_user.id}/reset-password",
        headers=auth_header,
        json={
            "old_password": str_to_b64_str(old_password),
            "new_password": str_to_b64_str(new_password),
        },
    )
    assert resp.status_code == HTTP_200_OK
    db.expunge(application_user)
    application_user = application_user.refresh_from_db(db=db)
    assert application_user.credentials_valid(password=new_password)


@pytest.mark.integration
def test_login_user_does_not_exist(test_client: TestClient) -> None:
    body = {
        "username": "does not exist",
        "password": str_to_b64_str("idonotknowmypassword"),
    }
    response = test_client.post(LOGIN_URL, headers={}, json=body)
    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.integration
def test_bad_login(user: FidesUser, test_client: TestClient) -> None:
    body = {
        "username": user.username,
        "password": str_to_b64_str("idonotknowmypassword"),
    }
    response = test_client.post(LOGIN_URL, headers={}, json=body)
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.integration
def test_login_creates_client(
    db: Session,
    test_config: FidesctlConfig,
    user_no_client: FidesUser,
    test_client: TestClient,
) -> None:
    body = {
        "username": user_no_client.username,
        "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
    }

    assert user_no_client.permissions is not None
    response = test_client.post(LOGIN_URL, headers={}, json=body)
    assert response.status_code == HTTP_200_OK

    db.refresh(user_no_client)
    assert user_no_client.client is not None
    assert "token_data" in list(response.json().keys())
    token = response.json()["token_data"]["access_token"]
    token_data = json.loads(
        extract_payload(token, test_config.security.app_encryption_key)
    )
    assert token_data["client-id"] == user_no_client.client.id
    assert token_data["scopes"] == [
        PRIVACY_REQUEST_READ
    ]  # Uses scopes on existing client

    assert "user_data" in list(response.json().keys())
    assert response.json()["user_data"]["id"] == user_no_client.id

    user_no_client.client.delete(db)


@pytest.mark.integration
def test_login_updates_last_login_date(
    db: Session, user: FidesUser, test_client: TestClient
) -> None:
    body = {
        "username": user.username,
        "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
    }

    response = test_client.post(LOGIN_URL, headers={}, json=body)
    assert response.status_code == HTTP_200_OK

    db.refresh(user)
    assert user.last_login_at is not None


@pytest.mark.integration
def test_login_uses_existing_client(
    db: Session, test_config: FidesctlConfig, user: FidesUser, test_client: TestClient
) -> None:
    body = {
        "username": user.username,
        "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
    }

    existing_client_id = user.client.id
    user.client.scopes = [PRIVACY_REQUEST_READ]
    user.client.save(db)
    response = test_client.post(LOGIN_URL, headers={}, json=body)
    assert response.status_code == HTTP_200_OK

    db.refresh(user)
    assert user.client is not None
    assert "token_data" in list(response.json().keys())
    token = response.json()["token_data"]["access_token"]
    token_data = json.loads(
        extract_payload(token, test_config.security.app_encryption_key)
    )
    assert token_data["client-id"] == existing_client_id
    assert token_data["scopes"] == [
        PRIVACY_REQUEST_READ
    ]  # Uses scopes on existing client

    assert "user_data" in list(response.json().keys())
    assert response.json()["user_data"]["id"] == user.id


@pytest.mark.integration
def test_user_not_deleted_on_logout(
    db: Session, test_client: TestClient, user: FidesUser, test_config: FidesctlConfig
) -> None:
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
        + generate_jwe(json.dumps(payload), test_config.security.app_encryption_key)
    }
    response = test_client.post(LOGOUT_URL, headers=auth_header, json={})
    assert response.status_code == HTTP_204_NO_CONTENT

    # Verify client was deleted
    client_search = ClientDetail.get_by(db, field="id", value=client_id)
    assert client_search is None

    # Assert user is not deleted
    user_search = FidesUser.get_by(db, field="id", value=user_id)
    db.refresh(user_search)
    assert user_search is not None

    # Assert user permissions are not deleted
    permission_search = FidesUserPermissions.get_by(db, field="user_id", value=user_id)
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
        + generate_jwe(json.dumps(payload), test_config.security.app_encryption_key)
    }
    response = test_client.post(LOGOUT_URL, headers=auth_header, json={})
    assert HTTP_403_FORBIDDEN == response.status_code


@pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
@pytest.mark.integration
def test_logout(
    db: Session,
    test_client: TestClient,
    auth_header: dict[str, str],
    oauth_client: ClientDetail,
) -> None:
    oauth_client_id = oauth_client.id
    response = test_client.post(LOGOUT_URL, headers=auth_header, json={})
    assert HTTP_204_NO_CONTENT == response.status_code

    # Verify client was deleted
    client_search = ClientDetail.get_by(db, field="id", value=oauth_client_id)
    assert client_search is None

    # Gets AuthorizationError - client does not exist, this token can't be used anymore
    response = test_client.post(LOGOUT_URL, headers=auth_header, json={})
    assert response.status_code == HTTP_403_FORBIDDEN

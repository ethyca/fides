import json
from datetime import datetime
from unittest import mock

import pytest

from fides.api.ops.api.v1.scope_registry import (
    CLIENT_CREATE,
    CLIENT_DELETE,
    CLIENT_READ,
    CLIENT_UPDATE,
    SCOPE_READ,
    SCOPE_REGISTRY,
    STORAGE_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    CLIENT,
    CLIENT_BY_ID,
    CLIENT_SCOPE,
    OAUTH_CALLBACK,
    SCOPE,
    TOKEN,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import OAuth2TokenException
from fides.api.ops.models.authentication_request import AuthenticationRequest
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.lib.models.client import ClientDetail
from fides.lib.oauth.jwt import generate_jwe
from fides.lib.oauth.oauth_util import extract_payload


class TestCreateClient:
    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + CLIENT

    def test_create_client_not_authenticated(self, api_client, url):
        response = api_client.post(url)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[CLIENT_READ]], indirect=True)
    def test_create_client_wrong_scope(self, auth_header, api_client, url):
        response = api_client.post(url, headers=auth_header)
        assert 403 == response.status_code

    def test_create_client_lacks_client(self, api_client, url, config):
        payload = {
            JWE_PAYLOAD_SCOPES: [CLIENT_CREATE],
        }
        # Build auth header without client
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), config.security.app_encryption_key)
        }

        response = api_client.post(url, headers=auth_header)
        assert 403 == response.status_code

    def test_create_client_with_expired_token(
        self, api_client, url, oauth_client, config
    ):
        payload = {
            JWE_PAYLOAD_CLIENT_ID: oauth_client.id,
            JWE_PAYLOAD_SCOPES: oauth_client.scopes,
            JWE_ISSUED_AT: datetime(1995, 1, 1).isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), config.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[CLIENT_CREATE]], indirect=True)
    def test_create_client(self, auth_header, db, api_client, url, config):

        response = api_client.post(url, headers=auth_header)
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert list(response_body.keys()) == ["client_id", "client_secret"]

        new_client = ClientDetail.get(
            db, object_id=response_body["client_id"], config=config
        )
        assert new_client.hashed_secret != response_body["client_secret"]

    @pytest.mark.parametrize("auth_header", [[CLIENT_CREATE]], indirect=True)
    def test_create_client_with_scopes(self, auth_header, db, api_client, url, config):
        scopes = [
            CLIENT_CREATE,
            CLIENT_DELETE,
            CLIENT_READ,
        ]
        response = api_client.post(
            url,
            headers=auth_header,
            json=scopes,
        )
        response_body = json.loads(response.text)
        assert 200 == response.status_code
        assert list(response_body.keys()) == ["client_id", "client_secret"]

        new_client = ClientDetail.get(
            db, object_id=response_body["client_id"], config=config
        )
        assert new_client.scopes == scopes

    @pytest.mark.parametrize("auth_header", [[CLIENT_CREATE]], indirect=True)
    def test_create_client_with_invalid_scopes(self, auth_header, api_client, url):
        response = api_client.post(
            url,
            headers=auth_header,
            json=["invalid-scope"],
        )

        assert 422 == response.status_code
        assert response.json()["detail"].startswith("Invalid Scope.")

    def test_create_client_with_root_client(self, url, api_client, config):
        data = {
            "client_id": config.security.oauth_root_client_id,
            "client_secret": config.security.oauth_root_client_secret,
        }

        # creates a token with all the scopes
        token_url = V1_URL_PREFIX + TOKEN

        response = api_client.post(token_url, data=data)
        jwt = json.loads(response.text).get("access_token")

        auth_header = {"Authorization": "Bearer " + jwt}

        # Tries to create a separate client with token that has all the scopes
        response = api_client.post(
            url,
            headers=auth_header,
        )
        assert response.status_code == 200
        assert "client_id" in response.json()
        assert "client_secret" in response.json()


class TestGetClientScopes:
    @pytest.fixture(scope="function")
    def url(self, oauth_client):
        return V1_URL_PREFIX + CLIENT_SCOPE.format(client_id=oauth_client.id)

    def test_get_scopes_not_authenticated(self, api_client, url):
        response = api_client.get(url)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_get_scopes_wrong_scope(self, auth_header, api_client, url):
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[CLIENT_READ]], indirect=True)
    def test_get_scopes_invalid_client(self, auth_header, api_client):
        url = V1_URL_PREFIX + CLIENT_SCOPE.format(client_id="bad_client")

        response = api_client.get(url, headers=auth_header)
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert response_body == []

    @pytest.mark.parametrize("auth_header", [[CLIENT_READ]], indirect=True)
    def test_get_scopes(self, auth_header, api_client, url):
        response = api_client.get(url, headers=auth_header)
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert response_body == SCOPE_REGISTRY


class TestSetClientScopes:
    @pytest.fixture(scope="function")
    def url(self, oauth_client):
        return V1_URL_PREFIX + CLIENT_SCOPE.format(client_id=oauth_client.id)

    def test_set_scopes_not_authenticated(self, api_client, url):
        response = api_client.put(url)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[CLIENT_READ]], indirect=True)
    def test_set_scopes_wrong_scope(self, auth_header, api_client, url):
        response = api_client.put(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[CLIENT_UPDATE]], indirect=True)
    def test_set_invalid_scope(self, auth_header, api_client, url):
        response = api_client.put(
            url, headers=auth_header, json=["this-is-not-a-valid-scope"]
        )
        assert 422 == response.status_code

    @pytest.mark.parametrize("auth_header", [[CLIENT_UPDATE]], indirect=True)
    def test_set_scopes_invalid_client(self, auth_header, api_client):
        url = V1_URL_PREFIX + CLIENT_SCOPE.format(client_id="bad_client")

        response = api_client.put(url, headers=auth_header, json=["storage:read"])
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert response_body is None  # No action was taken

    @pytest.mark.parametrize("auth_header", [[CLIENT_UPDATE]], indirect=True)
    def test_set_scopes(self, auth_header, db, api_client, oauth_client, url):
        response = api_client.put(url, headers=auth_header, json=["storage:read"])
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert response_body is None

        db.refresh(oauth_client)
        assert oauth_client.scopes == ["storage:read"]


class TestReadScopes:
    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + SCOPE

    def test_get_scopes_not_authenticated(self, api_client, url):
        response = api_client.get(url)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_get_scopes_wrong_scope(self, auth_header, api_client, url):
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[SCOPE_READ]], indirect=True)
    def test_get_scopes(self, auth_header, api_client, url):
        response = api_client.get(url, headers=auth_header)
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert response_body == SCOPE_REGISTRY


class TestDeleteClient:
    @pytest.fixture(scope="function")
    def url(self, oauth_client):
        return V1_URL_PREFIX + CLIENT_BY_ID.format(client_id=oauth_client.id)

    def test_delete_client_not_authenticated(self, api_client, url):
        response = api_client.delete(url)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[CLIENT_READ]], indirect=True)
    def test_delete_client_wrong_scope(self, auth_header, api_client, url):
        response = api_client.delete(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize("auth_header", [[CLIENT_DELETE]], indirect=True)
    def test_delete_client_invalid_client(self, auth_header, api_client):
        url = V1_URL_PREFIX + CLIENT_BY_ID.format(client_id="bad_client")

        response = api_client.delete(url, headers=auth_header)
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert response_body is None  # No indicator that client didn't exist

    @pytest.mark.parametrize("auth_header", [[CLIENT_DELETE]], indirect=True)
    def test_delete_client(
        self, auth_header, db, api_client, oauth_client, url, config
    ):
        response = api_client.delete(url, headers=auth_header)
        response_body = json.loads(response.text)

        assert 200 == response.status_code
        assert response_body is None

        db.expunge_all()
        client = ClientDetail.get(db, object_id=oauth_client.id, config=config)
        assert client is None


class TestAcquireAccessToken:
    @pytest.fixture(scope="function")
    def url(self):
        return V1_URL_PREFIX + TOKEN

    def test_no_form_data(self, url, api_client):
        response = api_client.post(url, data={})
        assert response.status_code == 401

    def test_invalid_client(self, url, api_client):
        response = api_client.post(
            url, data={"client_id": "notaclient", "secret": "badsecret"}
        )
        assert response.status_code == 401

    def test_invalid_client_secret(self, db, url, api_client, config):
        new_client, _ = ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
        )
        response = api_client.post(
            url, data={"client_id": new_client.id, "secret": "badsecret"}
        )
        assert response.status_code == 401

    def test_get_access_token_root_client(self, url, api_client, config):
        data = {
            "client_id": config.security.oauth_root_client_id,
            "client_secret": config.security.oauth_root_client_secret,
        }

        response = api_client.post(url, data=data)
        jwt = json.loads(response.text).get("access_token")
        assert 200 == response.status_code
        assert (
            data["client_id"]
            == json.loads(extract_payload(jwt, config.security.app_encryption_key))[
                JWE_PAYLOAD_CLIENT_ID
            ]
        )
        assert (
            json.loads(extract_payload(jwt, config.security.app_encryption_key))[
                JWE_PAYLOAD_SCOPES
            ]
            == SCOPE_REGISTRY
        )

    def test_get_access_token(self, db, url, api_client, config):
        new_client, secret = ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
        )

        data = {
            "client_id": new_client.id,
            "client_secret": secret,
        }

        response = api_client.post(url, data=data)
        jwt = json.loads(response.text).get("access_token")
        assert 200 == response.status_code
        assert (
            data["client_id"]
            == json.loads(extract_payload(jwt, config.security.app_encryption_key))[
                JWE_PAYLOAD_CLIENT_ID
            ]
        )
        assert (
            json.loads(extract_payload(jwt, config.security.app_encryption_key))[
                JWE_PAYLOAD_SCOPES
            ]
            == []
        )


class TestCallback:
    @pytest.fixture
    def callback_url(self):
        return V1_URL_PREFIX + OAUTH_CALLBACK

    def test_callback_for_missing_state(self, api_client, callback_url):
        response = api_client.get(
            callback_url, params={"code": "abc", "state": "not_found"}
        )
        assert response.status_code == 404
        assert response.json() == {
            "detail": "No authentication request found for the given state."
        }

    @mock.patch(
        "fides.api.ops.api.v1.endpoints.saas_config_endpoints.OAuth2AuthorizationCodeAuthenticationStrategy.get_access_token"
    )
    def test_callback_for_valid_state(
        self,
        get_access_token_mock,
        db,
        api_client,
        callback_url,
        oauth2_authorization_code_connection_config,
    ):
        get_access_token_mock.return_value = None
        AuthenticationRequest.create_or_update(
            db,
            data={
                "connection_key": oauth2_authorization_code_connection_config.key,
                "state": "new_request",
            },
        )
        response = api_client.get(
            callback_url, params={"code": "abc", "state": "new_request"}
        )
        assert response.ok
        get_access_token_mock.assert_called_once()

    @mock.patch(
        "fides.api.ops.api.v1.endpoints.saas_config_endpoints.OAuth2AuthorizationCodeAuthenticationStrategy.get_access_token"
    )
    def test_callback_for_valid_state_with_token_error(
        self,
        get_access_token_mock,
        db,
        api_client,
        callback_url,
        oauth2_authorization_code_connection_config,
    ):
        get_access_token_mock.side_effect = OAuth2TokenException(
            "Unable to retrieve access token."
        )
        AuthenticationRequest.create_or_update(
            db,
            data={
                "connection_key": oauth2_authorization_code_connection_config.key,
                "state": "new_request",
            },
        )
        response = api_client.get(
            callback_url, params={"code": "abc", "state": "new_request"}
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Unable to retrieve access token."}

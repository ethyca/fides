from unittest import mock
from unittest.mock import Mock
import json

import pytest
from starlette.testclient import TestClient

from fidesops.api.v1.scope_registry import ENCRYPTION_EXEC, STORAGE_CREATE_OR_UPDATE
from fidesops.api.v1.urn_registry import (
    DECRYPT_AES,
    ENCRYPTION_KEY,
    ENCRYPT_AES,
    V1_URL_PREFIX,
)


class TestGetEnrcyptionKey:
    @pytest.fixture
    def url(self) -> str:
        return V1_URL_PREFIX + ENCRYPTION_KEY

    def test_get_encryption_key_not_authorized(self, api_client: TestClient, url):
        response = api_client.get(url)

        assert response.status_code == 401

    def test_get_encryption_key_wrong_scope(
        self, api_client: TestClient, url, generate_auth_header
    ):
        response = api_client.get(
            url, headers=generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        )
        assert response.status_code == 403

    @mock.patch(
        "fidesops.api.v1.endpoints.encryption_endpoints.cryptographic_util.generate_secure_random_string"
    )
    def test_get_encryption_key(
        self,
        mock_generate_secure_random: Mock,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        mock_generate_secure_random.return_value = "a key"

        response = api_client.get(url, headers=generate_auth_header([ENCRYPTION_EXEC]))

        assert response.status_code == 200
        assert response.text == '"' + mock_generate_secure_random.return_value + '"'


class TestAESEncrypt:
    @pytest.fixture
    def url(self) -> str:
        return V1_URL_PREFIX + ENCRYPT_AES

    def test_aes_encrypt_not_authorized(self, api_client: TestClient, url):
        request_body = {"value": "plain_val", "key": "key"}
        response = api_client.put(url, json=request_body)
        assert response.status_code == 401

    def test_aes_encrypt_wrong_scope(
        self, api_client: TestClient, url, generate_auth_header
    ):
        response = api_client.put(
            url, headers=generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        )
        assert response.status_code == 403

    @mock.patch(
        "fidesops.api.v1.endpoints.encryption_endpoints.cryptographic_util"
        ".generate_secure_random_string"
    )
    @mock.patch("fidesops.api.v1.endpoints.encryption_endpoints.aes_gcm_encrypt")
    def test_aes_encrypt(
        self,
        mock_aes_gcm_encrypt: Mock,
        mock_generate_secure_random: Mock,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        nonce_val = "a nonce"
        plain_val = "plain value"
        encrypted_val = "encrypted value"
        key = "the key"
        request_body = {"value": plain_val, "key": key}
        mock_generate_secure_random.return_value = nonce_val
        mock_aes_gcm_encrypt.return_value = encrypted_val

        response = api_client.put(
            url,
            headers=generate_auth_header([ENCRYPTION_EXEC]),
            json=request_body,
        )
        response_body = json.loads(response.text)

        assert response.status_code == 200
        assert response_body["encrypted_value"] == encrypted_val
        assert response_body["nonce"] == nonce_val


class TestAESDecrypt:
    @pytest.fixture
    def url(self) -> str:
        return V1_URL_PREFIX + DECRYPT_AES

    def test_aes_decrypt_not_authorized(
        self, url, api_client: TestClient, generate_auth_header
    ):
        request = {"value": "encrypted_value", "key": "key", "nonce": "nonce"}
        response = api_client.put(
            url,
            headers=generate_auth_header([]),
            json=request,
        )

        assert response.status_code == 403

    def test_aes_decrypt_wrong_scope(
        self, api_client: TestClient, url, generate_auth_header
    ):
        response = api_client.put(
            url, headers=generate_auth_header([STORAGE_CREATE_OR_UPDATE])
        )
        assert response.status_code == 403

    @mock.patch("fidesops.api.v1.endpoints.encryption_endpoints.aes_gcm_decrypt")
    def test_aes_decrypt(
        self,
        mock_aes_gcm_decrypt: Mock,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        encrypted_value = "ucenwic"
        key = "the key"
        decrypted_value = "value"
        nonce = "the nonce"
        request = {"value": encrypted_value, "key": key, "nonce": nonce}
        mock_aes_gcm_decrypt.return_value = decrypted_value

        response = api_client.put(
            url,
            headers=generate_auth_header([ENCRYPTION_EXEC]),
            json=request,
        )
        response_body = json.loads(response.text)

        assert response.status_code == 200
        assert response_body["decrypted_value"] == decrypted_value

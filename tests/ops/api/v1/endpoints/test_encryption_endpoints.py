import json
from unittest import mock
from unittest.mock import Mock

import pytest
from fideslib.cryptography.cryptographic_util import b64_str_to_bytes, bytes_to_b64_str
from fidesops.ops.api.v1.scope_registry import ENCRYPTION_EXEC, STORAGE_CREATE_OR_UPDATE
from fidesops.ops.api.v1.urn_registry import (
    DECRYPT_AES,
    ENCRYPT_AES,
    ENCRYPTION_KEY,
    V1_URL_PREFIX,
)
from fidesops.ops.core.config import config
from fidesops.ops.util.encryption.aes_gcm_encryption_scheme import (
    decrypt,
    encrypt_verify_secret_length,
)
from starlette.testclient import TestClient


class TestGetEncryptionKey:
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
        "fidesops.ops.api.v1.endpoints.encryption_endpoints.cryptographic_util.generate_secure_random_string"
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

    def test_invalid_key(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        plain_val = "plain value"
        key = "short"
        request_body = {"value": plain_val, "key": key}

        response = api_client.put(
            url,
            headers=generate_auth_header([ENCRYPTION_EXEC]),
            json=request_body,
        )
        assert response.status_code == 422

    def test_aes_encrypt(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        plain_val = "plain value"
        key = "zfkslapqlwodaqld"
        request_body = {"value": plain_val, "key": key}

        response = api_client.put(
            url,
            headers=generate_auth_header([ENCRYPTION_EXEC]),
            json=request_body,
        )
        response_body = json.loads(response.text)
        encrypted_value = response_body["encrypted_value"]
        nonce = b64_str_to_bytes(response_body["nonce"])

        assert response.status_code == 200
        decrypted = decrypt(
            encrypted_value,
            key.encode(config.security.encoding),
            nonce,
        )
        assert decrypted == plain_val


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

    def test_aes_decrypt(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
    ):
        key = "zfkslapqlwodaqld"
        nonce = b'\x18\xf5"+\xdbj\xe6O\xc7|\x19\xd2'
        orig_data = "test_data"
        encrypted_data = encrypt_verify_secret_length(
            orig_data, key.encode(config.security.encoding), nonce
        )

        request = {
            "value": encrypted_data,
            "key": key,
            "nonce": bytes_to_b64_str(nonce),
        }

        response = api_client.put(
            url,
            headers=generate_auth_header([ENCRYPTION_EXEC]),
            json=request,
        )
        response_body = json.loads(response.text)

        assert response.status_code == 200
        assert response_body["decrypted_value"] == orig_data

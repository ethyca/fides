import json
from unittest import mock

import pytest

from fides.api.ops.api.v1.scope_registry import (
    ENCRYPTION_EXEC,
    STORAGE_CREATE_OR_UPDATE,
)
from fides.api.ops.api.v1.urn_registry import (
    DECRYPT_AES,
    ENCRYPT_AES,
    ENCRYPTION_KEY,
    V1_URL_PREFIX,
)
from fides.api.ops.util.encryption.aes_gcm_encryption_scheme import (
    decrypt,
    encrypt_verify_secret_length,
)
from fides.core.config import get_config
from fides.lib.cryptography.cryptographic_util import b64_str_to_bytes, bytes_to_b64_str

CONFIG = get_config()


class TestGetEncryptionKey:
    @pytest.fixture
    def url(self):
        return V1_URL_PREFIX + ENCRYPTION_KEY

    def test_get_encryption_key_not_authorized(self, api_client, url):
        response = api_client.get(url)

        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_get_encryption_key_wrong_scope(self, auth_header, api_client, url):
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[ENCRYPTION_EXEC]], indirect=True)
    @mock.patch(
        "fides.api.ops.api.v1.endpoints.encryption_endpoints.cryptographic_util.generate_secure_random_string"
    )
    def test_get_encryption_key(
        self,
        mock_generate_secure_random,
        auth_header,
        api_client,
        url,
    ):
        mock_generate_secure_random.return_value = "a key"

        response = api_client.get(url, headers=auth_header)

        assert response.status_code == 200
        assert response.text == '"' + mock_generate_secure_random.return_value + '"'


class TestAESEncrypt:
    @pytest.fixture
    def url(self):
        return V1_URL_PREFIX + ENCRYPT_AES

    def test_aes_encrypt_not_authorized(self, api_client, url):
        request_body = {"value": "plain_val", "key": "key"}
        response = api_client.put(url, json=request_body)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_aes_encrypt_wrong_scope(self, auth_header, api_client, url):
        response = api_client.put(url, headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[ENCRYPTION_EXEC]], indirect=True)
    def test_invalid_key(self, auth_header, url, api_client):
        plain_val = "plain value"
        key = "short"
        request_body = {"value": plain_val, "key": key}

        response = api_client.put(url, headers=auth_header, json=request_body)
        assert response.status_code == 422

    @pytest.mark.parametrize("auth_header", [[ENCRYPTION_EXEC]], indirect=True)
    def test_aes_encrypt(self, auth_header, url, api_client):
        plain_val = "plain value"
        key = "zfkslapqlwodaqld"
        request_body = {"value": plain_val, "key": key}

        response = api_client.put(url, headers=auth_header, json=request_body)
        response_body = json.loads(response.text)
        encrypted_value = response_body["encrypted_value"]
        nonce = b64_str_to_bytes(response_body["nonce"])

        assert response.status_code == 200
        decrypted = decrypt(
            encrypted_value,
            key.encode(CONFIG.security.encoding),
            nonce,
        )
        assert decrypted == plain_val


class TestAESDecrypt:
    @pytest.fixture
    def url(self):
        return V1_URL_PREFIX + DECRYPT_AES

    @pytest.mark.parametrize("auth_header", [[]], indirect=True)
    def test_aes_decrypt_not_authorized(self, auth_header, url, api_client):
        request = {"value": "encrypted_value", "key": "key", "nonce": "nonce"}
        response = api_client.put(url, headers=auth_header, json=request)

        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[STORAGE_CREATE_OR_UPDATE]], indirect=True)
    def test_aes_decrypt_wrong_scope(self, auth_header, api_client, url):
        response = api_client.put(url, headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[ENCRYPTION_EXEC]], indirect=True)
    def test_aes_decrypt(self, auth_header, url, api_client):
        key = "zfkslapqlwodaqld"
        nonce = b'\x18\xf5"+\xdbj\xe6O\xc7|\x19\xd2'
        orig_data = "test_data"
        encrypted_data = encrypt_verify_secret_length(
            orig_data, key.encode(CONFIG.security.encoding), nonce
        )

        request = {
            "value": encrypted_data,
            "key": key,
            "nonce": bytes_to_b64_str(nonce),
        }

        response = api_client.put(url, headers=auth_header, json=request)
        response_body = json.loads(response.text)

        assert response.status_code == 200
        assert response_body["decrypted_value"] == orig_data

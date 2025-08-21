"""Tests for the AzureStorageClient class."""

import pytest

from fides.api.service.storage.streaming.azure.azure_storage_client import (
    AzureStorageClient,
)


class TestAzureStorageClient:
    """Test the AzureStorageClient class."""

    def test_init_stores_storage_secrets(self):
        """Test that __init__ properly stores storage secrets."""
        secrets = {"account_name": "testaccount"}
        client = AzureStorageClient(secrets)
        assert client.storage_secrets == secrets

    def test_build_uri_success(self):
        """Test Azure URI construction success."""
        secrets = {"account_name": "testaccount"}
        client = AzureStorageClient(secrets)
        with pytest.raises(NotImplementedError):
            client.build_uri("test-container", "test-key")

    def test_build_uri_missing_account_name(self):
        """Test Azure URI construction failure when account_name is missing."""
        secrets = {}
        client = AzureStorageClient(secrets)

        with pytest.raises(NotImplementedError):
            client.build_uri("test-container", "test-key")

    def test_get_transport_params_with_all_keys(self):
        """Test transport params with all Azure keys."""
        secrets = {
            "account_name": "testaccount",
            "account_key": "testkey",
            "sas_token": "testsas",
        }
        client = AzureStorageClient(secrets)
        with pytest.raises(NotImplementedError):
            client.get_transport_params()

    def test_get_transport_params_with_partial_keys(self):
        """Test transport params with partial Azure keys."""
        secrets = {
            "account_name": "testaccount",
            "account_key": "testkey",
        }
        client = AzureStorageClient(secrets)
        with pytest.raises(NotImplementedError):
            client.get_transport_params()

    def test_get_transport_params_only_account_name(self):
        """Test transport params with only account_name."""
        secrets = {"account_name": "testaccount"}
        client = AzureStorageClient(secrets)
        with pytest.raises(NotImplementedError):
            client.get_transport_params()

    def test_generate_presigned_url_not_implemented(self):
        """Test that presigned URL generation raises NotImplementedError."""
        secrets = {"account_name": "testaccount"}
        client = AzureStorageClient(secrets)

        with pytest.raises(
            NotImplementedError,
            match="Presigned URL generation not yet implemented for Azure storage",
        ):
            client.generate_presigned_url("test-container", "test-key")

    def test_generate_presigned_url_error_message_includes_context(self):
        """Test that error message includes container and key context."""
        secrets = {"account_name": "testaccount"}
        client = AzureStorageClient(secrets)

        with pytest.raises(NotImplementedError) as exc_info:
            client.generate_presigned_url("test-container", "test-key")

        error_message = str(exc_info.value)
        assert "test-container" in error_message
        assert "test-key" in error_message

"""Tests for the GCSStorageClient class."""

from unittest.mock import Mock, patch

import pytest

from fides.api.schemas.storage.storage import GCSAuthMethod
from fides.api.service.storage.streaming.gcs.gcs_storage_client import GCSStorageClient


class TestGCSStorageClient:
    """Test the GCSStorageClient class."""

    def test_init_stores_storage_secrets(self):
        """Test that __init__ properly stores storage secrets."""
        secrets = {"service_account_info": {"type": "service_account"}}
        client = GCSStorageClient(secrets)
        assert client.storage_secrets == secrets

    def test_build_uri(self):
        """Test GCS URI construction."""
        secrets = {"service_account_info": {"type": "service_account"}}
        client = GCSStorageClient(secrets)
        uri = client.build_uri("test-bucket", "test-key")
        assert uri == "gs://test-bucket/test-key"

    def test_get_transport_params_service_account_info(self):
        """Test transport params with service account info."""
        secrets = {"service_account_info": {"type": "service_account"}}
        client = GCSStorageClient(secrets)
        params = client.get_transport_params()

        assert params["credentials"] == {"type": "service_account"}

    def test_get_transport_params_service_account_file(self):
        """Test transport params with service account file."""
        secrets = {"service_account_file": "/path/to/service-account.json"}
        client = GCSStorageClient(secrets)
        params = client.get_transport_params()

        assert params["credentials"] == "/path/to/service-account.json"

    def test_get_transport_params_no_credentials(self):
        """Test transport params with no credentials."""
        secrets = {}
        client = GCSStorageClient(secrets)
        params = client.get_transport_params()

        assert params == {}

    @patch("fides.api.service.storage.streaming.gcs.gcs_storage_client.get_gcs_blob")
    def test_generate_presigned_url_success(self, mock_get_gcs_blob):
        """Test successful signed URL generation."""
        mock_blob = Mock()
        mock_blob.generate_signed_url.return_value = "https://test-url.com"
        mock_get_gcs_blob.return_value = mock_blob

        secrets = {
            "private_key_id": "test_key_id",
            "private_key": "test_private_key",
            "client_email": "test@example.com",
            "client_id": "test_client_id",
            "type": "service_account",
        }
        client = GCSStorageClient(secrets)

        result = client.generate_presigned_url("test-bucket", "test-key", 3600)

        assert result == "https://test-url.com"
        mock_get_gcs_blob.assert_called_once()
        mock_blob.reload.assert_called_once()
        mock_blob.generate_signed_url.assert_called_once_with(
            version="v4", expiration=3600, method="GET"
        )

    @patch("fides.api.service.storage.streaming.gcs.gcs_storage_client.get_gcs_blob")
    def test_generate_presigned_url_default_ttl(self, mock_get_gcs_blob):
        """Test signed URL generation with default TTL."""
        mock_blob = Mock()
        mock_blob.generate_signed_url.return_value = "https://test-url.com"
        mock_get_gcs_blob.return_value = mock_blob

        # Mock CONFIG to return a default TTL
        with patch(
            "fides.api.service.storage.streaming.gcs.gcs_storage_client.CONFIG"
        ) as mock_config:
            mock_config.security.subject_request_download_link_ttl_seconds = 7200

            secrets = {"private_key_id": "test_key_id"}
            client = GCSStorageClient(secrets)

            result = client.generate_presigned_url("test-bucket", "test-key")

            assert result == "https://test-url.com"
            mock_blob.generate_signed_url.assert_called_once_with(
                version="v4", expiration=7200, method="GET"
            )

    @patch("fides.api.service.storage.streaming.gcs.gcs_storage_client.get_gcs_blob")
    def test_generate_presigned_url_failure(self, mock_get_gcs_blob):
        """Test signed URL generation failure."""
        mock_get_gcs_blob.side_effect = Exception("GCS blob error")

        secrets = {"private_key_id": "test_key_id"}
        client = GCSStorageClient(secrets)

        with pytest.raises(Exception, match="GCS blob error"):
            client.generate_presigned_url("test-bucket", "test-key")

    def test_generate_presigned_url_default_auth_method(self):
        """Test that default auth method is used when not specified."""
        secrets = {"private_key_id": "test_key_id"}
        client = GCSStorageClient(secrets)

        # This should not raise an error about missing auth_method
        assert client.storage_secrets.get("auth_method") is None

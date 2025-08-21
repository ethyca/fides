"""Tests for the S3StorageClient class."""

from unittest.mock import Mock, patch

import pytest

from fides.api.schemas.storage.storage import AWSAuthMethod, StorageSecrets
from fides.api.service.storage.streaming.s3.s3_storage_client import S3StorageClient


class TestS3StorageClient:
    """Test the S3StorageClient class."""

    def test_init_stores_storage_secrets(self):
        """Test that __init__ properly stores storage secrets."""
        secrets = {"aws_access_key_id": "test_key"}
        client = S3StorageClient(secrets)
        assert client.storage_secrets == secrets

    def test_build_uri_standard_s3(self):
        """Test S3 URI construction for standard AWS."""
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
        }
        client = S3StorageClient(secrets)
        uri = client.build_uri("test-bucket", "test-key")
        assert uri == "s3://test-bucket/test-key"

    def test_build_uri_custom_endpoint(self):
        """Test S3 URI construction for custom endpoint (e.g., MinIO)."""
        secrets = {
            "aws_access_key_id": "test_key",
            "endpoint_url": "http://localhost:9000",
        }
        client = S3StorageClient(secrets)
        uri = client.build_uri("test-bucket", "test-key")
        assert uri == "http://localhost:9000/test-bucket/test-key"

    def test_get_transport_params_with_all_keys(self):
        """Test transport params with all S3 keys."""
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region": "us-west-2",
            "endpoint_url": "http://localhost:9000",
        }
        client = S3StorageClient(secrets)
        params = client.get_transport_params()

        assert params["access_key"] == "test_key"
        assert params["secret_key"] == "test_secret"
        assert params["region"] == "us-west-2"
        assert params["endpoint_url"] == "http://localhost:9000"

    def test_get_transport_params_with_partial_keys(self):
        """Test transport params with partial S3 keys."""
        secrets = {
            "aws_access_key_id": "test_key",
            "region": "us-west-2",
        }
        client = S3StorageClient(secrets)
        params = client.get_transport_params()

        assert params["access_key"] == "test_key"
        assert params["region"] == "us-west-2"
        assert "secret_key" not in params
        assert "endpoint_url" not in params

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_success(
        self, mock_create_presigned, mock_get_s3_client
    ):
        """Test successful presigned URL generation."""
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_create_presigned.return_value = "https://test-url.com"

        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region": "us-west-2",
        }
        client = S3StorageClient(secrets)

        result = client.generate_presigned_url("test-bucket", "test-key", 3600)

        assert result == "https://test-url.com"
        mock_get_s3_client.assert_called_once()
        mock_create_presigned.assert_called_once_with(
            mock_s3_client, "test-bucket", "test-key", 3600
        )

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    def test_generate_presigned_url_failure(self, mock_get_s3_client):
        """Test presigned URL generation failure."""
        mock_get_s3_client.side_effect = Exception("S3 client error")

        secrets = {"aws_access_key_id": "test_key"}
        client = S3StorageClient(secrets)

        with pytest.raises(Exception, match="S3 client error"):
            client.generate_presigned_url("test-bucket", "test-key")

    def test_generate_presigned_url_default_auth_method(self):
        """Test that default auth method is used when not specified."""
        secrets = {"aws_access_key_id": "test_key"}
        client = S3StorageClient(secrets)

        # This should not raise an error about missing auth_method
        assert client.storage_secrets.get("auth_method") is None

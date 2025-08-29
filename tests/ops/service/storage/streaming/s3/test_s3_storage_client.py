"""Tests for S3StorageClient."""

from unittest.mock import Mock, patch

import pytest
from moto import mock_aws

from fides.api.schemas.storage.storage import AWSAuthMethod
from fides.api.service.storage.streaming.s3.s3_storage_client import S3StorageClient


class TestS3StorageClient:
    """Test the S3StorageClient class."""

    def test_init_stores_storage_secrets(self):
        """Test that __init__ properly stores storage secrets."""
        auth_method = "secret_keys"
        secrets = {"aws_access_key_id": "test_key"}
        client = S3StorageClient(auth_method, secrets)
        assert client.storage_secrets == secrets

    def test_build_uri_standard_s3(self):
        """Test S3 URI construction for standard AWS."""
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
        }
        client = S3StorageClient(auth_method, secrets)
        uri = client.build_uri("test-bucket", "test-key")
        assert uri == "s3://test-bucket/test-key"

    def test_build_uri_custom_endpoint(self):
        """Test S3 URI construction for custom endpoint (e.g., MinIO)."""
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
        }
        client = S3StorageClient(auth_method, secrets)
        uri = client.build_uri("test-bucket", "test-key")
        # Since we no longer support custom endpoints in the current implementation,
        # this will use standard S3 URI
        assert uri == "s3://test-bucket/test-key"

    @mock_aws
    def test_get_transport_params_with_all_keys(self):
        """Test transport params with all S3 keys."""
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
        }
        client = S3StorageClient(auth_method, secrets)
        params = client.get_transport_params()

        # Should have S3 client instance
        assert "client" in params
        assert params["client"] is not None

        # When using an S3 client, credential parameters are not included
        # to avoid smart-open warnings about ignored parameters
        assert "access_key" not in params
        assert "secret_key" not in params
        assert "region" not in params
        # endpoint_url is no longer supported in the current implementation

    @mock_aws
    def test_get_transport_params_with_partial_keys(self):
        """Test transport params with partial S3 keys."""
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "region_name": "us-west-2",
        }
        client = S3StorageClient(auth_method, secrets)
        params = client.get_transport_params()

        # Should have S3 client instance
        assert "client" in params
        assert params["client"] is not None

        # When using an S3 client, credential parameters are not included
        # to avoid smart-open warnings about ignored parameters
        assert "access_key" not in params
        assert "region" not in params
        assert "secret_key" not in params
        # endpoint_url is no longer supported in the current implementation

    @mock_aws
    def test_get_transport_params_with_assume_role_arn(self):
        """Test transport params include assume_role_arn when present."""
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        client = S3StorageClient(auth_method, secrets)
        params = client.get_transport_params()

        # Should have S3 client instance
        assert "client" in params
        assert params["client"] is not None

        # When using an S3 client, credential parameters are not included
        # to avoid smart-open warnings about ignored parameters
        assert "access_key" not in params
        assert "secret_key" not in params
        assert "region" not in params
        assert "assume_role_arn" not in params

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    def test_get_transport_params_fallback_without_client(self, mock_get_s3_client):
        """Test transport params include credential parameters when no S3 client is available."""
        # Mock get_s3_client to return None (simulating failure)
        mock_get_s3_client.return_value = None

        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
        }
        client = S3StorageClient(auth_method, secrets)

        # This shouldn't raise an exception since we can pass the transport params
        transport_params = client.get_transport_params()
        assert transport_params is not None
        assert "access_key" in transport_params
        assert "secret_key" in transport_params
        assert "region" in transport_params
        assert "assume_role_arn" not in transport_params

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    def test_get_transport_params_automatic_auth_failure(self, mock_get_s3_client):
        """Test that automatic authentication failures provide helpful error messages."""
        # Mock get_s3_client to raise an exception
        mock_get_s3_client.side_effect = Exception("Unable to locate credentials")

        # No AWS credentials provided - should use automatic auth
        auth_method = "secret_keys"
        secrets = {"region_name": "us-west-2"}
        client = S3StorageClient(auth_method, secrets)

        with pytest.raises(ValueError, match="Automatic AWS authentication failed"):
            client.get_transport_params()

    @mock_aws
    def test_get_transport_params_without_assume_role_arn(self):
        """Test transport params don't include assume_role_arn when not present."""
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
        }
        client = S3StorageClient(auth_method, secrets)
        params = client.get_transport_params()

        # Should have S3 client instance
        assert "client" in params
        assert params["client"] is not None

        # When using an S3 client, credential parameters are not included
        # to avoid smart-open warnings about ignored parameters
        assert "access_key" not in params
        assert "secret_key" not in params
        assert "region" not in params
        assert "assume_role_arn" not in params

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

        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
        }
        client = S3StorageClient(auth_method, secrets)

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

        auth_method = "secret_keys"
        secrets = {"aws_access_key_id": "test_key"}
        client = S3StorageClient(auth_method, secrets)

        with pytest.raises(Exception, match="S3 client error"):
            client.generate_presigned_url("test-bucket", "test-key")

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_with_credentials_uses_secret_keys(
        self, mock_create_presigned, mock_get_s3_client
    ):
        """Test that SECRET_KEYS auth method is used when AWS credentials are present."""
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_create_presigned.return_value = "https://test-url.com"

        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
        }
        client = S3StorageClient(auth_method, secrets)

        result = client.generate_presigned_url("test-bucket", "test-key")

        assert result == "https://test-url.com"
        # Verify get_s3_client was called with SECRET_KEYS auth method
        mock_get_s3_client.assert_called_once_with(
            AWSAuthMethod.SECRET_KEYS.value, secrets, None
        )

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_without_credentials_uses_automatic(
        self, mock_create_presigned, mock_get_s3_client
    ):
        """Test that AUTOMATIC auth method is used when AWS credentials are not present."""
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_create_presigned.return_value = "https://test-url.com"

        # No AWS credentials provided
        auth_method = "secret_keys"
        secrets = {"region_name": "us-west-2"}
        client = S3StorageClient(auth_method, secrets)

        result = client.generate_presigned_url("test-bucket", "test-key")

        assert result == "https://test-url.com"
        # Verify get_s3_client was called with AUTOMATIC auth method
        mock_get_s3_client.assert_called_once_with(
            AWSAuthMethod.AUTOMATIC.value, secrets, None
        )

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_with_empty_credentials_uses_automatic(
        self, mock_create_presigned, mock_get_s3_client
    ):
        """Test that AUTOMATIC auth method is used when AWS credentials are empty strings."""
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_create_presigned.return_value = "https://test-url.com"

        # Empty AWS credentials
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
            "region_name": "us-west-2",
        }
        client = S3StorageClient(auth_method, secrets)

        result = client.generate_presigned_url("test-bucket", "test-key")

        assert result == "https://test-url.com"
        # Verify get_s3_client was called with AUTOMATIC auth method
        mock_get_s3_client.assert_called_once_with(
            AWSAuthMethod.AUTOMATIC.value, secrets, None
        )

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_with_assume_role_arn_secret_keys(
        self, mock_create_presigned, mock_get_s3_client
    ):
        """Test that assume_role_arn is passed when using SECRET_KEYS auth method."""
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_create_presigned.return_value = "https://test-url.com"

        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        client = S3StorageClient(auth_method, secrets)

        result = client.generate_presigned_url("test-bucket", "test-key")

        assert result == "https://test-url.com"
        # Verify get_s3_client was called with SECRET_KEYS auth method and assume_role_arn
        mock_get_s3_client.assert_called_once_with(
            AWSAuthMethod.SECRET_KEYS.value,
            secrets,
            "arn:aws:iam::123456789012:role/TestRole",
        )

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_with_assume_role_arn_automatic(
        self, mock_create_presigned, mock_get_s3_client
    ):
        """Test that assume_role_arn is passed when using AUTOMATIC auth method."""
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_create_presigned.return_value = "https://test-url.com"

        # No AWS credentials, but with assume_role_arn
        auth_method = "secret_keys"
        secrets = {
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        client = S3StorageClient(auth_method, secrets)

        result = client.generate_presigned_url("test-bucket", "test-key")

        assert result == "https://test-url.com"
        # Verify get_s3_client was called with AUTOMATIC auth method and assume_role_arn
        mock_get_s3_client.assert_called_once_with(
            AWSAuthMethod.AUTOMATIC.value,
            secrets,
            "arn:aws:iam::123456789012:role/TestRole",
        )

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_without_assume_role_arn(
        self, mock_create_presigned, mock_get_s3_client
    ):
        """Test that None is passed for assume_role_arn when not present."""
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_create_presigned.return_value = "https://test-url.com"

        # No assume_role_arn
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
        }
        client = S3StorageClient(auth_method, secrets)

        result = client.generate_presigned_url("test-bucket", "test-key")

        assert result == "https://test-url.com"
        # Verify get_s3_client was called with None for assume_role_arn
        mock_get_s3_client.assert_called_once_with(
            AWSAuthMethod.SECRET_KEYS.value, secrets, None
        )

    @patch("fides.api.service.storage.streaming.s3.s3_storage_client.get_s3_client")
    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_with_empty_assume_role_arn(
        self, mock_create_presigned, mock_get_s3_client
    ):
        """Test that empty assume_role_arn is treated as None."""
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_create_presigned.return_value = "https://test-url.com"

        # Empty assume_role_arn
        auth_method = "secret_keys"
        secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "",
        }
        client = S3StorageClient(auth_method, secrets)

        result = client.generate_presigned_url("test-bucket", "test-key")

        assert result == "https://test-url.com"
        # Verify get_s3_client was called with empty string for assume_role_arn
        mock_get_s3_client.assert_called_once_with(
            AWSAuthMethod.SECRET_KEYS.value, secrets, ""
        )

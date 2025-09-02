"""
Tests for streaming S3 functionality.

These tests verify the streaming S3 upload functions including error handling,
fallback behavior, and integration with the smart-open streaming implementation.
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import StorageSecrets, StorageSecretsS3
from fides.api.service.storage.streaming.s3.streaming_s3 import (
    format_secrets,
    upload_to_s3_streaming,
)


@pytest.fixture
def mock_storage_secrets():
    """Mock storage secrets for testing."""
    return {
        StorageSecrets.AWS_ACCESS_KEY_ID: "test_access_key",
        StorageSecrets.AWS_SECRET_ACCESS_KEY: "test_secret_key",
    }


@pytest.fixture
def mock_document():
    """Mock document for testing."""
    return BytesIO(b"test document content")


class TestFormatSecrets:
    """Tests for the format_secrets function."""

    def test_format_secrets_from_storage_secrets_s3_model(self):
        """Test formatting secrets from StorageSecretsS3 model."""
        storage_secrets = StorageSecretsS3(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-west-2",
            assume_role_arn="arn:aws:iam::123456789012:role/TestRole",
        )

        result = format_secrets(storage_secrets)

        expected = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        assert result == expected

    def test_format_secrets_from_storage_secrets_s3_model_with_none_values(self):
        """Test formatting secrets from StorageSecretsS3 model with None values."""
        storage_secrets = StorageSecretsS3(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-west-2",
            assume_role_arn=None,  # None value
        )

        result = format_secrets(storage_secrets)

        expected = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
        }
        assert result == expected
        assert "assume_role_arn" not in result

    def test_format_secrets_from_dict_with_enum_keys(self):
        """Test formatting secrets from dict with StorageSecrets enum keys."""
        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID: "test_key",
            StorageSecrets.AWS_SECRET_ACCESS_KEY: "test_secret",
            StorageSecrets.REGION_NAME: "us-west-2",
            StorageSecrets.AWS_ASSUME_ROLE: "arn:aws:iam::123456789012:role/TestRole",
        }

        result = format_secrets(storage_secrets)

        expected = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        assert result == expected

    def test_format_secrets_from_dict_with_string_keys(self):
        """Test formatting secrets from dict with string keys."""
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }

        result = format_secrets(storage_secrets)

        expected = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        assert result == expected

    def test_format_secrets_keeps_existing_region(self):
        """Test that existing region is preserved."""
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "eu-west-1",
        }

        result = format_secrets(storage_secrets)

        assert result["region_name"] == "eu-west-1"
        assert result["aws_access_key_id"] == "test_key"
        assert result["aws_secret_access_key"] == "test_secret"

    def test_format_secrets_validation_secret_keys_auth(self):
        """Test validation for SECRET_KEYS authentication method."""
        # Valid SECRET_KEYS auth - all required fields present
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
        }

        result = format_secrets(storage_secrets)
        assert result is not None  # Should not raise exception

    def test_format_secrets_validation_secret_keys_auth_missing_access_key(self):
        """Test validation fails when access key is missing for SECRET_KEYS auth."""
        storage_secrets = {
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
        }

        with pytest.raises(
            ValueError, match="Missing required AWS credentials for SECRET_KEYS auth"
        ):
            format_secrets(storage_secrets)

    def test_format_secrets_validation_secret_keys_auth_missing_secret_key(self):
        """Test validation fails when secret key is missing for SECRET_KEYS auth."""
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "region_name": "us-west-2",
        }

        with pytest.raises(
            ValueError, match="Missing required AWS credentials for SECRET_KEYS auth"
        ):
            format_secrets(storage_secrets)

    def test_format_secrets_validation_secret_keys_auth_missing_region(self):
        """Test that default region is set when region is missing for SECRET_KEYS auth."""
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
        }

        result = format_secrets(storage_secrets)

        # Should not raise exception, should set default region
        assert result["aws_access_key_id"] == "test_key"
        assert result["aws_secret_access_key"] == "test_secret"

    def test_format_secrets_validation_automatic_auth(self):
        """Test validation for AUTOMATIC authentication method."""
        # Valid AUTOMATIC auth - only region required
        storage_secrets = {
            "region_name": "us-west-2",
        }

        result = format_secrets(storage_secrets)
        assert result is not None  # Should not raise exception
        assert result["region_name"] == "us-west-2"

    def test_format_secrets_validation_automatic_auth_missing_region(self):
        """Test validation fails when region is missing for AUTOMATIC auth."""
        storage_secrets = {}

        with pytest.raises(
            ValueError,
            match="Missing required region_name for AUTOMATIC authentication",
        ):
            format_secrets(storage_secrets)

    def test_format_secrets_validation_automatic_auth_empty_region(self):
        """Test validation fails when region is empty for AUTOMATIC auth."""
        storage_secrets = {
            "region_name": "",
        }

        with pytest.raises(
            ValueError,
            match="Missing required region_name for AUTOMATIC authentication",
        ):
            format_secrets(storage_secrets)

    def test_format_secrets_with_assume_role_arn_secret_keys(self):
        """Test that assume_role_arn works with SECRET_KEYS authentication."""
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }

        result = format_secrets(storage_secrets)

        expected = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        assert result == expected

    def test_format_secrets_with_assume_role_arn_automatic(self):
        """Test that assume_role_arn works with AUTOMATIC authentication."""
        storage_secrets = {
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }

        result = format_secrets(storage_secrets)

        expected = {
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        assert result == expected

    def test_format_secrets_handles_none_input(self):
        """Test that None input is handled gracefully."""
        with pytest.raises(
            ValueError,
            match="Missing required region_name for AUTOMATIC authentication",
        ):
            format_secrets(None)

    def test_format_secrets_handles_empty_dict(self):
        """Test that empty dict input is handled gracefully."""
        with pytest.raises(
            ValueError,
            match="Missing required region_name for AUTOMATIC authentication",
        ):
            format_secrets({})

    def test_format_secrets_mixed_enum_and_string_keys(self):
        """Test that mixed enum and string keys work correctly."""
        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID: "test_key",
            "aws_secret_access_key": "test_secret",  # String key
            StorageSecrets.REGION_NAME: "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",  # String key
        }

        result = format_secrets(storage_secrets)

        expected = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        assert result == expected


class TestUploadToS3Streaming:
    """Tests for upload_to_s3_streaming function."""

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStorageClient")
    @patch(
        "fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStreamingStorage"
    )
    def test_successful_upload(
        self,
        mock_streaming_storage_class,
        mock_client_class,
        mock_storage_secrets,
        sample_data,
        mock_privacy_request,
        mock_document,
    ):
        """Test successful streaming upload to S3 using smart-open."""
        # Mock the client and streaming storage
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_storage = MagicMock()
        mock_storage.upload_to_storage_streaming.return_value = (
            "https://example.com/test-file.zip"
        )
        mock_streaming_storage_class.return_value = mock_storage

        result_url = upload_to_s3_streaming(
            storage_secrets=mock_storage_secrets,
            data=sample_data,
            bucket_name="test-bucket",
            file_key="test-file.zip",
            resp_format="zip",
            privacy_request=mock_privacy_request,
            document=None,  # Set to None to test streaming path
            auth_method="secret_keys",
            max_workers=3,
        )

        # Verify the result
        assert result_url == "https://example.com/test-file.zip"

        # Verify the client was created with formatted secrets (string keys + region)
        expected_secrets = {
            "aws_access_key_id": "test_access_key",
            "aws_secret_access_key": "test_secret_key",
        }
        mock_client_class.assert_called_once_with("s3", "secret_keys", expected_secrets)

        # Verify the streaming storage was created
        mock_streaming_storage_class.assert_called_once_with(mock_client)

        # Verify the upload was called
        mock_storage.upload_to_storage_streaming.assert_called_once_with(
            sample_data,
            mock_storage.upload_to_storage_streaming.call_args[0][1],  # config
            mock_privacy_request,
            None,  # document
        )

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.generic_upload_to_s3")
    def test_document_upload_path(
        self,
        mock_generic_upload,
        mock_storage_secrets,
        sample_data,
        mock_privacy_request,
        mock_document,
    ):
        """Test the document upload path that calls generic_upload_to_s3."""
        # Mock generic_upload_to_s3 to return success
        mock_generic_upload.return_value = (
            "bucket",
            "https://example.com/test-file.zip",
        )

        result_url = upload_to_s3_streaming(
            storage_secrets=mock_storage_secrets,
            data=sample_data,
            bucket_name="test-bucket",
            file_key="test-file.zip",
            resp_format="zip",
            privacy_request=mock_privacy_request,
            document=mock_document,  # Set document to trigger this path
            auth_method="secret_keys",
            max_workers=3,
        )

        # Verify the result
        assert result_url == "https://example.com/test-file.zip"

        # Verify generic_upload_to_s3 was called with formatted secrets
        mock_generic_upload.assert_called_once()
        call_args = mock_generic_upload.call_args
        expected_formatted_secrets = {
            "aws_access_key_id": "test_access_key",
            "aws_secret_access_key": "test_secret_key",
        }
        assert call_args[0][0] == expected_formatted_secrets  # secrets
        assert call_args[0][1] == "test-bucket"  # bucket_name
        assert call_args[0][2] == "test-file.zip"  # file_key
        assert call_args[0][3] == "secret_keys"  # auth_method
        assert call_args[0][4] == mock_document  # document

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStorageClient")
    def test_client_creation_failure(
        self,
        mock_client_class,
        mock_storage_secrets,
        sample_data,
        mock_privacy_request,
    ):
        """Test handling of client creation failure."""
        # Mock client creation to fail
        mock_client_class.side_effect = Exception("Failed to create client")

        with pytest.raises(
            StorageUploadError,
            match="Unexpected error during smart-open streaming upload",
        ):
            upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="secret_keys",
                max_workers=3,
            )

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStorageClient")
    @patch(
        "fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStreamingStorage"
    )
    def test_upload_failure(
        self,
        mock_streaming_storage_class,
        mock_client_class,
        mock_storage_secrets,
        sample_data,
        mock_privacy_request,
    ):
        """Test handling of upload failure."""
        # Mock the client and streaming storage
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_storage = MagicMock()
        mock_storage.upload_to_storage_streaming.side_effect = Exception(
            "Upload failed"
        )
        mock_streaming_storage_class.return_value = mock_storage

        with pytest.raises(
            StorageUploadError,
            match="Unexpected error during smart-open streaming upload",
        ):
            upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="secret_keys",
                max_workers=3,
            )

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStorageClient")
    @patch(
        "fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStreamingStorage"
    )
    def test_different_auth_methods(
        self,
        mock_streaming_storage_class,
        mock_client_class,
        mock_storage_secrets,
        sample_data,
        mock_privacy_request,
    ):
        """Test that different auth methods work correctly."""
        # Mock the client and streaming storage
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_storage = MagicMock()
        mock_storage.upload_to_storage_streaming.return_value = (
            "https://example.com/test-file.zip"
        )
        mock_streaming_storage_class.return_value = mock_storage

        # Test different auth methods
        auth_methods = ["secret_keys", "automatic", "iam_role"]

        for auth_method in auth_methods:
            mock_client_class.reset_mock()
            mock_streaming_storage_class.reset_mock()
            mock_storage.upload_to_storage_streaming.reset_mock()

            result_url = upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method=auth_method,
                max_workers=3,
            )

            # Verify the result
            assert result_url == "https://example.com/test-file.zip"

            # Verify the client was created with formatted secrets (string keys + region)
            expected_secrets = {
                "aws_access_key_id": "test_access_key",
                "aws_secret_access_key": "test_secret_key",
            }
            mock_client_class.assert_called_once_with(
                "s3", auth_method, expected_secrets
            )

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStorageClient")
    @patch(
        "fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStreamingStorage"
    )
    def test_different_response_formats(
        self,
        mock_streaming_storage_class,
        mock_client_class,
        mock_storage_secrets,
        sample_data,
        mock_privacy_request,
    ):
        """Test that different response formats work correctly."""
        # Mock the client and streaming storage
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_storage = MagicMock()
        mock_storage.upload_to_storage_streaming.return_value = (
            "https://example.com/test-file.zip"
        )
        mock_streaming_storage_class.return_value = mock_storage

        # Test different response formats
        response_formats = ["json", "csv", "zip", "html"]

        for resp_format in response_formats:
            mock_storage.upload_to_storage_streaming.reset_mock()

            result_url = upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format=resp_format,
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="secret_keys",
                max_workers=3,
            )

            # Verify the result
            assert result_url == "https://example.com/test-file.zip"

            # Verify the upload was called
            mock_storage.upload_to_storage_streaming.assert_called_once()

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStorageClient")
    @patch(
        "fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStreamingStorage"
    )
    def test_different_max_workers(
        self,
        mock_streaming_storage_class,
        mock_client_class,
        mock_storage_secrets,
        sample_data,
        mock_privacy_request,
    ):
        """Test that different max_workers values work correctly."""
        # Mock the client and streaming storage
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_storage = MagicMock()
        mock_storage.upload_to_storage_streaming.return_value = (
            "https://example.com/test-file.zip"
        )
        mock_streaming_storage_class.return_value = mock_storage

        # Test different max_workers values
        max_workers_values = [1, 5, 10, 20]

        for max_workers in max_workers_values:
            mock_storage.upload_to_storage_streaming.reset_mock()

            result_url = upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="secret_keys",
                max_workers=max_workers,
            )

            # Verify the result
            assert result_url == "https://example.com/test-file.zip"

            # Verify the upload was called
            mock_storage.upload_to_storage_streaming.assert_called_once()

    def test_empty_bucket_name(
        self, mock_storage_secrets, sample_data, mock_privacy_request
    ):
        """Test that upload fails with empty bucket name."""
        with pytest.raises(
            StorageUploadError, match="Storage identifier cannot be empty or whitespace"
        ):
            upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="secret_keys",
                max_workers=3,
            )

    def test_empty_file_key(
        self, mock_storage_secrets, sample_data, mock_privacy_request
    ):
        """Test that upload fails with empty file key."""
        with pytest.raises(
            StorageUploadError, match="Storage identifier cannot be empty or whitespace"
        ):
            upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="",
                resp_format="zip",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="secret_keys",
                max_workers=3,
            )

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStorageClient")
    @patch(
        "fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStreamingStorage"
    )
    def test_upload_with_automatic_auth_and_assume_role(
        self,
        mock_streaming_storage_class,
        mock_client_class,
        sample_data,
        mock_privacy_request,
    ):
        """Test upload with AUTOMATIC auth method and assume role ARN."""
        # Mock the client and streaming storage
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_storage = MagicMock()
        mock_storage.upload_to_storage_streaming.return_value = (
            "https://example.com/test-file.zip"
        )
        mock_streaming_storage_class.return_value = mock_storage

        # Use AUTOMATIC auth with assume role ARN
        storage_secrets = {
            StorageSecrets.REGION_NAME: "us-west-2",
            StorageSecrets.AWS_ASSUME_ROLE: "arn:aws:iam::123456789012:role/TestRole",
        }

        result_url = upload_to_s3_streaming(
            storage_secrets=storage_secrets,
            data=sample_data,
            bucket_name="test-bucket",
            file_key="test-file.zip",
            resp_format="zip",
            privacy_request=mock_privacy_request,
            document=None,
            auth_method="automatic",
            max_workers=3,
        )

        # Verify the result
        assert result_url == "https://example.com/test-file.zip"

        # Verify the client was created with formatted secrets (only region + assume role)
        expected_secrets = {
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        mock_client_class.assert_called_once_with("s3", "automatic", expected_secrets)

    @patch("fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStorageClient")
    @patch(
        "fides.api.service.storage.streaming.s3.streaming_s3.SmartOpenStreamingStorage"
    )
    def test_upload_with_secret_keys_auth_and_assume_role(
        self,
        mock_streaming_storage_class,
        mock_client_class,
        sample_data,
        mock_privacy_request,
    ):
        """Test upload with SECRET_KEYS auth method and assume role ARN."""
        # Mock the client and streaming storage
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_storage = MagicMock()
        mock_storage.upload_to_storage_streaming.return_value = (
            "https://example.com/test-file.zip"
        )
        mock_streaming_storage_class.return_value = mock_storage

        # Use SECRET_KEYS auth with assume role ARN
        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID: "test_key",
            StorageSecrets.AWS_SECRET_ACCESS_KEY: "test_secret",
            StorageSecrets.REGION_NAME: "us-west-2",
            StorageSecrets.AWS_ASSUME_ROLE: "arn:aws:iam::123456789012:role/TestRole",
        }

        result_url = upload_to_s3_streaming(
            storage_secrets=storage_secrets,
            data=sample_data,
            bucket_name="test-bucket",
            file_key="test-file.zip",
            resp_format="zip",
            privacy_request=mock_privacy_request,
            document=None,
            auth_method="secret_keys",
            max_workers=3,
        )

        # Verify the result
        assert result_url == "https://example.com/test-file.zip"

        # Verify the client was created with formatted secrets (all fields + assume role)
        expected_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-west-2",
            "assume_role_arn": "arn:aws:iam::123456789012:role/TestRole",
        }
        mock_client_class.assert_called_once_with("s3", "secret_keys", expected_secrets)

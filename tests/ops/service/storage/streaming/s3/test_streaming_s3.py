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
    convert_to_storage_secrets_format,
    update_storage_secrets_s3,
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

        # Verify the client was created with converted secrets (string keys)
        expected_secrets = {
            "aws_access_key_id": "test_access_key",
            "aws_secret_access_key": "test_secret_key",
        }
        mock_client_class.assert_called_once_with("s3", expected_secrets)

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

        # Verify generic_upload_to_s3 was called with converted secrets
        mock_generic_upload.assert_called_once()
        call_args = mock_generic_upload.call_args
        assert call_args[0][0] == mock_storage_secrets  # secrets
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
            StorageUploadError, match="Error creating smart-open S3 client"
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

            # Verify the client was created with converted secrets (string keys)
            expected_secrets = {
                "aws_access_key_id": "test_access_key",
                "aws_secret_access_key": "test_secret_key",
            }
            mock_client_class.assert_called_once_with("s3", expected_secrets)

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

    def test_no_privacy_request(self, mock_storage_secrets, sample_data):
        """Test that upload fails without privacy request."""
        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=None,
                document=None,
                auth_method="secret_keys",
                max_workers=3,
            )

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


@pytest.mark.parametrize(
    "secrets,error",
    [
        pytest.param(
            StorageSecretsS3(
                **{
                    "aws_access_key_id": "test",
                    "aws_secret_access_key": "test",
                    "region_name": "us-east-1",
                }
            ),
            False,
            id="StorageSecretsS3",
        ),
        pytest.param(
            StorageSecretsS3(
                **{
                    "aws_access_key_id": "test",
                    "aws_secret_access_key": "test",
                    "region_name": "us-east-1",
                    "assume_role_arn": None,
                }
            ),
            False,
            id="StorageSecretsS3_with_none_values",
        ),
        pytest.param(
            {
                StorageSecrets.AWS_ACCESS_KEY_ID: "test",
                StorageSecrets.AWS_SECRET_ACCESS_KEY: "test",
                StorageSecrets.REGION_NAME: "us-east-1",
            },
            False,
            id="dict[StorageSecrets, Any]",
        ),
        pytest.param(
            {
                StorageSecrets.AWS_ACCESS_KEY_ID: None,
                StorageSecrets.AWS_SECRET_ACCESS_KEY: None,
                StorageSecrets.REGION_NAME: "us-east-1",
                StorageSecrets.AWS_ASSUME_ROLE: "arn:aws:iam::123456789012:role/test-role",
            },
            False,
            id="dict[StorageSecrets, Any] with None values",
        ),
        pytest.param(
            {
                StorageSecrets.AWS_ACCESS_KEY_ID: "test",
                StorageSecrets.AWS_SECRET_ACCESS_KEY: "test",
                StorageSecrets.REGION_NAME: "us-east-1",
                "invalid_key": "invalid_value",
            },
            ValueError,
            id="dict[StorageSecrets, Any] with invalid key",
        ),
        pytest.param(
            ["potato", "coconut", "banana"],
            ValueError,
            id="invalid_object",
        ),
        pytest.param(
            MagicMock(
                spec=[]
            ),  # Mock object that's not StorageSecretsS3 and has no model_dump method
            ValueError,
            id="object_without_model_dump",
        ),
        pytest.param(
            MagicMock(
                keys=MagicMock(side_effect=AttributeError("keys not callable"))
            ),  # Object with non-callable keys
            ValueError,
            id="object_with_non_callable_keys",
        ),
    ],
)
def test_update_storage_secrets_s3(secrets, error):
    if error:
        with pytest.raises(error) as exc_info:
            update_storage_secrets_s3(secrets)
        assert (
            "Storage secrets must be of type StorageSecretsS3, or dict[StorageSecrets, Any]"
            in str(exc_info.value)
        )
    else:
        secrets_updated = update_storage_secrets_s3(secrets)
        assert isinstance(secrets_updated, dict)
        if not isinstance(secrets, dict):
            secrets_dict = secrets.model_dump()
        else:
            # Convert StorageSecrets enum keys to their values to match the function behavior
            secrets_dict = {k.value: v for k, v in secrets.items()}
        assert secrets_updated == secrets_dict


class TestConvertToStorageSecretsFormat:
    """Tests for convert_to_storage_secrets_format function."""

    def test_convert_storage_secrets_s3(self):
        """Test converting StorageSecretsS3 to dict[StorageSecrets, Any]."""
        storage_secrets = StorageSecretsS3(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1",
            assume_role_arn=None,
        )

        result = convert_to_storage_secrets_format(storage_secrets)

        # Should convert to dict with StorageSecrets enum keys
        assert StorageSecrets.AWS_ACCESS_KEY_ID in result
        assert StorageSecrets.AWS_SECRET_ACCESS_KEY in result
        assert StorageSecrets.REGION_NAME in result
        assert result[StorageSecrets.AWS_ACCESS_KEY_ID] == "test_key"
        assert result[StorageSecrets.AWS_SECRET_ACCESS_KEY] == "test_secret"
        assert result[StorageSecrets.REGION_NAME] == "us-east-1"
        # None values should be excluded
        assert StorageSecrets.AWS_ASSUME_ROLE not in result

    def test_convert_storage_secrets_s3_with_assume_role(self):
        """Test converting StorageSecretsS3 with assume_role_arn."""
        storage_secrets = StorageSecretsS3(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1",
            assume_role_arn="arn:aws:iam::123456789012:role/test-role",
        )

        result = convert_to_storage_secrets_format(storage_secrets)

        # Should include assume_role_arn since it's not None
        assert StorageSecrets.AWS_ASSUME_ROLE in result
        assert (
            result[StorageSecrets.AWS_ASSUME_ROLE]
            == "arn:aws:iam::123456789012:role/test-role"
        )

    def test_convert_dict_storage_secrets(self):
        """Test converting dict[StorageSecrets, Any] (already in correct format)."""
        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID: "test_key",
            StorageSecrets.AWS_SECRET_ACCESS_KEY: "test_secret",
            StorageSecrets.REGION_NAME: "us-east-1",
        }

        result = convert_to_storage_secrets_format(storage_secrets)

        # Should return the same dict unchanged
        assert result == storage_secrets

    def test_convert_dict_storage_secrets_with_none_values(self):
        """Test converting dict[StorageSecrets, Any] with None values."""
        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID: "test_key",
            StorageSecrets.AWS_SECRET_ACCESS_KEY: None,
            StorageSecrets.REGION_NAME: "us-east-1",
        }

        result = convert_to_storage_secrets_format(storage_secrets)

        # Should return the same dict unchanged, including None values
        assert result == storage_secrets

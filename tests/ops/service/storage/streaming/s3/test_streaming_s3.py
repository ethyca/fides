"""
Tests for streaming S3 functionality.

These tests verify the streaming S3 upload functions including error handling,
fallback behavior, and integration with the cloud-agnostic streaming implementation.
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, ParamValidationError
from fideslang.validation import AnyHttpUrlString

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.service.storage.streaming.s3.streaming_s3 import upload_to_s3_streaming


@pytest.fixture
def mock_storage_secrets():
    """Mock storage secrets for testing."""
    return {
        StorageSecrets.AWS_ACCESS_KEY_ID.value: "test_access_key",
        StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "test_secret_key",
    }


@pytest.fixture
def mock_privacy_request():
    """Mock privacy request object."""
    mock_pr = MagicMock()
    mock_pr.id = "test-request-123"
    return mock_pr


@pytest.fixture
def mock_document():
    """Mock document for testing."""
    return BytesIO(b"test document content")


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "test_dataset": [
            {
                "id": "1",
                "name": "Test User",
                "email": "test@example.com",
                "attachments": [
                    {"filename": "doc1.pdf", "url": "https://example.com/doc1.pdf"},
                    {"filename": "doc2.pdf", "url": "https://example.com/doc2.pdf"},
                ],
            }
        ]
    }


@pytest.fixture
def mock_storage_client():
    """Mock storage client for testing."""
    client = MagicMock()
    client.upload_object.return_value = ("https://example.com/test-file.zip", {})
    return client


class TestUploadToS3Streaming:
    """Tests for upload_to_s3_streaming function."""

    def test_successful_upload(
        self,
        mock_storage_secrets,
        sample_data,
        mock_privacy_request,
        mock_document,
        mock_storage_client,
    ):
        """Test successful streaming upload to S3."""
        with (
            patch(
                "fides.api.service.storage.streaming.s3.streaming_s3.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.s3.streaming_s3.upload_to_storage_streaming",
                return_value=("https://example.com/test-file.zip"),
            ),
        ):
            result_url = upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=mock_privacy_request,
                document=mock_document,
                auth_method="secret_keys",
                max_workers=3,
            )

            assert result_url == "https://example.com/test-file.zip"

    def test_fallback_to_generic_upload_when_no_privacy_request(
        self, mock_storage_secrets, mock_document
    ):
        """Test fallback to generic upload when privacy_request is None."""
        with patch(
            "fides.api.service.storage.streaming.s3.streaming_s3.generic_upload_to_s3"
        ) as mock_generic_upload:
            mock_generic_upload.return_value = (
                "https://example.com/test-file.zip",
                "https://example.com/test-file.zip",
            )

            result_url = upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data={},
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=None,
                document=mock_document,
                auth_method="secret_keys",
            )

            assert result_url == "https://example.com/test-file.zip"
            mock_generic_upload.assert_called_once()

    def test_error_when_no_privacy_request_and_no_document(self, mock_storage_secrets):
        """Test error when both privacy_request and document are None."""
        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data={},
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=None,
                document=None,
                auth_method="secret_keys",
            )

    def test_storage_client_creation_error(
        self, mock_storage_secrets, mock_privacy_request
    ):
        """Test error handling when storage client creation fails."""
        with patch(
            "fides.api.service.storage.streaming.s3.streaming_s3.get_storage_client",
            side_effect=ClientError(
                {"Error": {"Code": "InvalidParameter", "Message": "Invalid parameter"}},
                "CreateClient",
            ),
        ):
            with pytest.raises(StorageUploadError, match="Error getting s3 client"):
                upload_to_s3_streaming(
                    storage_secrets=mock_storage_secrets,
                    data={},
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="zip",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="secret_keys",
                )

    def test_param_validation_error(self, mock_storage_secrets, mock_privacy_request):
        """Test error handling when parameter validation fails."""
        with patch(
            "fides.api.service.storage.streaming.s3.streaming_s3.get_storage_client",
            side_effect=ParamValidationError(
                report="Invalid parameter value",
                param_name="storage_secrets",
                value=mock_storage_secrets,
            ),
        ):
            with pytest.raises(StorageUploadError, match="Error getting s3 client"):
                upload_to_s3_streaming(
                    storage_secrets=mock_storage_secrets,
                    data={},
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="zip",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="secret_keys",
                )

    def test_upload_execution_error(self, mock_storage_secrets, mock_privacy_request):
        """Test error handling when upload execution fails."""
        with (
            patch(
                "fides.api.service.storage.streaming.s3.streaming_s3.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.s3.streaming_s3.upload_to_storage_streaming",
                side_effect=ClientError(
                    {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
                    "PutObject",
                ),
            ),
        ):
            with pytest.raises(StorageUploadError, match="Error uploading to S3"):
                upload_to_s3_streaming(
                    storage_secrets=mock_storage_secrets,
                    data={},
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="zip",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="secret_keys",
                )

    def test_unexpected_error_during_upload(
        self, mock_storage_secrets, mock_privacy_request
    ):
        """Test error handling when unexpected errors occur during upload."""
        with (
            patch(
                "fides.api.service.storage.streaming.s3.streaming_s3.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.s3.streaming_s3.upload_to_storage_streaming",
                side_effect=Exception("Unexpected error"),
            ),
        ):
            with pytest.raises(
                StorageUploadError, match="Unexpected error during streaming upload"
            ):
                upload_to_s3_streaming(
                    storage_secrets=mock_storage_secrets,
                    data={},
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="zip",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="secret_keys",
                )

    def test_custom_max_workers(self, mock_storage_secrets, mock_privacy_request):
        """Test that custom max_workers parameter is passed through."""
        with (
            patch(
                "fides.api.service.storage.streaming.s3.streaming_s3.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.s3.streaming_s3.upload_to_storage_streaming"
            ) as mock_upload,
        ):
            mock_upload.return_value = ("https://example.com/test-file.zip",)

            upload_to_s3_streaming(
                storage_secrets=mock_storage_secrets,
                data={},
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="zip",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="secret_keys",
                max_workers=10,
            )

            # Verify max_workers was passed to upload function through config
            mock_upload.assert_called_once()
            call_args = mock_upload.call_args
            # The config object is at index 2, and max_workers should be in the config
            config_arg = call_args[0][2]
            assert config_arg.max_workers == 10

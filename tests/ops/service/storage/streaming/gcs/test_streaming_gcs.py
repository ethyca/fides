"""Tests for GCS streaming storage functionality."""

from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from google.cloud.exceptions import GoogleCloudError

from fides.api.common_exceptions import StorageUploadError
from fides.api.service.storage.streaming.gcs.streaming_gcs import (
    upload_to_gcs_resumable,
    upload_to_gcs_streaming,
    upload_to_gcs_streaming_advanced,
)
from fides.api.service.storage.streaming.schemas import ProcessingMetrics


class TestUploadToGCSStreaming:
    """Test cases for upload_to_gcs_streaming function."""

    @pytest.fixture
    def mock_storage_client(self):
        """Create a mock storage client."""
        client = Mock()
        client.create_multipart_upload.return_value = Mock(upload_id="test-upload-id")
        return client

    @pytest.fixture
    def mock_privacy_request(self):
        """Create a mock privacy request."""
        request = Mock()
        request.id = "test-request-id"
        return request

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return {
            "users": [
                {
                    "id": "user1",
                    "name": "Test User",
                    "attachments": [
                        {"s3_key": "attachment1.pdf", "size": 1024},
                        {"s3_key": "attachment2.jpg", "size": 2048},
                    ],
                }
            ]
        }

    @pytest.fixture
    def storage_secrets(self):
        """Create sample storage secrets."""
        return {
            "type": "gcs",
            "project_id": "test-project",
            "bucket": "test-bucket",
        }

    def test_upload_to_gcs_streaming_success(
        self, mock_storage_client, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test successful GCS streaming upload."""
        with (
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.upload_to_storage_streaming",
                return_value=(
                    "https://storage.googleapis.com/test-bucket/test-file.zip",
                    ProcessingMetrics(),
                ),
            ),
        ):
            result, metrics = upload_to_gcs_streaming(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="service_account",
            )

            assert result == "https://storage.googleapis.com/test-bucket/test-file.zip"
            assert isinstance(metrics, ProcessingMetrics)

    def test_upload_to_gcs_streaming_with_document_no_privacy_request(
        self, storage_secrets, sample_data
    ):
        """Test GCS streaming upload with document but no privacy request."""
        mock_document = BytesIO(b"test content")

        with patch(
            "fides.api.service.storage.streaming.gcs.streaming_gcs.generic_upload_to_gcs",
            return_value=(
                None,
                "https://storage.googleapis.com/test-bucket/test-file.zip",
            ),
        ):
            result, metrics = upload_to_gcs_streaming(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=mock_document,
                auth_method="service_account",
            )

            assert result == "https://storage.googleapis.com/test-bucket/test-file.zip"
            assert isinstance(metrics, ProcessingMetrics)

    def test_upload_to_gcs_streaming_no_privacy_request_no_document(
        self, storage_secrets, sample_data
    ):
        """Test GCS streaming upload with no privacy request and no document."""
        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_gcs_streaming(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=None,
                auth_method="service_account",
            )

    def test_upload_to_gcs_streaming_client_error(
        self, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test GCS streaming upload with client creation error."""
        with patch(
            "fides.api.service.storage.streaming.gcs.streaming_gcs.get_storage_client",
            side_effect=GoogleCloudError("Failed to create client"),
        ):
            with pytest.raises(StorageUploadError, match="Error getting GCS client"):
                upload_to_gcs_streaming(
                    storage_secrets=storage_secrets,
                    data=sample_data,
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="json",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="service_account",
                )

    def test_upload_to_gcs_streaming_upload_error(
        self, mock_storage_client, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test GCS streaming upload with upload error."""
        with (
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.upload_to_storage_streaming",
                side_effect=GoogleCloudError("Upload failed"),
            ),
        ):
            with pytest.raises(StorageUploadError, match="Error uploading to GCS"):
                upload_to_gcs_streaming(
                    storage_secrets=storage_secrets,
                    data=sample_data,
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="json",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="service_account",
                )

    def test_upload_to_gcs_streaming_unexpected_error(
        self, mock_storage_client, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test GCS streaming upload with unexpected error."""
        with (
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.upload_to_storage_streaming",
                side_effect=Exception("Unexpected error"),
            ),
        ):
            with pytest.raises(
                StorageUploadError, match="Unexpected error during streaming upload"
            ):
                upload_to_gcs_streaming(
                    storage_secrets=storage_secrets,
                    data=sample_data,
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="json",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="service_account",
                )


class TestUploadToGCSStreamingAdvanced:
    """Test cases for upload_to_gcs_streaming_advanced function."""

    @pytest.fixture
    def mock_privacy_request(self):
        """Create a mock privacy request."""
        request = Mock()
        request.id = "test-request-id"
        return request

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return {"users": [{"id": "user1", "name": "Test User"}]}

    @pytest.fixture
    def storage_secrets(self):
        """Create sample storage secrets."""
        return {
            "type": "gcs",
            "project_id": "test-project",
            "bucket": "test-bucket",
        }

    def test_upload_to_gcs_streaming_advanced_success(
        self, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test successful advanced GCS streaming upload."""
        with patch(
            "fides.api.service.storage.streaming.gcs.streaming_gcs.upload_to_gcs_streaming",
            return_value=(
                "https://storage.googleapis.com/test-bucket/test-file.zip",
                ProcessingMetrics(),
            ),
        ):
            result, metrics = upload_to_gcs_streaming_advanced(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="service_account",
            )

            assert result == "https://storage.googleapis.com/test-bucket/test-file.zip"
            assert isinstance(metrics, ProcessingMetrics)

    def test_upload_to_gcs_streaming_advanced_with_document_no_privacy_request(
        self, sample_data, storage_secrets
    ):
        """Test advanced GCS streaming upload with document but no privacy request."""
        mock_document = BytesIO(b"test content")

        with patch(
            "fides.api.service.storage.streaming.gcs.streaming_gcs.generic_upload_to_gcs",
            return_value=(
                None,
                "https://storage.googleapis.com/test-bucket/test-file.zip",
            ),
        ):
            result, metrics = upload_to_gcs_streaming_advanced(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=mock_document,
                auth_method="service_account",
            )

            assert result == "https://storage.googleapis.com/test-bucket/test-file.zip"
            assert isinstance(metrics, ProcessingMetrics)

    def test_upload_to_gcs_streaming_advanced_no_privacy_request_no_document(
        self, sample_data, storage_secrets
    ):
        """Test advanced GCS streaming upload with no privacy request and no document."""
        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_gcs_streaming_advanced(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=None,
                auth_method="service_account",
            )

    def test_upload_to_gcs_streaming_advanced_error(
        self, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test advanced GCS streaming upload with error."""
        with patch(
            "fides.api.service.storage.streaming.gcs.streaming_gcs.upload_to_gcs_streaming",
            side_effect=Exception("Upload failed"),
        ):
            with pytest.raises(
                StorageUploadError,
                match="Unexpected error during advanced streaming upload",
            ):
                upload_to_gcs_streaming_advanced(
                    storage_secrets=storage_secrets,
                    data=sample_data,
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="json",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="service_account",
                )


class TestUploadToGCSResumable:
    """Test cases for upload_to_gcs_resumable function."""

    @pytest.fixture
    def mock_storage_client(self):
        """Create a mock storage client."""
        client = Mock()
        client.create_multipart_upload.return_value = Mock(upload_id="test-upload-id")
        return client

    @pytest.fixture
    def mock_privacy_request(self):
        """Create a mock privacy request."""
        request = Mock()
        request.id = "test-request-id"
        return request

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return {"users": [{"id": "user1", "name": "Test User"}]}

    @pytest.fixture
    def storage_secrets(self):
        """Create sample storage secrets."""
        return {
            "type": "gcs",
            "project_id": "test-project",
            "bucket": "test-bucket",
        }

    def test_upload_to_gcs_resumable_success(
        self, mock_storage_client, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test successful GCS resumable upload."""
        with (
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.upload_to_storage_streaming",
                return_value=(
                    "https://storage.googleapis.com/test-bucket/test-file.zip",
                    ProcessingMetrics(),
                ),
            ),
        ):
            result, metrics = upload_to_gcs_resumable(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=mock_privacy_request,
                document=None,
                auth_method="service_account",
            )

            assert result == "https://storage.googleapis.com/test-bucket/test-file.zip"
            assert isinstance(metrics, ProcessingMetrics)

    def test_upload_to_gcs_resumable_with_document_no_privacy_request(
        self, sample_data, storage_secrets
    ):
        """Test GCS resumable upload with document but no privacy request."""
        mock_document = BytesIO(b"test content")

        with patch(
            "fides.api.service.storage.streaming.gcs.streaming_gcs.generic_upload_to_gcs",
            return_value=(
                None,
                "https://storage.googleapis.com/test-bucket/test-file.zip",
            ),
        ):
            result, metrics = upload_to_gcs_resumable(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=mock_document,
                auth_method="service_account",
            )

            assert result == "https://storage.googleapis.com/test-bucket/test-file.zip"
            assert isinstance(metrics, ProcessingMetrics)

    def test_upload_to_gcs_resumable_no_privacy_request_no_document(
        self, sample_data, storage_secrets
    ):
        """Test GCS resumable upload with no privacy request and no document."""
        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_gcs_resumable(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=None,
                auth_method="service_account",
            )

    def test_upload_to_gcs_resumable_client_error(
        self, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test GCS resumable upload with client creation error."""
        with patch(
            "fides.api.service.storage.streaming.gcs.streaming_gcs.get_storage_client",
            side_effect=GoogleCloudError("Failed to create client"),
        ):
            with pytest.raises(
                StorageUploadError, match="Error during GCS resumable upload"
            ):
                upload_to_gcs_resumable(
                    storage_secrets=storage_secrets,
                    data=sample_data,
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="json",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="service_account",
                )

    def test_upload_to_gcs_resumable_upload_error(
        self, mock_storage_client, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test GCS resumable upload with upload error."""
        with (
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.upload_to_storage_streaming",
                side_effect=GoogleCloudError("Upload failed"),
            ),
        ):
            with pytest.raises(
                StorageUploadError, match="Error during GCS resumable upload"
            ):
                upload_to_gcs_resumable(
                    storage_secrets=storage_secrets,
                    data=sample_data,
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="json",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="service_account",
                )

    def test_upload_to_gcs_resumable_unexpected_error(
        self, mock_storage_client, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test GCS resumable upload with unexpected error."""
        with (
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.get_storage_client",
                return_value=mock_storage_client,
            ),
            patch(
                "fides.api.service.storage.streaming.gcs.streaming_gcs.upload_to_storage_streaming",
                side_effect=Exception("Unexpected error"),
            ),
        ):
            with pytest.raises(
                StorageUploadError, match="Unexpected error during GCS resumable upload"
            ):
                upload_to_gcs_resumable(
                    storage_secrets=storage_secrets,
                    data=sample_data,
                    bucket_name="test-bucket",
                    file_key="test-file.zip",
                    resp_format="json",
                    privacy_request=mock_privacy_request,
                    document=None,
                    auth_method="service_account",
                )

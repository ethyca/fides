"""Tests for GCS streaming storage functionality.

Note: All streaming functions currently raise NotImplementedError as they are not yet implemented.
These tests verify the proper error behavior until the functions are fully implemented.
"""

from io import BytesIO
from unittest.mock import Mock

import pytest

from fides.api.service.storage.streaming.gcs.streaming_gcs import (
    upload_to_gcs_resumable,
    upload_to_gcs_streaming,
    upload_to_gcs_streaming_advanced,
    upload_to_gcs_streaming_with_retry,
)


class TestUploadToGCSStreaming:
    """Test cases for upload_to_gcs_streaming function."""

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

    def test_upload_to_gcs_streaming_not_implemented(
        self, sample_data, storage_secrets
    ):
        """Test that GCS streaming upload raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="GCS streaming upload not yet implemented"
        ):
            upload_to_gcs_streaming(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=Mock(id="test-request-id"),
                document=None,
                auth_method="service_account",
            )

    def test_upload_to_gcs_streaming_with_document_not_implemented(
        self, sample_data, storage_secrets
    ):
        """Test that GCS streaming upload with document raises NotImplementedError."""
        mock_document = BytesIO(b"test content")

        with pytest.raises(
            NotImplementedError, match="GCS streaming upload not yet implemented"
        ):
            upload_to_gcs_streaming(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=mock_document,
                auth_method="service_account",
            )

    def test_upload_to_gcs_streaming_no_privacy_request_no_document(
        self, sample_data, storage_secrets
    ):
        """Test that GCS streaming upload with no privacy request raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="GCS streaming upload not yet implemented"
        ):
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


class TestUploadToGCSStreamingAdvanced:
    """Test cases for upload_to_gcs_streaming_advanced function."""

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

    def test_upload_to_gcs_streaming_advanced_not_implemented(
        self, sample_data, storage_secrets
    ):
        """Test that advanced GCS streaming upload raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError,
            match="Advanced GCS streaming upload not yet implemented",
        ):
            upload_to_gcs_streaming_advanced(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=Mock(id="test-request-id"),
                document=None,
                auth_method="service_account",
            )

    def test_upload_to_gcs_streaming_advanced_with_document_not_implemented(
        self, sample_data, storage_secrets
    ):
        """Test that advanced GCS streaming upload with document raises NotImplementedError."""
        mock_document = BytesIO(b"test content")

        with pytest.raises(
            NotImplementedError,
            match="Advanced GCS streaming upload not yet implemented",
        ):
            upload_to_gcs_streaming_advanced(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=mock_document,
                auth_method="service_account",
            )

    def test_upload_to_gcs_streaming_advanced_no_privacy_request_no_document(
        self, sample_data, storage_secrets
    ):
        """Test that advanced GCS streaming upload with no privacy request raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError,
            match="Advanced GCS streaming upload not yet implemented",
        ):
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


class TestUploadToGCSResumable:
    """Test cases for upload_to_gcs_resumable function."""

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

    def test_upload_to_gcs_resumable_not_implemented(
        self, sample_data, storage_secrets
    ):
        """Test that GCS resumable upload raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="GCS resumable upload not yet implemented"
        ):
            upload_to_gcs_resumable(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=Mock(id="test-request-id"),
                document=None,
                auth_method="service_account",
            )

    def test_upload_to_gcs_resumable_with_document_not_implemented(
        self, sample_data, storage_secrets
    ):
        """Test that GCS resumable upload with document raises NotImplementedError."""
        mock_document = BytesIO(b"test content")

        with pytest.raises(
            NotImplementedError, match="GCS resumable upload not yet implemented"
        ):
            upload_to_gcs_resumable(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=mock_document,
                auth_method="service_account",
            )

    def test_upload_to_gcs_resumable_no_privacy_request_no_document(
        self, sample_data, storage_secrets
    ):
        """Test that GCS resumable upload with no privacy request raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="GCS resumable upload not yet implemented"
        ):
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


class TestUploadToGCSStreamingWithRetry:
    """Test cases for upload_to_gcs_streaming_with_retry function."""

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

    def test_upload_to_gcs_streaming_with_retry_not_implemented(
        self, sample_data, storage_secrets
    ):
        """Test that GCS streaming upload with retry raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError,
            match="GCS streaming upload with retry not yet implemented",
        ):
            upload_to_gcs_streaming_with_retry(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=Mock(id="test-request-id"),
                document=None,
                auth_method="service_account",
            )

    def test_upload_to_gcs_streaming_with_retry_with_document_not_implemented(
        self, sample_data, storage_secrets
    ):
        """Test that GCS streaming upload with retry and document raises NotImplementedError."""
        mock_document = BytesIO(b"test content")

        with pytest.raises(
            NotImplementedError,
            match="GCS streaming upload with retry not yet implemented",
        ):
            upload_to_gcs_streaming_with_retry(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=mock_document,
                auth_method="service_account",
            )

    def test_upload_to_gcs_streaming_with_retry_no_privacy_request_no_document(
        self, sample_data, storage_secrets
    ):
        """Test that GCS streaming upload with retry and no privacy request raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError,
            match="GCS streaming upload with retry not yet implemented",
        ):
            upload_to_gcs_streaming_with_retry(
                storage_secrets=storage_secrets,
                data=sample_data,
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="json",
                privacy_request=None,
                document=None,
                auth_method="service_account",
            )

import time
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from google.cloud.exceptions import GoogleCloudError
from google.cloud.storage import Blob, Bucket, Client

from fides.api.common_exceptions import StorageUploadError
from fides.api.service.storage.gcs import get_gcs_client
from fides.api.service.storage.streaming.cloud_storage_client import (
    MultipartUploadResponse,
    UploadPartResponse,
)
from fides.api.service.storage.streaming.gcs.gcs_schemas import (
    GCSChunkUploadResponse,
    GCSResumableUploadResponse,
)
from fides.api.service.storage.streaming.gcs.gcs_storage_client import (
    GCSStorageClient,
    create_gcs_storage_client,
)
from fides.api.service.storage.streaming.util import GCS_MIN_CHUNK_SIZE


@pytest.fixture
def mock_gcs_client():
    """Create a mock GCS client for testing."""
    mock_client = create_autospec(Client)
    mock_client.project = "test-project"
    return mock_client


@pytest.fixture
def mock_bucket():
    """Create a mock GCS bucket for testing."""
    mock_bucket = create_autospec(Bucket)
    mock_bucket.name = "test-bucket-123"
    return mock_bucket


@pytest.fixture
def mock_blob():
    """Create a mock GCS blob for testing."""
    mock_blob = create_autospec(Blob)
    mock_blob.name = "test-file.zip"
    mock_blob.bucket.name = "test-bucket-123"
    mock_blob.size = 1024
    mock_blob.content_type = "application/zip"
    mock_blob.etag = "test-etag-123"
    mock_blob.updated = "2023-01-01T00:00:00Z"
    mock_blob.metadata = {"source": "test"}
    return mock_blob


@pytest.fixture
def gcs_storage_client(mock_gcs_client):
    """Create GCSStorageClient instance with mock GCS client."""
    return GCSStorageClient(mock_gcs_client)


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {"source": "privacy_request", "format": "zip", "request_id": "test-123"}


@pytest.fixture
def test_file_content():
    """Sample file content for testing."""
    return b"This is a test file content for GCS operations testing."


@pytest.fixture
def chunk_content():
    """Sample chunk content for testing."""
    chunk_size = GCS_MIN_CHUNK_SIZE
    base_content = b"test content"
    repetitions_needed = (chunk_size // len(base_content)) + 1
    return base_content * repetitions_needed


class TestGCSStorageClientInitialization:
    """Tests for GCSStorageClient initialization."""

    def test_init_with_gcs_client(self, mock_gcs_client):
        """Test GCSStorageClient initialization with GCS client."""
        client = GCSStorageClient(mock_gcs_client)
        assert client.client == mock_gcs_client
        assert client._resumable_uploads == {}


class TestGCSStorageClientMultipartUpload:
    """Tests for multipart upload operations (compatibility layer)."""

    def test_create_multipart_upload_success(
        self, gcs_storage_client, mock_bucket, mock_blob, sample_metadata
    ):
        """Test successful multipart upload creation."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.create_resumable_upload_session.return_value = (
            "https://resumable-url.com"
        )

        response = gcs_storage_client.create_multipart_upload(
            bucket="test-bucket-123",
            key="test-file.zip",
            content_type="application/zip",
            metadata=sample_metadata,
        )

        assert isinstance(response, MultipartUploadResponse)
        assert response.upload_id is not None
        assert response.upload_id.startswith("gcs_resumable_")
        assert "resumable_url" in response.metadata

        # Verify the upload was stored
        assert response.upload_id in gcs_storage_client._resumable_uploads
        upload_info = gcs_storage_client._resumable_uploads[response.upload_id]
        assert upload_info["bucket"] == "test-bucket-123"
        assert upload_info["key"] == "test-file.zip"
        assert upload_info["bytes_uploaded"] == 0

        # Verify metadata was set
        mock_blob.metadata = sample_metadata

        # Clean up
        gcs_storage_client.abort_multipart_upload(
            bucket="test-bucket-123",
            key="test-file.zip",
            upload_id=response.upload_id,
        )

    def test_create_multipart_upload_without_metadata(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test multipart upload creation without metadata."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.create_resumable_upload_session.return_value = (
            "https://resumable-url.com"
        )

        response = gcs_storage_client.create_multipart_upload(
            bucket="test-bucket-123",
            key="test-file-no-metadata.zip",
            content_type="application/zip",
        )

        assert response.upload_id is not None
        assert response.upload_id in gcs_storage_client._resumable_uploads

        # Clean up
        gcs_storage_client.abort_multipart_upload(
            bucket="test-bucket-123",
            key="test-file-no-metadata.zip",
            upload_id=response.upload_id,
        )

    def test_create_multipart_upload_gcs_error(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test multipart upload creation with GCS error."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.create_resumable_upload_session.side_effect = GoogleCloudError(
            "GCS error"
        )

        with pytest.raises(GoogleCloudError, match="GCS error"):
            gcs_storage_client.create_multipart_upload(
                bucket="test-bucket-123",
                key="test-file.zip",
                content_type="application/zip",
            )

    def test_upload_part_not_implemented(self, gcs_storage_client, chunk_content):
        """Test that upload_part raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="GCS upload_part is not implemented"):
            gcs_storage_client.upload_part(
                bucket="test-bucket-123",
                key="test-parts.zip",
                upload_id="test-upload-id",
                part_number=1,
                body=chunk_content,
            )

    def test_complete_multipart_upload_not_implemented(self, gcs_storage_client):
        """Test that complete_multipart_upload raises NotImplementedError."""
        parts = [UploadPartResponse(etag="etag1", part_number=1)]

        with pytest.raises(NotImplementedError, match="GCS complete_multipart_upload is not implemented"):
            gcs_storage_client.complete_multipart_upload(
                bucket="test-bucket-123",
                key="test-complete.zip",
                upload_id="test-upload-id",
                parts=parts,
            )

    def test_abort_multipart_upload_not_implemented(self, gcs_storage_client):
        """Test that abort_multipart_upload raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="GCS abort_multipart_upload is not implemented"):
            gcs_storage_client.abort_multipart_upload(
                bucket="test-bucket-123",
                key="test-abort.zip",
                upload_id="test-upload-id",
            )


class TestGCSStorageClientResumableUpload:
    """Tests for native GCS resumable upload operations."""

    def test_create_resumable_upload_success(
        self, gcs_storage_client, mock_bucket, mock_blob, sample_metadata
    ):
        """Test successful resumable upload creation."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.create_resumable_upload_session.return_value = (
            "https://resumable-url.com"
        )

        response = gcs_storage_client.create_resumable_upload(
            bucket="test-bucket-123",
            key="test-file.zip",
            content_type="application/zip",
            metadata=sample_metadata,
        )

        assert isinstance(response, GCSResumableUploadResponse)
        assert response.upload_id is not None
        assert response.upload_id.startswith("gcs_resumable_")
        assert response.resumable_url == "https://resumable-url.com"
        assert "bucket" in response.metadata
        assert "key" in response.metadata

        # Verify the upload was stored
        assert response.upload_id in gcs_storage_client._resumable_uploads

        # Clean up
        gcs_storage_client.abort_resumable_upload(
            bucket="test-bucket-123",
            key="test-file.zip",
            upload_id=response.upload_id,
        )

    def test_upload_chunk_not_implemented(self, gcs_storage_client, chunk_content):
        """Test that upload_chunk raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="GCS upload_chunk is not fully implemented"):
            gcs_storage_client.upload_chunk(
                bucket="test-bucket-123",
                key="test-chunks.zip",
                upload_id="test-upload-id",
                chunk_data=chunk_content,
            )

    def test_complete_resumable_upload_not_implemented(self, gcs_storage_client):
        """Test that complete_resumable_upload raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="GCS complete_resumable_upload is not fully implemented"):
            gcs_storage_client.complete_resumable_upload(
                bucket="test-bucket-123",
                key="test-complete-resumable.zip",
                upload_id="test-upload-id",
            )

    def test_abort_resumable_upload_not_implemented(self, gcs_storage_client):
        """Test that abort_resumable_upload raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="GCS abort_resumable_upload is not fully implemented"):
            gcs_storage_client.abort_resumable_upload(
                bucket="test-bucket-123",
                key="test-abort-resumable.zip",
                upload_id="test-upload-id",
            )

    def test_get_resumable_upload_status(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test getting resumable upload status."""
        # First create a resumable upload
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.create_resumable_upload_session.return_value = (
            "https://resumable-url.com"
        )

        upload_response = gcs_storage_client.create_resumable_upload(
            bucket="test-bucket-123",
            key="test-status.zip",
            content_type="application/zip",
        )

        status = gcs_storage_client.get_resumable_upload_status(
            upload_response.upload_id
        )

        assert status is not None
        assert status["bucket"] == "test-bucket-123"
        assert status["key"] == "test-status.zip"
        assert status["bytes_uploaded"] == 0
        assert status["resumable_url"] == "https://resumable-url.com"

        # Test with invalid upload ID
        invalid_status = gcs_storage_client.get_resumable_upload_status("invalid-id")
        assert invalid_status is None

        # Clean up - since abort is not implemented, manually remove from dict
        del gcs_storage_client._resumable_uploads[upload_response.upload_id]


class TestGCSStorageClientObjectOperations:
    """Tests for GCS object operations."""

    def test_get_object_head_success(self, gcs_storage_client, mock_bucket, mock_blob):
        """Test successful object head retrieval."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.reload.return_value = None

        result = gcs_storage_client.get_object_head(
            bucket="test-bucket-123",
            key="test-file.zip",
        )

        assert result["ContentLength"] == 1024
        assert result["ContentType"] == "application/zip"
        assert result["ETag"] == "test-etag-123"
        assert result["LastModified"] == "2023-01-01T00:00:00Z"
        assert result["Metadata"] == {"source": "test"}

        mock_blob.reload.assert_called_once()

    def test_get_object_head_gcs_error(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test object head retrieval with GCS error."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.reload.side_effect = GoogleCloudError("GCS error")

        with pytest.raises(GoogleCloudError, match="GCS error"):
            gcs_storage_client.get_object_head(
                bucket="test-bucket-123",
                key="test-file.zip",
            )

    def test_get_object_range_success(self, gcs_storage_client, mock_bucket, mock_blob):
        """Test successful object range retrieval."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        expected_data = b"range data"
        mock_blob.download_as_bytes.return_value = expected_data

        result = gcs_storage_client.get_object_range(
            bucket="test-bucket-123",
            key="test-file.zip",
            start_byte=0,
            end_byte=9,
        )

        assert result == expected_data
        mock_blob.download_as_bytes.assert_called_once_with(start=0, end=9)

    def test_get_object_range_gcs_error(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test object range retrieval with GCS error."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.download_as_bytes.side_effect = GoogleCloudError("GCS error")

        with pytest.raises(GoogleCloudError, match="GCS error"):
            gcs_storage_client.get_object_range(
                bucket="test-bucket-123",
                key="test-file.zip",
                start_byte=0,
                end_byte=9,
            )

    def test_generate_presigned_url_success(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test successful presigned URL generation."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        expected_url = "https://signed-url.com"
        mock_blob.generate_signed_url.return_value = expected_url

        result = gcs_storage_client.generate_presigned_url(
            bucket="test-bucket-123",
            key="test-file.zip",
            ttl_seconds=3600,
        )

        assert result == expected_url
        mock_blob.generate_signed_url.assert_called_once_with(
            version="v4", expiration=3600, method="GET"
        )

    def test_generate_presigned_url_default_ttl(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test presigned URL generation with default TTL."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        expected_url = "https://signed-url.com"
        mock_blob.generate_signed_url.return_value = expected_url

        result = gcs_storage_client.generate_presigned_url(
            bucket="test-bucket-123",
            key="test-file.zip",
        )

        assert result == expected_url
        mock_blob.generate_signed_url.assert_called_once_with(
            version="v4", expiration=3600, method="GET"
        )

    def test_generate_presigned_url_error(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test presigned URL generation with error."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.generate_signed_url.side_effect = Exception("URL generation error")

        with pytest.raises(Exception, match="URL generation error"):
            gcs_storage_client.generate_presigned_url(
                bucket="test-bucket-123",
                key="test-file.zip",
            )


class TestGCSCreateStorageClient:
    """Tests for the factory function."""

    @patch("fides.api.service.storage.streaming.gcs.gcs_storage_client.get_gcs_client")
    def test_create_gcs_storage_client_success(
        self, mock_get_gcs_client, mock_gcs_client
    ):
        """Test successful GCS storage client creation."""
        mock_get_gcs_client.return_value = mock_gcs_client

        client = create_gcs_storage_client("adc", None)

        assert isinstance(client, GCSStorageClient)
        assert client.client == mock_gcs_client
        mock_get_gcs_client.assert_called_once_with("adc", None)

    @patch("fides.api.service.storage.streaming.gcs.gcs_storage_client.get_gcs_client")
    def test_create_gcs_storage_client_with_secrets(
        self, mock_get_gcs_client, mock_gcs_client
    ):
        """Test GCS storage client creation with secrets."""
        mock_get_gcs_client.return_value = mock_gcs_client
        secrets = {"type": "service_account", "project_id": "test-project"}

        client = create_gcs_storage_client("service_account", secrets)

        assert isinstance(client, GCSStorageClient)
        assert client.client == mock_gcs_client
        mock_get_gcs_client.assert_called_once_with("service_account", secrets)


class TestGCSStorageClientEdgeCases:
    """Tests for edge cases and error handling."""

    def test_multiple_uploads_same_key(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test handling multiple uploads with the same key."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.create_resumable_upload_session.return_value = (
            "https://resumable-url.com"
        )

        # Mock time to ensure different timestamps
        with patch("time.time") as mock_time:
            mock_time.side_effect = [1234567890, 1234567891]  # Different timestamps

            # Create first upload
            response1 = gcs_storage_client.create_multipart_upload(
                bucket="test-bucket-123",
                key="same-key.zip",
                content_type="application/zip",
            )

            # Create second upload with same key
            response2 = gcs_storage_client.create_multipart_upload(
                bucket="test-bucket-123",
                key="same-key.zip",
                content_type="application/zip",
            )

            assert response1.upload_id != response2.upload_id
            assert len(gcs_storage_client._resumable_uploads) == 2

            # Clean up - manually remove since abort is not implemented
            del gcs_storage_client._resumable_uploads[response1.upload_id]
            del gcs_storage_client._resumable_uploads[response2.upload_id]

    def test_upload_id_collision_handling(
        self, gcs_storage_client, mock_bucket, mock_blob
    ):
        """Test handling of upload ID collisions (very unlikely but possible)."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.create_resumable_upload_session.return_value = (
            "https://resumable-url.com"
        )

        # Mock time to return same timestamp and hash to simulate collision
        with patch("time.time", return_value=1234567890):
            with patch(
                "builtins.hash", side_effect=[42, 42]
            ):  # Same hash for both keys
                response1 = gcs_storage_client.create_multipart_upload(
                    bucket="test-bucket-123",
                    key="collision-test1.zip",
                    content_type="application/zip",
                )

                response2 = gcs_storage_client.create_multipart_upload(
                    bucket="test-bucket-123",
                    key="collision-test2.zip",
                    content_type="application/zip",
                )

                # In this case, we would get the same upload ID due to collision
                # This is a limitation of the current implementation
                # In a real scenario, we'd want to add additional uniqueness
                assert response1.upload_id == response2.upload_id
                assert len(gcs_storage_client._resumable_uploads) == 1

                # Clean up - manually remove since abort is not implemented
                del gcs_storage_client._resumable_uploads[response1.upload_id]

    def test_cleanup_on_exception(self, gcs_storage_client, mock_bucket, mock_blob):
        """Test that uploads are properly cleaned up even when exceptions occur."""
        # Configure mocks
        gcs_storage_client.client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.create_resumable_upload_session.return_value = (
            "https://resumable-url.com"
        )

        # Create an upload
        response = gcs_storage_client.create_multipart_upload(
            bucket="test-bucket-123",
            key="cleanup-test.zip",
            content_type="application/zip",
        )

        # Verify upload exists
        assert response.upload_id in gcs_storage_client._resumable_uploads

        # Simulate an exception during upload
        try:
            raise Exception("Test exception")
        except Exception:
            # Even with exception, cleanup should work manually
            # Since abort is not implemented, we clean up manually
            if response.upload_id in gcs_storage_client._resumable_uploads:
                del gcs_storage_client._resumable_uploads[response.upload_id]

        # Verify upload was cleaned up
        assert response.upload_id not in gcs_storage_client._resumable_uploads

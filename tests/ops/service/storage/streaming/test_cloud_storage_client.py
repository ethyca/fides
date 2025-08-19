"""Tests for the CloudStorageClient abstract base class and ProgressCallback protocol."""

from typing import Any, Dict, List, get_type_hints
from unittest.mock import create_autospec, patch

import pytest

from fides.api.service.storage.streaming.cloud_storage_client import (
    CloudStorageClient,
    ProgressCallback,
)
from fides.api.service.storage.streaming.schemas import (
    MultipartUploadResponse,
    ProcessingMetrics,
    UploadPartResponse,
)


class TestCloudStorageClient:
    """Test cases for the CloudStorageClient abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that CloudStorageClient cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CloudStorageClient()

    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = CloudStorageClient.__abstractmethods__
        expected_methods = {
            "create_multipart_upload",
            "upload_part",
            "complete_multipart_upload",
            "abort_multipart_upload",
            "get_object_head",
            "get_object_range",
            "generate_presigned_url",
        }
        assert abstract_methods == expected_methods

    def test_mock_implementation_works(self, mock_storage_client):
        """Test that our mock implementation can be instantiated."""
        assert isinstance(mock_storage_client, CloudStorageClient)

    def test_create_multipart_upload(self, mock_storage_client):
        """Test create_multipart_upload method."""
        response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
            metadata={"test": "value"},
        )

        assert isinstance(response, MultipartUploadResponse)
        assert response.upload_id.startswith("generic_upload_")
        assert response.metadata["bucket"] == "test-bucket"
        assert response.metadata["key"] == "test-key"
        assert response.metadata["content_type"] == "application/zip"

    def test_upload_part(self, mock_storage_client):
        """Test upload_part method."""
        # First create an upload
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        # Then upload a part
        part_response = mock_storage_client.upload_part(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=b"test data",
            metadata={"part": "metadata"},
        )

        assert isinstance(part_response, UploadPartResponse)
        assert part_response.etag.startswith("generic_etag_")
        assert part_response.part_number == 1
        assert part_response.metadata["part"] == "metadata"

    def test_upload_part_invalid_upload_id(self, mock_storage_client):
        """Test upload_part with invalid upload ID."""
        # Configure the mock to raise an error for invalid upload ID
        mock_storage_client.upload_part.side_effect = ValueError(
            "Upload invalid_id not found"
        )

        with pytest.raises(ValueError, match="Upload invalid_id not found"):
            mock_storage_client.upload_part(
                bucket="test-bucket",
                key="test-key",
                upload_id="invalid_id",
                part_number=1,
                body=b"test data",
            )

    def test_upload_part_bucket_key_mismatch(self, mock_storage_client):
        """Test upload_part with bucket/key mismatch."""
        # Configure the mock to raise an error for bucket/key mismatch
        mock_storage_client.upload_part.side_effect = ValueError(
            "Bucket or key mismatch"
        )

        with pytest.raises(ValueError, match="Bucket or key mismatch"):
            mock_storage_client.upload_part(
                bucket="bucket2",
                key="key2",
                upload_id="some_upload_id",
                part_number=1,
                body=b"test data",
            )

    def test_complete_multipart_upload(self, mock_storage_client):
        """Test complete_multipart_upload method."""
        # Create upload and upload parts
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        part1 = mock_storage_client.upload_part(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=b"part1",
        )

        part2 = mock_storage_client.upload_part(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            part_number=2,
            body=b"part2",
        )

        # Complete the upload
        mock_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            parts=[part1, part2],
            metadata={"completed": "true"},
        )

        # Verify the method was called
        mock_storage_client.complete_multipart_upload.assert_called_once()

    def test_complete_multipart_upload_invalid_upload_id(self, mock_storage_client):
        """Test complete_multipart_upload with invalid upload ID."""
        # Configure the mock to raise an error for invalid upload ID
        mock_storage_client.complete_multipart_upload.side_effect = ValueError(
            "Upload invalid_id not found"
        )

        with pytest.raises(ValueError, match="Upload invalid_id not found"):
            mock_storage_client.complete_multipart_upload(
                bucket="test-bucket",
                key="test-key",
                upload_id="invalid_id",
                parts=[],
            )

    def test_abort_multipart_upload(self, mock_storage_client):
        """Test abort_multipart_upload method."""
        # Create an upload
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        # Abort the upload
        mock_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
        )

        # Verify the method was called
        mock_storage_client.abort_multipart_upload.assert_called_once()

    def test_abort_multipart_upload_invalid_upload_id(self, mock_storage_client):
        """Test abort_multipart_upload with invalid upload ID."""
        # Configure the mock to raise an error for invalid upload ID
        mock_storage_client.abort_multipart_upload.side_effect = ValueError(
            "Upload invalid_id not found"
        )

        with pytest.raises(ValueError, match="Upload invalid_id not found"):
            mock_storage_client.abort_multipart_upload(
                bucket="test-bucket",
                key="test-key",
                upload_id="invalid_id",
            )

    def test_get_object_head(self, mock_storage_client):
        """Test get_object_head method."""
        # Create and complete an upload to have an object
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        part = mock_storage_client.upload_part(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=b"test data",
        )

        # Complete the upload to create the object
        mock_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            parts=[part],
        )

        # Get object head
        head = mock_storage_client.get_object_head("test-bucket", "test-key")

        assert isinstance(head, dict)
        assert "ContentLength" in head
        assert "ContentType" in head
        assert "ETag" in head
        assert "Metadata" in head

    def test_get_object_head_object_not_found(self, mock_storage_client):
        """Test get_object_head with non-existent object."""
        # Configure the mock to raise an error for non-existent object
        mock_storage_client.get_object_head.side_effect = ValueError(
            "Object test-bucket/test-key not found"
        )

        with pytest.raises(ValueError, match="Object test-bucket/test-key not found"):
            mock_storage_client.get_object_head("test-bucket", "test-key")

    def test_get_object_range(self, mock_storage_client):
        """Test get_object_range method."""
        # Create and complete an upload to have an object
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        part = mock_storage_client.upload_part(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=b"test data",
        )

        # Complete the upload to create the object
        mock_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            parts=[part],
        )

        # Get object range
        data = mock_storage_client.get_object_range("test-bucket", "test-key", 0, 9)

        assert isinstance(data, bytes)
        assert len(data) == 10  # 0-9 inclusive = 10 bytes

    def test_get_object_range_object_not_found(self, mock_storage_client):
        """Test get_object_range with non-existent object."""
        # Configure the mock to raise an error for non-existent object
        mock_storage_client.get_object_range.side_effect = ValueError(
            "Object test-bucket/test-key not found"
        )

        with pytest.raises(ValueError, match="Object test-bucket/test-key not found"):
            mock_storage_client.get_object_range("test-bucket", "test-key", 0, 9)

    def test_generate_presigned_url(self, mock_storage_client):
        """Test generate_presigned_url method."""
        # Create and complete an upload to have an object
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            content_type="application/zip",
        )

        part = mock_storage_client.upload_part(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=b"test data",
        )

        # Complete the upload to create the object
        mock_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-key",
            upload_id=upload_response.upload_id,
            parts=[part],
        )

        # Generate presigned URL with default TTL
        url = mock_storage_client.generate_presigned_url("test-bucket", "test-key")

        assert isinstance(url, str)
        assert url.startswith("https://mock-storage.example.com/")
        assert "ttl=3600" in url  # Default TTL

        # Generate presigned URL with custom TTL
        url_custom = mock_storage_client.generate_presigned_url(
            "test-bucket", "test-key", 7200
        )

        assert "ttl=7200" in url_custom

    def test_generate_presigned_url_object_not_found(self, mock_storage_client):
        """Test generate_presigned_url with non-existent object."""
        # Configure the mock to raise an error for non-existent object
        mock_storage_client.generate_presigned_url.side_effect = ValueError(
            "Object test-bucket/test-key not found"
        )

        with pytest.raises(ValueError, match="Object test-bucket/test-key not found"):
            mock_storage_client.generate_presigned_url("test-bucket", "test-key")

    def test_multipart_upload_workflow(self, mock_storage_client):
        """Test complete multipart upload workflow."""
        # Step 1: Create multipart upload
        upload_response = mock_storage_client.create_multipart_upload(
            bucket="workflow-bucket",
            key="workflow-key",
            content_type="application/zip",
            metadata={"workflow": "test"},
        )

        assert upload_response.upload_id.startswith("generic_upload_")

        # Step 2: Upload multiple parts
        parts = []
        for i in range(1, 4):  # Upload 3 parts
            part = mock_storage_client.upload_part(
                bucket="workflow-bucket",
                key="workflow-key",
                upload_id=upload_response.upload_id,
                part_number=i,
                body=f"part{i}".encode(),
                metadata={"part_number": str(i)},
            )
            parts.append(part)

        # Verify parts were created
        assert len(parts) == 3
        for i, part in enumerate(parts, 1):
            assert part.part_number == i
            assert part.metadata["part_number"] == str(i)

        # Step 3: Complete the upload
        mock_storage_client.complete_multipart_upload(
            bucket="workflow-bucket",
            key="workflow-key",
            upload_id=upload_response.upload_id,
            parts=parts,
            metadata={"status": "completed"},
        )

        # Verify the method was called
        mock_storage_client.complete_multipart_upload.assert_called_once()

    def test_with_storage_config_fixture(self, mock_storage_client, storage_config):
        """Test using the storage_config fixture for more realistic testing."""
        # Use the storage config bucket name
        bucket = storage_config.details["bucket"]
        key = "test-with-fixture"

        response = mock_storage_client.create_multipart_upload(
            bucket=bucket,
            key=key,
            content_type="application/zip",
            metadata={"storage_config_id": str(storage_config.id)},
        )

        assert response.metadata["bucket"] == bucket
        assert response.metadata["key"] == key
        assert response.metadata["content_type"] == "application/zip"

    def test_with_gcs_storage_config_fixture(
        self, mock_gcs_storage_client, storage_config_default_gcs
    ):
        """Test using the GCS storage config fixture."""
        # Use the GCS storage config bucket name
        bucket = storage_config_default_gcs.details["bucket"]
        key = "test-gcs-fixture"

        response = mock_gcs_storage_client.create_multipart_upload(
            bucket=bucket,
            key=key,
            content_type="application/zip",
            metadata={"storage_type": "gcs"},
        )

        assert response.metadata["bucket"] == bucket
        assert response.metadata["key"] == key
        assert response.metadata["content_type"] == "application/zip"

    def test_with_s3_storage_config_fixture(
        self, mock_s3_storage_client, storage_config
    ):
        """Test using the S3 storage config fixture."""
        # Use the S3 storage config bucket name
        bucket = storage_config.details["bucket"]
        key = "test-s3-fixture"

        response = mock_s3_storage_client.create_multipart_upload(
            bucket=bucket,
            key=key,
            content_type="application/zip",
            metadata={"storage_type": "s3"},
        )

        assert response.metadata["bucket"] == bucket
        assert response.metadata["key"] == key
        assert response.metadata["content_type"] == "application/zip"


class TestProgressCallback:
    """Test cases for the ProgressCallback protocol."""

    def test_progress_callback_protocol(self):
        """Test that ProgressCallback protocol is properly defined."""
        # The protocol should be callable with ProcessingMetrics
        assert hasattr(ProgressCallback, "__call__")

    def test_progress_callback_implementation(self):
        """Test that a function can implement the ProgressCallback protocol."""
        callback_called = False
        callback_metrics = None

        def progress_callback(metrics: ProcessingMetrics) -> None:
            nonlocal callback_called, callback_metrics
            callback_called = True
            callback_metrics = metrics

        # Verify the function can be assigned to the protocol type
        callback: ProgressCallback = progress_callback

        # Test calling the callback
        test_metrics = ProcessingMetrics(
            total_attachments=10,
            processed_attachments=5,
            total_bytes=1000,
            processed_bytes=500,
        )

        callback(test_metrics)

        assert callback_called
        assert callback_metrics == test_metrics

    def test_progress_callback_with_lambda(self):
        """Test that a lambda can implement the ProgressCallback protocol."""
        callback: ProgressCallback = lambda metrics: metrics.total_attachments

        test_metrics = ProcessingMetrics(total_attachments=42)
        result = callback(test_metrics)

        assert result == 42

    def test_progress_callback_with_class_method(self):
        """Test that a class method can implement the ProgressCallback protocol."""

        class ProgressTracker:
            def __init__(self):
                self.last_metrics = None

            def track_progress(self, metrics: ProcessingMetrics) -> None:
                self.last_metrics = metrics

        tracker = ProgressTracker()
        callback: ProgressCallback = tracker.track_progress

        test_metrics = ProcessingMetrics(
            total_attachments=100,
            processed_attachments=50,
        )

        callback(test_metrics)

        assert tracker.last_metrics == test_metrics

    def test_progress_callback_with_autospec_mock(self):
        """Test that an autospec mock can implement the ProgressCallback protocol."""
        mock_callback = create_autospec(ProgressCallback)
        callback: ProgressCallback = mock_callback

        test_metrics = ProcessingMetrics(
            total_attachments=5,
            processed_attachments=3,
        )

        callback(test_metrics)

        mock_callback.assert_called_once_with(test_metrics)

    def test_progress_callback_type_hints(self):
        """Test that ProgressCallback has proper type hints."""
        # Get the type hints for the protocol
        hints = get_type_hints(ProgressCallback.__call__)

        # Should have a parameter named 'metrics' of type ProcessingMetrics
        assert "metrics" in hints
        assert hints["metrics"] == ProcessingMetrics

        # Should return None (NoneType in type hints)
        assert hints.get("return") == type(None)

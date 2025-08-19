from unittest.mock import Mock, create_autospec

import pytest

from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.schemas import (
    MultipartUploadResponse,
    UploadPartResponse,
)


@pytest.fixture
def mock_storage_client():
    """Create a comprehensive mock storage client using autospec."""
    client = create_autospec(CloudStorageClient, spec_set=False)

    # Mock the multipart upload response using autospec with spec_set=False to allow attribute setting
    def mock_create_upload(bucket, key, content_type, metadata=None):
        upload_response = create_autospec(MultipartUploadResponse, spec_set=False)
        upload_response.upload_id = f"generic_upload_{bucket}_{key}_789"
        upload_response.metadata = {
            "bucket": bucket,
            "key": key,
            "content_type": content_type,
            **(metadata or {}),
        }
        return upload_response

    client.create_multipart_upload.side_effect = mock_create_upload

    # Create a list to store mock parts for tracking
    mock_parts = []

    # Mock upload part responses with proper call tracking
    def mock_upload_part(*args, **kwargs):
        part = create_autospec(UploadPartResponse, spec_set=False)
        call_count = len(mock_parts) + 1
        part.etag = f"generic_etag_{call_count}"
        part.part_number = kwargs.get("part_number", call_count)
        part.metadata = kwargs.get("metadata", {})
        mock_parts.append(part)
        return part

    # Use side_effect with a function that creates fresh mocks
    client.upload_part.side_effect = mock_upload_part

    # Mock object storage for completed uploads
    mock_objects = {}

    def mock_complete_upload(bucket, key, upload_id, parts, metadata=None):
        object_key = f"{bucket}/{key}"
        mock_objects[object_key] = {
            "parts": parts,
            "metadata": metadata or {},
            "size": sum(len(part.etag) for part in parts) if parts else 0,
        }
        return None

    client.complete_multipart_upload.side_effect = mock_complete_upload
    client.abort_multipart_upload.return_value = None

    # Mock object retrieval methods
    def mock_get_object_head(bucket, key):
        object_key = f"{bucket}/{key}"
        if object_key in mock_objects:
            obj = mock_objects[object_key]
            return {
                "ContentLength": obj["size"],
                "ContentType": "application/octet-stream",
                "ETag": f"mock_etag_{object_key}",
                "Metadata": obj["metadata"],
            }
        raise ValueError(f"Object {object_key} not found")

    client.get_object_head.side_effect = mock_get_object_head

    def mock_get_object_range(bucket, key, start_byte, end_byte):
        object_key = f"{bucket}/{key}"
        if object_key in mock_objects:
            range_size = end_byte - start_byte + 1
            return b"x" * max(0, range_size)
        raise ValueError(f"Object {object_key} not found")

    client.get_object_range.side_effect = mock_get_object_range

    def mock_generate_presigned_url(bucket, key, ttl_seconds=None):
        object_key = f"{bucket}/{key}"
        if object_key in mock_objects:
            ttl = ttl_seconds or 3600
            return f"https://mock-storage.example.com/{bucket}/{key}?ttl={ttl}"
        raise ValueError(f"Object {object_key} not found")

    client.generate_presigned_url.side_effect = mock_generate_presigned_url

    return client


@pytest.fixture
def mock_gcs_storage_client():
    """Create a mock GCS storage client using Mock."""
    client = Mock(spec=CloudStorageClient)

    # Mock the multipart upload response
    def mock_create_upload(bucket, key, content_type, metadata=None):
        upload_response = Mock()
        upload_response.upload_id = f"gcs_upload_{bucket}_{key}_123"
        upload_response.metadata = {
            "bucket": bucket,
            "key": key,
            "content_type": content_type,
            **(metadata or {}),
        }
        return upload_response

    client.create_multipart_upload.side_effect = mock_create_upload

    # Mock upload part responses
    def mock_upload_part(bucket, key, upload_id, part_number, body, metadata=None):
        part = Mock()
        part.etag = f"gcs_etag_{part_number}"
        part.part_number = part_number
        part.metadata = metadata or {}
        return part

    client.upload_part.side_effect = mock_upload_part

    # Mock the complete and abort methods
    client.complete_multipart_upload.return_value = None
    client.abort_multipart_upload.return_value = None

    return client


@pytest.fixture
def mock_s3_storage_client():
    """Create a mock S3 storage client using Mock."""
    client = Mock(spec=CloudStorageClient)

    # Mock the multipart upload response
    def mock_create_upload(bucket, key, content_type, metadata=None):
        upload_response = Mock()
        upload_response.upload_id = f"s3_upload_{bucket}_{key}_456"
        upload_response.metadata = {
            "bucket": bucket,
            "key": key,
            "content_type": content_type,
            **(metadata or {}),
        }
        return upload_response

    client.create_multipart_upload.side_effect = mock_create_upload

    # Mock upload part responses
    def mock_upload_part(bucket, key, upload_id, part_number, body, metadata=None):
        part = Mock()
        part.etag = f"s3_etag_{part_number}"
        part.part_number = part_number
        part.metadata = metadata or {}
        return part

    client.upload_part.side_effect = mock_upload_part

    # Mock the complete and abort methods
    client.complete_multipart_upload.return_value = None
    client.abort_multipart_upload.return_value = None

    return client

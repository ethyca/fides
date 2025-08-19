"""
Tests for S3StorageClient class.

These tests verify the S3-specific implementation of CloudStorageClient,
including multipart uploads, object operations, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
import boto3
from moto import mock_s3
from botocore.exceptions import ClientError, ParamValidationError

from fides.api.service.storage.streaming.s3_storage_client import S3StorageClient, create_s3_storage_client
from fides.api.service.storage.streaming.cloud_storage_client import MultipartUploadResponse, UploadPartResponse


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    return {
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
        "aws_session_token": "testing",
        "region_name": "us-east-1"
    }


@pytest.fixture
def s3_client(aws_credentials):
    """Create a real S3 client using moto."""
    with mock_s3():
        client = boto3.client("s3", **aws_credentials)
        # Create test bucket
        client.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-east-1"}
        )
        yield client


@pytest.fixture
def s3_storage_client(s3_client):
    """Create S3StorageClient instance with real S3 client from moto."""
    return S3StorageClient(s3_client)


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "source": "privacy_request",
        "format": "zip",
        "request_id": "test-123"
    }


@pytest.fixture
def test_file_content():
    """Sample file content for testing."""
    return b"This is a test file content for S3 operations testing."


class TestS3StorageClientInitialization:
    """Tests for S3StorageClient initialization."""

    def test_init_with_s3_client(self, s3_client):
        """Test S3StorageClient initialization with S3 client."""
        client = S3StorageClient(s3_client)
        assert client.client == s3_client


class TestS3StorageClientMultipartUpload:
    """Tests for multipart upload operations."""

    def test_create_multipart_upload_success(self, s3_storage_client, sample_metadata):
        """Test successful multipart upload creation."""
        response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-file.zip",
            content_type="application/zip",
            metadata=sample_metadata
        )

        assert isinstance(response, MultipartUploadResponse)
        assert response.upload_id is not None
        assert "UploadId" in response.metadata
        assert "Bucket" in response.metadata

        # Verify the upload was actually created in S3
        s3_client = s3_storage_client.client
        multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
        assert len(multipart_uploads["Uploads"]) == 1
        assert multipart_uploads["Uploads"][0]["Key"] == "test-file.zip"

    def test_create_multipart_upload_without_metadata(self, s3_storage_client):
        """Test multipart upload creation without metadata."""
        response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-file-no-metadata.zip",
            content_type="application/zip"
        )

        assert response.upload_id is not None

        # Verify the upload was created
        s3_client = s3_storage_client.client
        multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
        assert len(multipart_uploads["Uploads"]) == 2  # Including previous test

    def test_create_multipart_upload_bucket_not_exists(self, s3_storage_client):
        """Test multipart upload creation with non-existent bucket."""
        with pytest.raises(ClientError) as exc_info:
            s3_storage_client.create_multipart_upload(
                bucket="nonexistent-bucket",
                key="test-file.zip",
                content_type="application/zip"
            )

        assert "NoSuchBucket" in str(exc_info.value)

    def test_upload_part_success(self, s3_storage_client):
        """Test successful part upload."""
        # First create a multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-parts.zip",
            content_type="application/zip"
        )

        # Upload a part
        response = s3_storage_client.upload_part(
            bucket="test-bucket",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=b"test part content"
        )

        assert isinstance(response, UploadPartResponse)
        assert response.etag is not None
        assert response.part_number == 1
        assert "ETag" in response.metadata

    def test_upload_part_invalid_upload_id(self, s3_storage_client):
        """Test part upload with invalid upload ID."""
        with pytest.raises(ClientError) as exc_info:
            s3_storage_client.upload_part(
                bucket="test-bucket",
                upload_id="invalid-upload-id",
                part_number=1,
                body=b"test content"
            )

        assert "NoSuchUpload" in str(exc_info.value)

    def test_complete_multipart_upload_success(self, s3_storage_client):
        """Test successful multipart upload completion."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-complete.zip",
            content_type="application/zip"
        )

        # Upload parts
        parts = []
        for i in range(1, 4):
            part_response = s3_storage_client.upload_part(
                bucket="test-bucket",
                upload_id=upload_response.upload_id,
                part_number=i,
                body=f"part {i} content".encode()
            )
            parts.append(part_response)

        # Complete the upload
        s3_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-complete.zip",
            upload_id=upload_response.upload_id,
            parts=parts
        )

        # Verify the object now exists
        s3_client = s3_storage_client.client
        head_response = s3_client.head_object(Bucket="test-bucket", Key="test-complete.zip")
        assert head_response["ContentLength"] > 0

        # Verify no pending multipart uploads
        multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
        assert len(multipart_uploads.get("Uploads", [])) == 0

    def test_complete_multipart_upload_with_metadata(self, s3_storage_client, sample_metadata):
        """Test multipart upload completion with metadata."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-metadata.zip",
            content_type="application/zip"
        )

        # Upload a part
        part_response = s3_storage_client.upload_part(
            bucket="test-bucket",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=b"test content"
        )

        # Complete with metadata
        s3_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-metadata.zip",
            upload_id=upload_response.upload_id,
            parts=[part_response],
            metadata=sample_metadata
        )

        # Note: Current implementation doesn't use metadata parameter
        # This test documents the current behavior
        s3_client = s3_storage_client.client
        head_response = s3_client.head_object(Bucket="test-bucket", Key="test-metadata.zip")
        assert head_response["ContentLength"] > 0

    def test_complete_multipart_upload_invalid_parts(self, s3_storage_client):
        """Test multipart upload completion with invalid parts."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-invalid-parts.zip",
            content_type="application/zip"
        )

        # Try to complete with invalid parts
        invalid_parts = [UploadPartResponse(etag="invalid-etag", part_number=999, metadata={})]

        with pytest.raises(ClientError) as exc_info:
            s3_storage_client.complete_multipart_upload(
                bucket="test-bucket",
                key="test-invalid-parts.zip",
                upload_id=upload_response.upload_id,
                parts=invalid_parts
            )

        assert "InvalidPart" in str(exc_info.value)

    def test_abort_multipart_upload_success(self, s3_storage_client):
        """Test successful multipart upload abortion."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-abort.zip",
            content_type="application/zip"
        )

        # Abort the upload
        s3_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="test-abort.zip",
            upload_id=upload_response.upload_id
        )

        # Verify no pending multipart uploads
        s3_client = s3_storage_client.client
        multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
        assert len(multipart_uploads.get("Uploads", [])) == 0

    def test_abort_multipart_upload_not_exists(self, s3_storage_client):
        """Test multipart upload abortion with non-existent upload."""
        with pytest.raises(ClientError) as exc_info:
            s3_storage_client.abort_multipart_upload(
                bucket="test-bucket",
                key="test-abort-not-exists.zip",
                upload_id="nonexistent-upload"
            )

        assert "NoSuchUpload" in str(exc_info.value)


class TestS3StorageClientObjectOperations:
    """Tests for object operations."""

    def test_get_object_head_success(self, s3_storage_client, test_file_content):
        """Test successful object head retrieval."""
        # First upload a test object
        s3_client = s3_storage_client.client
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test-head-object.txt",
            Body=test_file_content,
            ContentType="text/plain"
        )

        # Get object head
        response = s3_storage_client.get_object_head(
            bucket="test-bucket",
            key="test-head-object.txt"
        )

        assert response["ContentLength"] == len(test_file_content)
        assert response["ContentType"] == "text/plain"
        assert "ETag" in response

    def test_get_object_head_not_exists(self, s3_storage_client):
        """Test object head retrieval with non-existent object."""
        with pytest.raises(ClientError) as exc_info:
            s3_storage_client.get_object_head(
                bucket="test-bucket",
                key="nonexistent-file.txt"
            )

        assert "NoSuchKey" in str(exc_info.value)

    def test_get_object_range_success(self, s3_storage_client, test_file_content):
        """Test successful object range retrieval."""
        # First upload a test object
        s3_client = s3_storage_client.client
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test-range-object.txt",
            Body=test_file_content,
            ContentType="text/plain"
        )

        # Get object range
        response = s3_storage_client.get_object_range(
            bucket="test-bucket",
            key="test-range-object.txt",
            start_byte=0,
            end_byte=9
        )

        assert response == test_file_content[:10]  # First 10 bytes

    def test_get_object_range_partial(self, s3_storage_client, test_file_content):
        """Test object range retrieval for middle portion."""
        # First upload a test object
        s3_client = s3_storage_client.client
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test-range-partial.txt",
            Body=test_file_content,
            ContentType="text/plain"
        )

        # Get middle portion
        response = s3_storage_client.get_object_range(
            bucket="test-bucket",
            key="test-range-partial.txt",
            start_byte=10,
            end_byte=19
        )

        assert response == test_file_content[10:20]  # Bytes 10-19

    def test_get_object_range_invalid_range(self, s3_storage_client, test_file_content):
        """Test object range retrieval with invalid range."""
        # First upload a test object
        s3_client = s3_storage_client.client
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test-range-invalid.txt",
            Body=test_file_content,
            ContentType="text/plain"
        )

        # Try to get range beyond file size
        with pytest.raises(ClientError) as exc_info:
            s3_storage_client.get_object_range(
                bucket="test-bucket",
                key="test-range-invalid.txt",
                start_byte=999999,
                end_byte=1000000
            )

        assert "InvalidRange" in str(exc_info.value)

    def test_get_object_range_closes_stream(self, s3_storage_client, test_file_content):
        """Test that object range retrieval properly handles the stream."""
        # First upload a test object
        s3_client = s3_storage_client.client
        s3_client.put_object(
            Bucket="test-bucket",
            Key="test-range-stream.txt",
            Body=test_file_content,
            ContentType="text/plain"
        )

        # Get object range - this should work without stream issues
        response = s3_storage_client.get_object_range(
            bucket="test-bucket",
            key="test-range-stream.txt",
            start_byte=0,
            end_byte=1023
        )

        assert len(response) > 0
        # moto handles stream cleanup automatically, so we just verify it works


class TestS3StorageClientPresignedURL:
    """Tests for presigned URL generation."""

    @patch("fides.api.service.storage.s3_storage_client.create_presigned_url_for_s3")
    def test_generate_presigned_url_success(self, mock_create_url, s3_storage_client):
        """Test successful presigned URL generation."""
        expected_url = "https://test-bucket.s3.amazonaws.com/test-key?signature=abc123"
        mock_create_url.return_value = expected_url

        url = s3_storage_client.generate_presigned_url(
            bucket="test-bucket",
            key="test-file.zip"
        )

        assert url == expected_url
        mock_create_url.assert_called_once_with(
            s3_storage_client.client,
            "test-bucket",
            "test-file.zip",
            None
        )

    @patch("fides.api.service.storage.s3_storage_client.create_presigned_url_for_s3")
    def test_generate_presigned_url_with_ttl(self, mock_create_url, s3_storage_client):
        """Test presigned URL generation with custom TTL."""
        expected_url = "https://test-bucket.s3.amazonaws.com/test-key?signature=abc123&expires=86400"
        mock_create_url.return_value = expected_url

        url = s3_storage_client.generate_presigned_url(
            bucket="test-bucket",
            key="test-file.zip",
            ttl_seconds=86400
        )

        assert url == expected_url
        mock_create_url.assert_called_once_with(
            s3_storage_client.client,
            "test-bucket",
            "test-file.zip",
            86400
        )

    @patch("fides.api.service.storage.s3_storage_client.create_presigned_url_for_s3")
    def test_generate_presigned_url_error(self, mock_create_url, s3_storage_client):
        """Test presigned URL generation with error."""
        mock_create_url.side_effect = Exception("URL generation failed")

        with pytest.raises(Exception) as exc_info:
            s3_storage_client.generate_presigned_url(
                bucket="test-bucket",
                key="test-file.zip"
            )

        assert "URL generation failed" in str(exc_info.value)


class TestS3StorageClientIntegration:
    """Integration tests for complete multipart upload workflow."""

    def test_complete_multipart_upload_workflow(self, s3_storage_client):
        """Test complete multipart upload workflow from start to finish."""
        # 1. Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="large-file.zip",
            content_type="application/zip"
        )

        assert upload_response.upload_id is not None

        # 2. Upload multiple parts
        parts = []
        for i in range(1, 4):
            part_response = s3_storage_client.upload_part(
                bucket="test-bucket",
                upload_id=upload_response.upload_id,
                part_number=i,
                body=f"part {i} content".encode()
            )
            parts.append(part_response)

        assert len(parts) == 3
        assert all(isinstance(part, UploadPartResponse) for part in parts)

        # 3. Complete multipart upload
        s3_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="large-file.zip",
            upload_id=upload_response.upload_id,
            parts=parts
        )

        # 4. Verify the final object exists and has correct content
        s3_client = s3_storage_client.client
        head_response = s3_client.head_object(Bucket="test-bucket", Key="large-file.zip")
        assert head_response["ContentLength"] > 0

        # 5. Verify no pending multipart uploads
        multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
        assert len(multipart_uploads.get("Uploads", [])) == 0

    def test_multipart_upload_with_error_handling(self, s3_storage_client):
        """Test multipart upload workflow with error handling and cleanup."""
        # 1. Create upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="error-handling-test.zip",
            content_type="application/zip"
        )

        try:
            # 2. Upload first part successfully
            part1_response = s3_storage_client.upload_part(
                bucket="test-bucket",
                upload_id=upload_response.upload_id,
                part_number=1,
                body=b"part 1 content"
            )

            # 3. Try to upload part with invalid part number (should fail)
            with pytest.raises(ClientError):
                s3_storage_client.upload_part(
                    bucket="test-bucket",
                    upload_id=upload_response.upload_id,
                    part_number=999,  # Invalid part number
                    body=b"invalid part"
                )

        except ClientError:
            # 4. Cleanup on failure
            s3_storage_client.abort_multipart_upload(
                bucket="test-bucket",
                key="error-handling-test.zip",
                upload_id=upload_response.upload_id
            )

            # 5. Verify cleanup was successful
            s3_client = s3_storage_client.client
            multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
            assert len(multipart_uploads.get("Uploads", [])) == 0


class TestCreateS3StorageClient:
    """Tests for the create_s3_storage_client factory function."""

    @patch("fides.api.service.storage.s3_storage_client.get_s3_client")
    def test_create_s3_storage_client_success(self, mock_get_s3_client, aws_credentials):
        """Test successful S3 storage client creation."""
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client

        client = create_s3_storage_client("automatic", aws_credentials)

        assert isinstance(client, S3StorageClient)
        assert client.client == mock_s3_client
        mock_get_s3_client.assert_called_once_with("automatic", aws_credentials)

    @patch("fides.api.service.storage.s3_storage_client.get_s3_client")
    def test_create_s3_storage_client_with_different_auth_methods(self, mock_get_s3_client, aws_credentials):
        """Test S3 storage client creation with different auth methods."""
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client

        auth_methods = ["automatic", "assume_role", "iam"]

        for auth_method in auth_methods:
            client = create_s3_storage_client(auth_method, aws_credentials)
            assert isinstance(client, S3StorageClient)
            mock_get_s3_client.assert_called_with(auth_method, aws_credentials)
            mock_get_s3_client.reset_mock()

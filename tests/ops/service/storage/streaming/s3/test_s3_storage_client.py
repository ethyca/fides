import json
from unittest.mock import patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from fides.api.common_exceptions import StorageUploadError
from fides.api.service.storage.streaming.cloud_storage_client import (
    MultipartUploadResponse,
    UploadPartResponse,
)
from fides.api.service.storage.streaming.s3.s3_storage_client import (
    S3StorageClient,
    create_s3_storage_client,
)
from fides.api.service.storage.streaming.util import AWS_MIN_PART_SIZE


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    return {
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
        "aws_session_token": "testing",
        "region_name": "us-east-1",
    }


@pytest.fixture
def s3_client(aws_credentials):
    """Create a real S3 client using moto."""
    with mock_aws():
        client = boto3.client("s3", **aws_credentials)
        client.create_bucket(Bucket="test-bucket")
        yield client


@pytest.fixture
def s3_storage_client(s3_client):
    """Create S3StorageClient instance with real S3 client from moto."""
    return S3StorageClient(s3_client)


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {"source": "privacy_request", "format": "zip", "request_id": "test-123"}


@pytest.fixture
def test_file_content():
    """Sample file content for testing."""
    return b"This is a test file content for S3 operations testing."


@pytest.fixture
def part_content():
    """Sample part content for testing."""
    part_size = AWS_MIN_PART_SIZE  # Use constant instead of hardcoded 5MB
    # Calculate how many repetitions needed to reach AWS_MIN_PART_SIZE
    base_content = b"test content"
    repetitions_needed = (part_size // len(base_content)) + 1
    return base_content * repetitions_needed


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
            metadata=sample_metadata,
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

        # Clean up
        s3_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="test-file.zip",
            upload_id=response.upload_id,
        )

    def test_create_multipart_upload_without_metadata(self, s3_storage_client):
        """Test multipart upload creation without metadata."""
        response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-file-no-metadata.zip",
            content_type="application/zip",
        )

        assert response.upload_id is not None

        # Verify the upload was created
        s3_client = s3_storage_client.client
        multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
        assert len(multipart_uploads["Uploads"]) == 1
        assert multipart_uploads["Uploads"][0]["Key"] == "test-file-no-metadata.zip"

        # Clean up
        s3_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="test-file-no-metadata.zip",
            upload_id=response.upload_id,
        )

    def test_create_multipart_upload_bucket_not_exists(self, s3_storage_client):
        """Test multipart upload creation with non-existent bucket."""
        with pytest.raises(ClientError) as exc_info:
            s3_storage_client.create_multipart_upload(
                bucket="nonexistent-bucket",
                key="test-file.zip",
                content_type="application/zip",
            )

        # Check for either the AWS error code or the moto error message
        error_str = str(exc_info.value)
        assert any(
            [
                "NoSuchBucket" in error_str,  # Real AWS error
                "404" in error_str,  # moto error code
                "Not Found" in error_str,  # moto error message
            ]
        ), f"Expected error to contain NoSuchBucket, 404, or Not Found, got: {error_str}"

    def test_upload_part_success(self, s3_storage_client, part_content):
        """Test successful part upload."""
        # First create a multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket", key="test-parts.zip", content_type="application/zip"
        )

        # Ensure we meet the minimum size requirement
        assert (
            len(part_content) >= AWS_MIN_PART_SIZE
        ), f"Part size {len(part_content)} < {AWS_MIN_PART_SIZE}"
        response = s3_storage_client.upload_part(
            bucket="test-bucket",
            key="test-parts.zip",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=part_content,
        )

        assert isinstance(response, UploadPartResponse)
        assert response.etag is not None
        assert response.part_number == 1
        assert "ETag" in response.metadata

        # Clean up
        s3_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="test-parts.zip",
            upload_id=upload_response.upload_id,
        )

    def test_upload_part_invalid_upload_id(self, s3_storage_client, part_content):
        """Test part upload with invalid upload ID."""
        with pytest.raises(KeyError) as exc_info:
            s3_storage_client.upload_part(
                bucket="test-bucket",
                key="test-parts.zip",
                upload_id="invalid-upload-id",
                part_number=1,
                body=part_content,  # Use valid part content
            )

        assert "invalid-upload-id" in str(exc_info.value)

    def test_upload_part_invalid_part_number_validation(
        self, s3_storage_client, part_content
    ):
        """Test that our PartNumber validation catches invalid part numbers."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="validation-test.zip",
            content_type="application/zip",
        )

        # Test with part number 0 (should fail validation)
        with pytest.raises(
            ValueError, match="Part number must be between 1 and 10,000"
        ):
            s3_storage_client.upload_part(
                bucket="test-bucket",
                key="validation-test.zip",
                upload_id=upload_response.upload_id,
                part_number=0,  # Invalid - must be >= 1
                body=part_content,  # Use valid part content
            )

        # Test with part number 10001 (should fail validation)
        with pytest.raises(
            ValueError, match="Part number must be between 1 and 10,000"
        ):
            s3_storage_client.upload_part(
                bucket="test-bucket",
                key="validation-test.zip",
                upload_id=upload_response.upload_id,
                part_number=10001,  # Invalid - must be <= 10000
                body=part_content,  # Use valid part content
            )

        response = s3_storage_client.upload_part(
            bucket="test-bucket",
            key="validation-test.zip",
            upload_id=upload_response.upload_id,
            part_number=1,  # Valid
            body=part_content,
        )
        assert response.part_number == 1

        # Clean up
        s3_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="validation-test.zip",
            upload_id=upload_response.upload_id,
        )

    def test_upload_part_invalid_upload_id_validation(self, s3_storage_client):
        """Test that our UploadId validation catches invalid upload IDs."""
        # Test with empty upload ID (should fail validation)
        with pytest.raises(ValueError, match="Upload ID cannot be empty or whitespace"):
            s3_storage_client.upload_part(
                bucket="test-bucket",
                key="validation-test.zip",
                upload_id="",  # Invalid - empty
                part_number=1,
                body=b"test content",
            )

        # Test with whitespace-only upload ID (should fail validation)
        with pytest.raises(ValueError, match="Upload ID cannot be empty or whitespace"):
            s3_storage_client.upload_part(
                bucket="test-bucket",
                key="validation-test.zip",
                upload_id="   ",  # Invalid - whitespace only
                part_number=1,
                body=b"test content",
            )

        # Test with None upload ID (should fail validation)
        with pytest.raises(ValueError, match="Input should be a valid string"):
            s3_storage_client.upload_part(
                bucket="test-bucket",
                key="validation-test.zip",
                upload_id=None,  # Invalid - None
                part_number=1,
                body=b"test content",
            )

    def test_complete_multipart_upload_success(self, s3_storage_client, part_content):
        """Test successful multipart upload completion."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-complete.zip",
            content_type="application/zip",
        )

        # Upload parts with proper sizes (AWS S3 minimum per part)
        parts = []
        for i in range(1, 4):
            part_response = s3_storage_client.upload_part(
                bucket="test-bucket",
                key="test-complete.zip",
                upload_id=upload_response.upload_id,
                part_number=i,
                body=part_content,
            )
            parts.append(part_response)

        # Complete the upload
        s3_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-complete.zip",
            upload_id=upload_response.upload_id,
            parts=parts,
        )

        # Verify the object now exists
        s3_client = s3_storage_client.client
        head_response = s3_client.head_object(
            Bucket="test-bucket", Key="test-complete.zip"
        )
        assert head_response["ContentLength"] > 0

        # Verify no pending multipart uploads
        multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
        assert len(multipart_uploads.get("Uploads", [])) == 0

    def test_complete_multipart_upload_with_metadata(
        self, s3_storage_client, sample_metadata, part_content
    ):
        """Test multipart upload completion with metadata."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-metadata.zip",
            content_type="application/zip",
        )

        part_response = s3_storage_client.upload_part(
            bucket="test-bucket",
            key="test-metadata.zip",
            upload_id=upload_response.upload_id,
            part_number=1,
            body=part_content,
        )

        # Complete with metadata
        s3_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="test-metadata.zip",
            upload_id=upload_response.upload_id,
            parts=[part_response],
            metadata=sample_metadata,
        )

        # Note: Current implementation doesn't use metadata parameter
        # This test documents the current behavior
        s3_client = s3_storage_client.client
        head_response = s3_client.head_object(
            Bucket="test-bucket", Key="test-metadata.zip"
        )
        assert head_response["ContentLength"] > 0

    def test_complete_multipart_upload_invalid_parts(self, s3_storage_client):
        """Test multipart upload completion with invalid parts."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="test-invalid-parts.zip",
            content_type="application/zip",
        )

        # Try to complete with invalid parts
        invalid_parts = [
            UploadPartResponse(etag="invalid-etag", part_number=999, metadata={})
        ]

        with pytest.raises(ClientError) as exc_info:
            s3_storage_client.complete_multipart_upload(
                bucket="test-bucket",
                key="test-invalid-parts.zip",
                upload_id=upload_response.upload_id,
                parts=invalid_parts,
            )

        # Check for either the AWS error code or the moto error message
        error_str = str(exc_info.value)
        assert any(
            [
                "InvalidPart" in error_str,  # Real AWS error
                "400" in error_str,  # moto error code
                "Bad Request" in error_str,  # moto error message
            ]
        ), f"Expected error to contain InvalidPart, 400, or Bad Request, got: {error_str}"

        # Clean up
        s3_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="test-invalid-parts.zip",
            upload_id=upload_response.upload_id,
        )

    def test_abort_multipart_upload_success(self, s3_storage_client):
        """Test successful multipart upload abortion."""
        # Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket", key="test-abort.zip", content_type="application/zip"
        )

        # Abort the upload
        s3_storage_client.abort_multipart_upload(
            bucket="test-bucket",
            key="test-abort.zip",
            upload_id=upload_response.upload_id,
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
                upload_id="nonexistent-upload",
            )

        # Check for either the AWS error code or the moto error message
        error_str = str(exc_info.value)
        assert any(
            [
                "NoSuchUpload" in error_str,  # Real AWS error
                "404" in error_str,  # moto error code
                "Not Found" in error_str,  # moto error message
            ]
        ), f"Expected error to contain NoSuchUpload, 404, or Not Found, got: {error_str}"


class TestS3StorageClientPresignedURL:
    """Tests for presigned URL generation."""

    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_success(self, mock_create_url, s3_storage_client):
        """Test successful presigned URL generation."""
        expected_url = "https://test-bucket.s3.amazonaws.com/test-key?signature=abc123"
        mock_create_url.return_value = expected_url

        url = s3_storage_client.generate_presigned_url(
            bucket="test-bucket", key="test-file.zip"
        )

        assert url == expected_url
        mock_create_url.assert_called_once_with(
            s3_storage_client.client, "test-bucket", "test-file.zip", None
        )

    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_with_ttl(self, mock_create_url, s3_storage_client):
        """Test presigned URL generation with custom TTL."""
        expected_url = "https://test-bucket.s3.amazonaws.com/test-key?signature=abc123&expires=86400"
        mock_create_url.return_value = expected_url

        url = s3_storage_client.generate_presigned_url(
            bucket="test-bucket", key="test-file.zip", ttl_seconds=86400
        )

        assert url == expected_url
        mock_create_url.assert_called_once_with(
            s3_storage_client.client, "test-bucket", "test-file.zip", 86400
        )

    @patch(
        "fides.api.service.storage.streaming.s3.s3_storage_client.create_presigned_url_for_s3"
    )
    def test_generate_presigned_url_error(self, mock_create_url, s3_storage_client):
        """Test presigned URL generation with error."""
        mock_create_url.side_effect = Exception("URL generation failed")

        with pytest.raises(Exception) as exc_info:
            s3_storage_client.generate_presigned_url(
                bucket="test-bucket", key="test-file.zip"
            )

        assert "URL generation failed" in str(exc_info.value)


class TestS3StorageClientIntegration:
    """Integration tests for complete multipart upload workflow."""

    def test_complete_multipart_upload_workflow(self, s3_storage_client, part_content):
        """Test complete multipart upload workflow from start to finish."""
        # 1. Create multipart upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket", key="large-file.zip", content_type="application/zip"
        )

        assert upload_response.upload_id is not None

        # 2. Upload multiple parts with proper sizes (AWS S3 minimum per part)
        parts = []
        for i in range(1, 4):
            part_response = s3_storage_client.upload_part(
                bucket="test-bucket",
                key="large-file.zip",
                upload_id=upload_response.upload_id,
                part_number=i,
                body=part_content,
            )
            parts.append(part_response)

        assert len(parts) == 3
        assert all(isinstance(part, UploadPartResponse) for part in parts)

        # 3. Complete multipart upload
        s3_storage_client.complete_multipart_upload(
            bucket="test-bucket",
            key="large-file.zip",
            upload_id=upload_response.upload_id,
            parts=parts,
        )

        # 4. Verify the final object exists and has correct content
        s3_client = s3_storage_client.client
        head_response = s3_client.head_object(
            Bucket="test-bucket", Key="large-file.zip"
        )
        assert head_response["ContentLength"] > 0

        # 5. Verify no pending multipart uploads
        multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
        assert len(multipart_uploads.get("Uploads", [])) == 0

    def test_multipart_upload_with_error_handling(
        self, s3_storage_client, part_content
    ):
        """Test multipart upload workflow with error handling and cleanup."""
        # 1. Create upload
        upload_response = s3_storage_client.create_multipart_upload(
            bucket="test-bucket",
            key="error-handling-test.zip",
            content_type="application/zip",
        )

        try:
            # 2. Upload first part successfully with proper size
            part1_response = s3_storage_client.upload_part(
                bucket="test-bucket",
                key="error-handling-test.zip",
                upload_id=upload_response.upload_id,
                part_number=1,
                body=part_content,
            )

            # 3. Try to upload part with non-existent upload ID (should fail)
            with pytest.raises(KeyError):
                s3_storage_client.upload_part(
                    bucket="test-bucket",
                    key="error-handling-test.zip",
                    upload_id="non-existent-upload-id",  # This should definitely fail
                    part_number=2,  # Valid part number
                    body=part_content,  # Use valid part content
                )

        except KeyError:
            # 4. Cleanup on failure
            s3_storage_client.abort_multipart_upload(
                bucket="test-bucket",
                key="error-handling-test.zip",
                upload_id=upload_response.upload_id,
            )

            # 5. Verify cleanup was successful
            s3_client = s3_storage_client.client
            multipart_uploads = s3_client.list_multipart_uploads(Bucket="test-bucket")
            assert len(multipart_uploads.get("Uploads", [])) == 0


class TestCreateS3StorageClient:
    """Tests for the create_s3_storage_client factory function."""

    def test_create_s3_storage_client_success(self, aws_credentials):
        """Test successful S3 storage client creation."""
        with mock_aws():
            client = create_s3_storage_client("automatic", aws_credentials)

            assert isinstance(client, S3StorageClient)
            assert client.client is not None

            # Verify the client can perform basic S3 operations
            s3_client = client.client
            s3_client.create_bucket(Bucket="factory-test-bucket")

            # Test that we can use the storage client for basic operations
            response = client.create_multipart_upload(
                bucket="factory-test-bucket",
                key="test-factory-file.zip",
                content_type="application/zip",
            )
            assert response.upload_id is not None

    def test_create_s3_storage_client_with_different_auth_methods(
        self, aws_credentials
    ):
        """Test S3 storage client creation with different auth methods."""
        auth_methods = ["automatic", "secret_keys"]

        for auth_method in auth_methods:
            with mock_aws():
                if auth_method == "secret_keys":
                    # For secret_keys method, we need the actual credentials
                    test_credentials = {
                        "aws_access_key_id": "testing",
                        "aws_secret_access_key": "testing",
                        "region_name": "us-east-1",
                    }
                else:
                    test_credentials = aws_credentials

                client = create_s3_storage_client(auth_method, test_credentials)
                assert isinstance(client, S3StorageClient)

                # Verify the client works by testing a basic operation
                s3_client = client.client
                bucket_name = f"test-bucket-{auth_method}"
                s3_client.create_bucket(Bucket=bucket_name)

                # Test multipart upload creation
                response = client.create_multipart_upload(
                    bucket=bucket_name,
                    key="test-file.zip",
                    content_type="application/zip",
                )
                assert response.upload_id is not None

    def test_create_s3_storage_client_with_assume_role(self, aws_credentials):
        """Test S3 storage client creation with assume role auth method."""
        with mock_aws():
            # Create a test role first
            sts = boto3.client("sts")
            iam = boto3.client("iam")

            # Get account ID
            identity = sts.get_caller_identity()
            account_id = identity["Account"]

            # Create a test role
            role_name = "TestAssumeRole"
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }

            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            )

            role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

            # Test creating client with assume role
            test_credentials = {
                "aws_access_key_id": "testing",
                "aws_secret_access_key": "testing",
                "region_name": "us-east-1",
                "assume_role_arn": role_arn,
            }

            client = create_s3_storage_client("secret_keys", test_credentials)
            assert isinstance(client, S3StorageClient)

            # Verify the client works
            s3_client = client.client
            s3_client.create_bucket(Bucket="assume-role-test-bucket")

    def test_create_s3_storage_client_invalid_auth_method(self, aws_credentials):
        """Test S3 storage client creation with invalid auth method."""
        with mock_aws():
            with pytest.raises(ValueError, match="AWS auth method not supported"):
                create_s3_storage_client("invalid_method", aws_credentials)

    def test_create_s3_storage_client_missing_secrets(self):
        """Test S3 storage client creation with missing secrets for secret_keys method."""
        with mock_aws():
            with pytest.raises(
                StorageUploadError, match="Storage secrets not found for S3 storage"
            ):
                create_s3_storage_client("secret_keys", {})

import pytest
from pydantic import ValidationError

from fides.api.service.storage.streaming.gcs.gcs_schemas import (
    GCSAbortResumableUploadRequest,
    GCSChunkUploadRequest,
    GCSChunkUploadResponse,
    GCSCompleteResumableUploadRequest,
    GCSGenerateSignedUrlRequest,
    GCSGetObjectRangeRequest,
    GCSGetObjectRequest,
    GCSResumableUploadRequest,
    GCSResumableUploadResponse,
)
from fides.api.service.storage.streaming.util import GCS_MIN_CHUNK_SIZE


class TestGCSResumableUploadRequest:
    """Test cases for GCSResumableUploadRequest schema."""

    def test_valid_resumable_upload_request(self):
        """Test that a valid resumable upload request can be created."""
        request = GCSResumableUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            content_type="application/zip",
            metadata={"source": "test"},
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.content_type == "application/zip"
        assert request.metadata == {"source": "test"}

    def test_resumable_upload_request_without_metadata(self):
        """Test that resumable upload request can be created without metadata."""
        request = GCSResumableUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            content_type="application/zip",
        )

        assert request.metadata is None

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "bucket", "", "Bucket cannot be empty or whitespace", id="bucket-empty"
            ),
            pytest.param(
                "bucket",
                "   ",
                "Bucket cannot be empty or whitespace",
                id="bucket-whitespace",
            ),
            pytest.param(
                "bucket", None, "Input should be a valid string", id="bucket-none"
            ),
            pytest.param(
                "bucket",
                "ab",
                "GCS bucket name must be between 3 and 63 characters",
                id="bucket-too-short",
            ),
            pytest.param(
                "bucket",
                "a" * 64,
                "GCS bucket name must be between 3 and 63 characters",
                id="bucket-too-long",
            ),
            pytest.param(
                "bucket",
                "-invalid",
                "GCS bucket name must start with a letter or number",
                id="bucket-starts-with-hyphen",
            ),
            pytest.param(
                "bucket",
                "invalid-",
                "GCS bucket name must end with a letter or number",
                id="bucket-ends-with-hyphen",
            ),
            pytest.param(
                "bucket",
                "invalid@bucket",
                "GCS bucket name can only contain letters, numbers, hyphens, and underscores",
                id="bucket-invalid-char",
            ),
            pytest.param(
                "key", "", "Key cannot be empty or whitespace", id="key-empty"
            ),
            pytest.param(
                "key", "   ", "Key cannot be empty or whitespace", id="key-whitespace"
            ),
            pytest.param("key", None, "Input should be a valid string", id="key-none"),
            pytest.param(
                "key",
                "/invalid",
                "GCS object key cannot start with '/'",
                id="key-starts-with-slash",
            ),
            pytest.param(
                "key",
                "a" * 1025,
                "GCS object key cannot exceed 1024 characters",
                id="key-too-long",
            ),
            pytest.param(
                "content_type",
                "",
                "Content type cannot be empty or whitespace",
                id="content-type-empty",
            ),
            pytest.param(
                "content_type",
                "   ",
                "Content type cannot be empty or whitespace",
                id="content-type-whitespace",
            ),
            pytest.param(
                "content_type",
                None,
                "Input should be a valid string",
                id="content-type-none",
            ),
        ],
    )
    def test_resumable_upload_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket-123",
            "key": "test-file.zip",
            "content_type": "application/zip",
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSResumableUploadRequest(**valid_data)

    def test_resumable_upload_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = GCSResumableUploadRequest(
            bucket="  test-bucket-123  ",
            key="  test-file.zip  ",
            content_type="  application/zip  ",
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.content_type == "application/zip"

    def test_resumable_upload_request_bucket_boundaries(self):
        """Test that bucket name boundaries are correctly enforced."""
        # Test minimum valid bucket name length
        request = GCSResumableUploadRequest(
            bucket="abc",
            key="test-file.zip",
            content_type="application/zip",
        )
        assert request.bucket == "abc"

        # Test maximum valid bucket name length
        request = GCSResumableUploadRequest(
            bucket="a" * 63,
            key="test-file.zip",
            content_type="application/zip",
        )
        assert len(request.bucket) == 63

    def test_resumable_upload_request_key_boundaries(self):
        """Test that object key boundaries are correctly enforced."""
        # Test maximum valid key length
        request = GCSResumableUploadRequest(
            bucket="test-bucket-123",
            key="a" * 1024,
            content_type="application/zip",
        )
        assert len(request.key) == 1024


class TestGCSResumableUploadResponse:
    """Test cases for GCSResumableUploadResponse schema."""

    def test_valid_resumable_upload_response(self):
        """Test that a valid resumable upload response can be created."""
        response = GCSResumableUploadResponse(
            upload_id="test-upload-id-123",
            resumable_url="https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o",
            metadata={"status": "created"},
        )

        assert response.upload_id == "test-upload-id-123"
        assert (
            response.resumable_url
            == "https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o"
        )
        assert response.metadata == {"status": "created"}

    def test_resumable_upload_response_without_metadata(self):
        """Test that resumable upload response can be created without metadata."""
        response = GCSResumableUploadResponse(
            upload_id="test-upload-id-123",
            resumable_url="https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o",
        )

        assert response.metadata is None

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "upload_id",
                "",
                "Upload ID cannot be empty or whitespace",
                id="upload-id-empty",
            ),
            pytest.param(
                "upload_id",
                "   ",
                "Upload ID cannot be empty or whitespace",
                id="upload-id-whitespace",
            ),
            pytest.param(
                "upload_id", None, "Input should be a valid string", id="upload-id-none"
            ),
            pytest.param(
                "resumable_url",
                "",
                "Resumable URL cannot be empty or whitespace",
                id="resumable-url-empty",
            ),
            pytest.param(
                "resumable_url",
                "   ",
                "Resumable URL cannot be empty or whitespace",
                id="resumable-url-whitespace",
            ),
            pytest.param(
                "resumable_url",
                None,
                "Input should be a valid string",
                id="resumable-url-none",
            ),
            pytest.param(
                "resumable_url",
                "http://example.com",
                "Resumable URL must be an HTTPS URL",
                id="resumable-url-http",
            ),
            pytest.param(
                "resumable_url",
                "ftp://example.com",
                "Resumable URL must be an HTTPS URL",
                id="resumable-url-ftp",
            ),
            pytest.param(
                "resumable_url",
                "not-a-url",
                "Resumable URL must be an HTTPS URL",
                id="resumable-url-invalid",
            ),
        ],
    )
    def test_resumable_upload_response_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "upload_id": "test-upload-id-123",
            "resumable_url": "https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o",
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSResumableUploadResponse(**valid_data)

    def test_resumable_upload_response_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        response = GCSResumableUploadResponse(
            upload_id="  test-upload-id-123  ",
            resumable_url="  https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o  ",
        )

        assert response.upload_id == "test-upload-id-123"
        assert (
            response.resumable_url
            == "https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o"
        )


class TestGCSChunkUploadRequest:
    """Test cases for GCSChunkUploadRequest schema."""

    def test_valid_chunk_upload_request(self):
        """Test that a valid chunk upload request can be created."""
        request = GCSChunkUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            chunk_data=b"x" * GCS_MIN_CHUNK_SIZE,
            metadata={"chunk": "1"},
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"
        assert len(request.chunk_data) == GCS_MIN_CHUNK_SIZE
        assert request.metadata == {"chunk": "1"}

    def test_chunk_upload_request_without_metadata(self):
        """Test that chunk upload request can be created without metadata."""
        request = GCSChunkUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            chunk_data=b"x" * GCS_MIN_CHUNK_SIZE,
        )

        assert request.metadata is None

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "bucket", "", "Bucket cannot be empty or whitespace", id="bucket-empty"
            ),
            pytest.param(
                "bucket",
                "   ",
                "Bucket cannot be empty or whitespace",
                id="bucket-whitespace",
            ),
            pytest.param(
                "bucket", None, "Input should be a valid string", id="bucket-none"
            ),
            pytest.param(
                "key", "", "Key cannot be empty or whitespace", id="key-empty"
            ),
            pytest.param(
                "key", "   ", "Key cannot be empty or whitespace", id="key-whitespace"
            ),
            pytest.param("key", None, "Input should be a valid string", id="key-none"),
            pytest.param(
                "upload_id",
                "",
                "Upload ID cannot be empty or whitespace",
                id="upload-id-empty",
            ),
            pytest.param(
                "upload_id",
                "   ",
                "Upload ID cannot be empty or whitespace",
                id="upload-id-whitespace",
            ),
            pytest.param(
                "upload_id", None, "Input should be a valid string", id="upload-id-none"
            ),
            pytest.param(
                "chunk_data", b"", "Chunk data cannot be empty", id="chunk-data-empty"
            ),
            pytest.param(
                "chunk_data",
                None,
                "Input should be a valid bytes",
                id="chunk-data-none",
            ),
        ],
    )
    def test_chunk_upload_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket-123",
            "key": "test-file.zip",
            "upload_id": "test-upload-id-123",
            "chunk_data": b"x" * GCS_MIN_CHUNK_SIZE,
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSChunkUploadRequest(**valid_data)

    def test_chunk_upload_request_chunk_data_too_small(self):
        """Test that chunk data size validation enforces minimum chunk size."""
        small_chunk = b"x" * (GCS_MIN_CHUNK_SIZE - 1)

        with pytest.raises(
            ValueError,
            match=f"Chunk data must be at least {GCS_MIN_CHUNK_SIZE // 1024}KB",
        ):
            GCSChunkUploadRequest(
                bucket="test-bucket-123",
                key="test-file.zip",
                upload_id="test-upload-id-123",
                chunk_data=small_chunk,
            )

    def test_chunk_upload_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = GCSChunkUploadRequest(
            bucket="  test-bucket-123  ",
            key="  test-file.zip  ",
            upload_id="  test-upload-id-123  ",
            chunk_data=b"x" * GCS_MIN_CHUNK_SIZE,
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"


class TestGCSChunkUploadResponse:
    """Test cases for GCSChunkUploadResponse schema."""

    def test_valid_chunk_upload_response(self):
        """Test that a valid chunk upload response can be created."""
        response = GCSChunkUploadResponse(
            bytes_uploaded=1024,
            metadata={"status": "uploaded"},
        )

        assert response.bytes_uploaded == 1024
        assert response.metadata == {"status": "uploaded"}

    def test_chunk_upload_response_without_metadata(self):
        """Test that chunk upload response can be created without metadata."""
        response = GCSChunkUploadResponse(
            bytes_uploaded=1024,
        )

        assert response.metadata is None

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "bytes_uploaded",
                -1,
                "Bytes uploaded cannot be negative",
                id="bytes-uploaded-negative",
            ),
            pytest.param(
                "bytes_uploaded",
                None,
                "Input should be a valid integer",
                id="bytes-uploaded-none",
            ),
        ],
    )
    def test_chunk_upload_response_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bytes_uploaded": 1024,
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSChunkUploadResponse(**valid_data)

    def test_chunk_upload_response_zero_bytes(self):
        """Test that zero bytes uploaded is valid."""
        response = GCSChunkUploadResponse(
            bytes_uploaded=0,
        )

        assert response.bytes_uploaded == 0


class TestGCSCompleteResumableUploadRequest:
    """Test cases for GCSCompleteResumableUploadRequest schema."""

    def test_valid_complete_resumable_upload_request(self):
        """Test that a valid complete resumable upload request can be created."""
        request = GCSCompleteResumableUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            metadata={"status": "completed"},
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"
        assert request.metadata == {"status": "completed"}

    def test_complete_resumable_upload_request_without_metadata(self):
        """Test that complete resumable upload request can be created without metadata."""
        request = GCSCompleteResumableUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            upload_id="test-upload-id-123",
        )

        assert request.metadata is None

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "bucket", "", "Bucket cannot be empty or whitespace", id="bucket-empty"
            ),
            pytest.param(
                "bucket",
                "   ",
                "Bucket cannot be empty or whitespace",
                id="bucket-whitespace",
            ),
            pytest.param(
                "bucket", None, "Input should be a valid string", id="bucket-none"
            ),
            pytest.param(
                "key", "", "Key cannot be empty or whitespace", id="key-empty"
            ),
            pytest.param(
                "key", "   ", "Key cannot be empty or whitespace", id="key-whitespace"
            ),
            pytest.param("key", None, "Input should be a valid string", id="key-none"),
            pytest.param(
                "upload_id",
                "",
                "Upload ID cannot be empty or whitespace",
                id="upload-id-empty",
            ),
            pytest.param(
                "upload_id",
                "   ",
                "Upload ID cannot be empty or whitespace",
                id="upload-id-whitespace",
            ),
            pytest.param(
                "upload_id", None, "Input should be a valid string", id="upload-id-none"
            ),
        ],
    )
    def test_complete_resumable_upload_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket-123",
            "key": "test-file.zip",
            "upload_id": "test-upload-id-123",
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSCompleteResumableUploadRequest(**valid_data)

    def test_complete_resumable_upload_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = GCSCompleteResumableUploadRequest(
            bucket="  test-bucket-123  ",
            key="  test-file.zip  ",
            upload_id="  test-upload-id-123  ",
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"


class TestGCSAbortResumableUploadRequest:
    """Test cases for GCSAbortResumableUploadRequest schema."""

    def test_valid_abort_resumable_upload_request(self):
        """Test that a valid abort resumable upload request can be created."""
        request = GCSAbortResumableUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            upload_id="test-upload-id-123",
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "bucket", "", "Bucket cannot be empty or whitespace", id="bucket-empty"
            ),
            pytest.param(
                "bucket",
                "   ",
                "Bucket cannot be empty or whitespace",
                id="bucket-whitespace",
            ),
            pytest.param(
                "bucket", None, "Input should be a valid string", id="bucket-none"
            ),
            pytest.param(
                "key", "", "Key cannot be empty or whitespace", id="key-empty"
            ),
            pytest.param(
                "key", "   ", "Key cannot be empty or whitespace", id="key-whitespace"
            ),
            pytest.param("key", None, "Input should be a valid string", id="key-none"),
            pytest.param(
                "upload_id",
                "",
                "Upload ID cannot be empty or whitespace",
                id="upload-id-empty",
            ),
            pytest.param(
                "upload_id",
                "   ",
                "Upload ID cannot be empty or whitespace",
                id="upload-id-whitespace",
            ),
            pytest.param(
                "upload_id", None, "Input should be a valid string", id="upload-id-none"
            ),
        ],
    )
    def test_abort_resumable_upload_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket-123",
            "key": "test-file.zip",
            "upload_id": "test-upload-id-123",
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSAbortResumableUploadRequest(**valid_data)

    def test_abort_resumable_upload_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = GCSAbortResumableUploadRequest(
            bucket="  test-bucket-123  ",
            key="  test-file.zip  ",
            upload_id="  test-upload-id-123  ",
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"


class TestGCSGetObjectRequest:
    """Test cases for GCSGetObjectRequest schema."""

    def test_valid_get_object_request(self):
        """Test that a valid get object request can be created."""
        request = GCSGetObjectRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "bucket", "", "Bucket cannot be empty or whitespace", id="bucket-empty"
            ),
            pytest.param(
                "bucket",
                "   ",
                "Bucket cannot be empty or whitespace",
                id="bucket-whitespace",
            ),
            pytest.param(
                "bucket", None, "Input should be a valid string", id="bucket-none"
            ),
            pytest.param(
                "key", "", "Key cannot be empty or whitespace", id="key-empty"
            ),
            pytest.param(
                "key", "   ", "Key cannot be empty or whitespace", id="key-whitespace"
            ),
            pytest.param("key", None, "Input should be a valid string", id="key-none"),
        ],
    )
    def test_get_object_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket-123",
            "key": "test-file.zip",
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSGetObjectRequest(**valid_data)

    def test_get_object_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = GCSGetObjectRequest(
            bucket="  test-bucket-123  ",
            key="  test-file.zip  ",
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"


class TestGCSGetObjectRangeRequest:
    """Test cases for GCSGetObjectRangeRequest schema."""

    def test_valid_get_object_range_request(self):
        """Test that a valid get object range request can be created."""
        request = GCSGetObjectRangeRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            start_byte=0,
            end_byte=1023,
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.start_byte == 0
        assert request.end_byte == 1023

    def test_get_object_range_request_zero_range(self):
        """Test that a zero-byte range request is valid."""
        request = GCSGetObjectRangeRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            start_byte=100,
            end_byte=100,
        )

        assert request.start_byte == 100
        assert request.end_byte == 100

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "bucket", "", "Bucket cannot be empty or whitespace", id="bucket-empty"
            ),
            pytest.param(
                "bucket",
                "   ",
                "Bucket cannot be empty or whitespace",
                id="bucket-whitespace",
            ),
            pytest.param(
                "bucket", None, "Input should be a valid string", id="bucket-none"
            ),
            pytest.param(
                "key", "", "Key cannot be empty or whitespace", id="key-empty"
            ),
            pytest.param(
                "key", "   ", "Key cannot be empty or whitespace", id="key-whitespace"
            ),
            pytest.param("key", None, "Input should be a valid string", id="key-none"),
            pytest.param(
                "start_byte",
                -1,
                "Input should be greater than or equal to 0",
                id="start-byte-negative",
            ),
            pytest.param(
                "start_byte",
                None,
                "Input should be a valid integer",
                id="start-byte-none",
            ),
            pytest.param(
                "end_byte",
                -1,
                "Input should be greater than or equal to 0",
                id="end-byte-negative",
            ),
            pytest.param(
                "end_byte", None, "Input should be a valid integer", id="end-byte-none"
            ),
        ],
    )
    def test_get_object_range_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket-123",
            "key": "test-file.zip",
            "start_byte": 0,
            "end_byte": 1023,
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSGetObjectRangeRequest(**valid_data)

    def test_get_object_range_request_end_byte_less_than_start_byte(self):
        """Test that end_byte must be greater than or equal to start_byte."""
        with pytest.raises(
            ValueError, match="end_byte must be greater than or equal to start_byte"
        ):
            GCSGetObjectRangeRequest(
                bucket="test-bucket-123",
                key="test-file.zip",
                start_byte=100,
                end_byte=99,
            )

    def test_get_object_range_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = GCSGetObjectRangeRequest(
            bucket="  test-bucket-123  ",
            key="  test-file.zip  ",
            start_byte=0,
            end_byte=1023,
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"


class TestGCSGenerateSignedUrlRequest:
    """Test cases for GCSGenerateSignedUrlRequest schema."""

    def test_valid_generate_signed_url_request(self):
        """Test that a valid generate signed URL request can be created."""
        request = GCSGenerateSignedUrlRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            ttl_seconds=3600,
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"
        assert request.ttl_seconds == 3600

    def test_generate_signed_url_request_without_ttl(self):
        """Test that generate signed URL request can be created without TTL."""
        request = GCSGenerateSignedUrlRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
        )

        assert request.ttl_seconds is None

    def test_generate_signed_url_request_ttl_boundaries(self):
        """Test that TTL boundaries are correctly enforced."""
        # Test minimum valid TTL
        request = GCSGenerateSignedUrlRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            ttl_seconds=1,
        )
        assert request.ttl_seconds == 1

        # Test maximum valid TTL (7 days)
        request = GCSGenerateSignedUrlRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            ttl_seconds=604800,
        )
        assert request.ttl_seconds == 604800

    @pytest.mark.parametrize(
        "field, invalid_value, expected_error",
        [
            pytest.param(
                "bucket", "", "Bucket cannot be empty or whitespace", id="bucket-empty"
            ),
            pytest.param(
                "bucket",
                "   ",
                "Bucket cannot be empty or whitespace",
                id="bucket-whitespace",
            ),
            pytest.param(
                "bucket", None, "Input should be a valid string", id="bucket-none"
            ),
            pytest.param(
                "key", "", "Key cannot be empty or whitespace", id="key-empty"
            ),
            pytest.param(
                "key", "   ", "Key cannot be empty or whitespace", id="key-whitespace"
            ),
            pytest.param("key", None, "Input should be a valid string", id="key-none"),
            pytest.param(
                "ttl_seconds",
                0,
                "Input should be greater than or equal to 1",
                id="ttl-zero",
            ),
            pytest.param(
                "ttl_seconds",
                -1,
                "Input should be greater than or equal to 1",
                id="ttl-negative",
            ),
            pytest.param(
                "ttl_seconds",
                604801,
                "Input should be less than or equal to 604800",
                id="ttl-too-large",
            ),
        ],
    )
    def test_generate_signed_url_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket-123",
            "key": "test-file.zip",
            "ttl_seconds": 3600,
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            GCSGenerateSignedUrlRequest(**valid_data)

    def test_generate_signed_url_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = GCSGenerateSignedUrlRequest(
            bucket="  test-bucket-123  ",
            key="  test-file.zip  ",
            ttl_seconds=3600,
        )

        assert request.bucket == "test-bucket-123"
        assert request.key == "test-file.zip"


class TestGCSSchemasConfig:
    """Test cases for GCS schema configuration."""

    def test_gcs_resumable_upload_request_config(self):
        """Test that GCSResumableUploadRequest has correct configuration."""
        request = GCSResumableUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            content_type="application/zip",
        )

        # Test that extra fields are forbidden
        with pytest.raises(ValidationError):
            GCSResumableUploadRequest(
                bucket="test-bucket-123",
                key="test-file.zip",
                content_type="application/zip",
                extra_field="should_fail",
            )

    def test_gcs_resumable_upload_response_config(self):
        """Test that GCSResumableUploadResponse has correct configuration."""
        response = GCSResumableUploadResponse(
            upload_id="test-upload-id-123",
            resumable_url="https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o",
        )

        # Test that extra fields are allowed
        response_with_extra = GCSResumableUploadResponse(
            upload_id="test-upload-id-123",
            resumable_url="https://storage.googleapis.com/upload/storage/v1/b/test-bucket/o",
            extra_field="should_work",
        )
        assert hasattr(response_with_extra, "extra_field")

    def test_gcs_chunk_upload_request_config(self):
        """Test that GCSChunkUploadRequest has correct configuration."""
        request = GCSChunkUploadRequest(
            bucket="test-bucket-123",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            chunk_data=b"x" * GCS_MIN_CHUNK_SIZE,
        )

        # Test that extra fields are forbidden
        with pytest.raises(ValidationError):
            GCSChunkUploadRequest(
                bucket="test-bucket-123",
                key="test-file.zip",
                upload_id="test-upload-id-123",
                chunk_data=b"x" * GCS_MIN_CHUNK_SIZE,
                extra_field="should_fail",
            )

    def test_gcs_chunk_upload_response_config(self):
        """Test that GCSChunkUploadResponse has correct configuration."""
        response = GCSChunkUploadResponse(
            bytes_uploaded=1024,
        )

        # Test that extra fields are allowed
        response_with_extra = GCSChunkUploadResponse(
            bytes_uploaded=1024,
            extra_field="should_work",
        )
        assert hasattr(response_with_extra, "extra_field")

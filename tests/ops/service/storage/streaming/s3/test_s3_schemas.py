import pytest
from pydantic import ValidationError

from fides.api.service.storage.streaming.s3.s3_schemas import (
    AWSAbortMultipartUploadRequest,
    AWSCompleteMultipartUploadRequest,
    AWSCreateMultipartUploadRequest,
    AWSGeneratePresignedUrlRequest,
    AWSUploadPartRequest,
)
from fides.api.service.storage.streaming.schemas import UploadPartResponse
from fides.api.service.storage.streaming.util import AWS_MIN_PART_SIZE


class TestAWSUploadPartRequest:
    """Test cases for AWSUploadPartRequest schema."""

    def test_valid_upload_part_request(self):
        """Test that a valid upload part request can be created."""
        request = AWSUploadPartRequest(
            bucket="test-bucket",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            part_number=1,
            body=b"x" * AWS_MIN_PART_SIZE,
            metadata={"source": "test"},
        )

        assert request.bucket == "test-bucket"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"
        assert request.part_number == 1
        assert len(request.body) == AWS_MIN_PART_SIZE
        assert request.metadata == {"source": "test"}

    def test_upload_part_request_without_metadata(self):
        """Test that upload part request can be created without metadata."""
        request = AWSUploadPartRequest(
            bucket="test-bucket",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            part_number=1,
            body=b"x" * AWS_MIN_PART_SIZE,
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
                "part_number",
                0,
                "Part number must be between 1 and 10,000",
                id="part-number-zero",
            ),
            pytest.param(
                "part_number",
                10001,
                "Part number must be between 1 and 10,000",
                id="part-number-too-large",
            ),
            pytest.param(
                "part_number",
                -1,
                "Part number must be between 1 and 10,000",
                id="part-number-negative",
            ),
            pytest.param(
                "part_number",
                None,
                "Input should be a valid integer",
                id="part-number-none",
            ),
            pytest.param("body", b"", "Body cannot be empty", id="body-empty"),
            pytest.param("body", None, "Input should be a valid bytes", id="body-none"),
        ],
    )
    def test_upload_part_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket",
            "key": "test-file.zip",
            "upload_id": "test-upload-id-123",
            "part_number": 1,
            "body": b"x" * AWS_MIN_PART_SIZE,
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            AWSUploadPartRequest(**valid_data)

    def test_upload_part_request_body_too_small(self):
        """Test that body size validation enforces minimum part size."""
        small_body = b"x" * (AWS_MIN_PART_SIZE - 1)

        with pytest.raises(
            ValueError, match=f"Body must be at least {AWS_MIN_PART_SIZE} bytes"
        ):
            AWSUploadPartRequest(
                bucket="test-bucket",
                key="test-file.zip",
                upload_id="test-upload-id-123",
                part_number=1,
                body=small_body,
            )

    def test_upload_part_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = AWSUploadPartRequest(
            bucket="  test-bucket  ",
            key="  test-file.zip  ",
            upload_id="  test-upload-id-123  ",
            part_number=1,
            body=b"x" * AWS_MIN_PART_SIZE,
        )

        assert request.bucket == "test-bucket"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"

    def test_upload_part_request_part_number_boundaries(self):
        """Test that part number boundaries are correctly enforced."""
        # Test minimum valid part number
        request = AWSUploadPartRequest(
            bucket="test-bucket",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            part_number=1,
            body=b"x" * AWS_MIN_PART_SIZE,
        )
        assert request.part_number == 1

        # Test maximum valid part number
        request = AWSUploadPartRequest(
            bucket="test-bucket",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            part_number=10000,
            body=b"x" * AWS_MIN_PART_SIZE,
        )
        assert request.part_number == 10000


class TestAWSCreateMultipartUploadRequest:
    """Test cases for AWSCreateMultipartUploadRequest schema."""

    def test_valid_create_multipart_upload_request(self):
        """Test that a valid create multipart upload request can be created."""
        request = AWSCreateMultipartUploadRequest(
            bucket="test-bucket",
            key="test-file.zip",
            content_type="application/zip",
            metadata={"source": "test"},
        )

        assert request.bucket == "test-bucket"
        assert request.key == "test-file.zip"
        assert request.content_type == "application/zip"
        assert request.metadata == {"source": "test"}

    def test_create_multipart_upload_request_without_metadata(self):
        """Test that create multipart upload request can be created without metadata."""
        request = AWSCreateMultipartUploadRequest(
            bucket="test-bucket",
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
                "key", "", "Key cannot be empty or whitespace", id="key-empty"
            ),
            pytest.param(
                "key", "   ", "Key cannot be empty or whitespace", id="key-whitespace"
            ),
            pytest.param("key", None, "Input should be a valid string", id="key-none"),
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
    def test_create_multipart_upload_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket",
            "key": "test-file.zip",
            "content_type": "application/zip",
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            AWSCreateMultipartUploadRequest(**valid_data)

    def test_create_multipart_upload_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = AWSCreateMultipartUploadRequest(
            bucket="  test-bucket  ",
            key="  test-file.zip  ",
            content_type="  application/zip  ",
        )

        assert request.bucket == "test-bucket"
        assert request.key == "test-file.zip"
        assert request.content_type == "application/zip"


class TestAWSAbortMultipartUploadRequest:
    """Test cases for AWSAbortMultipartUploadRequest schema."""

    def test_valid_abort_multipart_upload_request(self):
        """Test that a valid abort multipart upload request can be created."""
        request = AWSAbortMultipartUploadRequest(
            bucket="test-bucket",
            key="test-file.zip",
            upload_id="test-upload-id-123",
        )

        assert request.bucket == "test-bucket"
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
    def test_abort_multipart_upload_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        valid_data = {
            "bucket": "test-bucket",
            "key": "test-file.zip",
            "upload_id": "test-upload-id-123",
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            AWSAbortMultipartUploadRequest(**valid_data)

    def test_abort_multipart_upload_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        request = AWSAbortMultipartUploadRequest(
            bucket="  test-bucket  ",
            key="  test-file.zip  ",
            upload_id="  test-upload-id-123  ",
        )

        assert request.bucket == "test-bucket"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"


class TestAWSGeneratePresignedUrlRequest:
    """Test cases for AWSGeneratePresignedUrlRequest schema."""

    def test_valid_generate_presigned_url_request(self):
        """Test that a valid generate presigned URL request can be created."""
        request = AWSGeneratePresignedUrlRequest(
            bucket="test-bucket",
            key="test-file.zip",
            ttl_seconds=3600,
        )

        assert request.bucket == "test-bucket"
        assert request.key == "test-file.zip"
        assert request.ttl_seconds == 3600

    def test_generate_presigned_url_request_without_ttl(self):
        """Test that generate presigned URL request can be created without TTL."""
        request = AWSGeneratePresignedUrlRequest(
            bucket="test-bucket",
            key="test-file.zip",
        )

        assert request.ttl_seconds is None

    @pytest.mark.parametrize(
        "ttl_seconds, should_raise, expected_error",
        [
            (0, True, "Input should be greater than or equal to 1"),
            (-1, True, "Input should be greater than or equal to 1"),
            (1, False, None),  # Minimum valid value
            (3600, False, None),  # 1 hour
            (86400, False, None),  # 1 day
            (604800, False, None),  # 7 days (maximum)
            (
                604801,
                True,
                "Input should be less than or equal to 604800",
            ),  # Exceeds maximum
        ],
    )
    def test_generate_presigned_url_request_ttl_validation(
        self, ttl_seconds, should_raise, expected_error
    ):
        """Test TTL validation for various values."""
        if should_raise:
            with pytest.raises(ValidationError, match=expected_error):
                AWSGeneratePresignedUrlRequest(
                    bucket="test-bucket",
                    key="test-file.zip",
                    ttl_seconds=ttl_seconds,
                )
        else:
            request = AWSGeneratePresignedUrlRequest(
                bucket="test-bucket",
                key="test-file.zip",
                ttl_seconds=ttl_seconds,
            )
            assert request.ttl_seconds == ttl_seconds


class TestAWSCompleteMultipartUploadRequest:
    """Test cases for AWSCompleteMultipartUploadRequest schema."""

    def test_valid_complete_multipart_upload_request(self):
        """Test that a valid complete multipart upload request can be created."""
        parts = [
            UploadPartResponse(etag="etag1", part_number=1),
            UploadPartResponse(etag="etag2", part_number=2),
        ]

        request = AWSCompleteMultipartUploadRequest(
            bucket="test-bucket",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            parts=parts,
            metadata={"source": "test"},
        )

        assert request.bucket == "test-bucket"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"
        assert request.parts == parts
        assert request.metadata == {"source": "test"}

    def test_complete_multipart_upload_request_without_metadata(self):
        """Test that complete multipart upload request can be created without metadata."""
        parts = [UploadPartResponse(etag="etag1", part_number=1)]

        request = AWSCompleteMultipartUploadRequest(
            bucket="test-bucket",
            key="test-file.zip",
            upload_id="test-upload-id-123",
            parts=parts,
        )

        assert request.metadata is None

    def test_complete_multipart_upload_request_empty_parts(self):
        """Test that complete multipart upload request cannot have empty parts list."""
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            AWSCompleteMultipartUploadRequest(
                bucket="test-bucket",
                key="test-file.zip",
                upload_id="test-upload-id-123",
                parts=[],
            )

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
    def test_complete_multipart_upload_request_validation_errors(
        self, field, invalid_value, expected_error
    ):
        """Test that validation errors are raised for invalid values."""
        parts = [UploadPartResponse(etag="etag1", part_number=1)]
        valid_data = {
            "bucket": "test-bucket",
            "key": "test-file.zip",
            "upload_id": "test-upload-id-123",
            "parts": parts,
        }
        valid_data[field] = invalid_value

        with pytest.raises(ValueError, match=expected_error):
            AWSCompleteMultipartUploadRequest(**valid_data)

    def test_complete_multipart_upload_request_whitespace_trimming(self):
        """Test that whitespace is trimmed from string fields."""
        parts = [UploadPartResponse(etag="etag1", part_number=1)]

        request = AWSCompleteMultipartUploadRequest(
            bucket="  test-bucket  ",
            key="  test-file.zip  ",
            upload_id="  test-upload-id-123  ",
            parts=parts,
        )

        assert request.bucket == "test-bucket"
        assert request.key == "test-file.zip"
        assert request.upload_id == "test-upload-id-123"


class TestAWSSchemasConfig:
    """Test cases for AWS schema configuration."""

    @pytest.mark.parametrize(
        "schema_class",
        [
            AWSUploadPartRequest,
            AWSCreateMultipartUploadRequest,
            AWSAbortMultipartUploadRequest,
            AWSGeneratePresignedUrlRequest,
            AWSCompleteMultipartUploadRequest,
        ],
    )
    def test_schema_config_extra_forbid(self, schema_class):
        """Test that all AWS schemas forbid extra fields."""
        # This should work with valid data
        if schema_class == AWSUploadPartRequest:
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
                upload_id="test-upload-id-123",
                part_number=1,
                body=b"x" * AWS_MIN_PART_SIZE,
            )
        elif schema_class == AWSCreateMultipartUploadRequest:
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
                content_type="application/zip",
            )
        elif schema_class == AWSAbortMultipartUploadRequest:
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
                upload_id="test-upload-id-123",
            )
        elif schema_class == AWSGeneratePresignedUrlRequest:
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
            )
        elif schema_class == AWSCompleteMultipartUploadRequest:
            parts = [UploadPartResponse(etag="etag1", part_number=1)]
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
                upload_id="test-upload-id-123",
                parts=parts,
            )

        # This should fail with extra fields
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            # Try to add an extra field
            instance_dict = instance.model_dump()
            instance_dict["extra_field"] = "should_fail"
            schema_class(**instance_dict)

    @pytest.mark.parametrize(
        "schema_class",
        [
            AWSUploadPartRequest,
            AWSCreateMultipartUploadRequest,
            AWSAbortMultipartUploadRequest,
            AWSGeneratePresignedUrlRequest,
            AWSCompleteMultipartUploadRequest,
        ],
    )
    def test_schema_config_case_insensitive(self, schema_class):
        """Test that all AWS schemas are case insensitive."""
        # This should work with valid data
        if schema_class == AWSUploadPartRequest:
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
                upload_id="test-upload-id-123",
                part_number=1,
                body=b"x" * AWS_MIN_PART_SIZE,
            )
        elif schema_class == AWSCreateMultipartUploadRequest:
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
                content_type="application/zip",
            )
        elif schema_class == AWSAbortMultipartUploadRequest:
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
                upload_id="test-upload-id-123",
            )
        elif schema_class == AWSGeneratePresignedUrlRequest:
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
            )
        elif schema_class == AWSCompleteMultipartUploadRequest:
            parts = [UploadPartResponse(etag="etag1", part_number=1)]
            instance = schema_class(
                bucket="test-bucket",
                key="test-file.zip",
                upload_id="test-upload-id-123",
                parts=parts,
            )

        # Verify the instance was created successfully
        assert instance is not None

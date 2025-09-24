"""Tests for streaming storage schemas."""

import pytest
from pydantic import ValidationError

from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    AttachmentProcessingInfo,
    MultipartUploadResponse,
    SmartOpenStreamingStorageConfig,
    StorageUploadConfig,
    StreamingBufferConfig,
    UploadPartResponse,
)


class TestAttachmentInfo:
    """Test AttachmentInfo schema."""

    def test_valid_attachment_info(self):
        """Test valid attachment info creation."""
        attachment = AttachmentInfo(
            storage_key="test/path/file.pdf",
            file_name="test.pdf",
            content_type="application/pdf",
            size=1024,
        )
        assert attachment.storage_key == "test/path/file.pdf"
        assert attachment.file_name == "test.pdf"
        assert attachment.content_type == "application/pdf"
        assert attachment.size == 1024

    def test_attachment_info_without_file_name(self):
        """Test attachment info without file_name."""
        attachment = AttachmentInfo(
            storage_key="test/path/file.pdf",
            content_type="application/pdf",
            size=1024,
        )
        assert attachment.file_name is None

    def test_attachment_info_empty_storage_key_validation(self):
        """Test validation of empty storage_key."""
        with pytest.raises(
            ValidationError, match="storage_key cannot be empty or whitespace"
        ):
            AttachmentInfo(
                storage_key="",
                file_name="test.pdf",
                content_type="application/pdf",
                size=1024,
            )

    def test_attachment_info_whitespace_storage_key_validation(self):
        """Test validation of whitespace-only storage_key."""
        with pytest.raises(
            ValidationError, match="storage_key cannot be empty or whitespace"
        ):
            AttachmentInfo(
                storage_key="   ",
                file_name="test.pdf",
                content_type="application/pdf",
                size=1024,
            )

    def test_attachment_info_empty_file_name_validation(self):
        """Test validation of empty file_name."""
        with pytest.raises(
            ValidationError, match="file_name cannot be empty or whitespace if provided"
        ):
            AttachmentInfo(
                storage_key="test/path/file.pdf",
                file_name="",
                content_type="application/pdf",
                size=1024,
            )

    def test_attachment_info_whitespace_file_name_validation(self):
        """Test validation of whitespace-only file_name."""
        with pytest.raises(
            ValidationError, match="file_name cannot be empty or whitespace if provided"
        ):
            AttachmentInfo(
                storage_key="test/path/file.pdf",
                file_name="   ",
                content_type="application/pdf",
                size=1024,
            )

    def test_attachment_info_strips_storage_key(self):
        """Test that storage_key is stripped of whitespace."""
        attachment = AttachmentInfo(
            storage_key="  test/path/file.pdf  ",
            file_name="test.pdf",
            content_type="application/pdf",
            size=1024,
        )
        assert attachment.storage_key == "test/path/file.pdf"

    def test_attachment_info_strips_file_name(self):
        """Test that file_name is stripped of whitespace."""
        attachment = AttachmentInfo(
            storage_key="test/path/file.pdf",
            file_name="  test.pdf  ",
            content_type="application/pdf",
            size=1024,
        )
        assert attachment.file_name == "test.pdf"


class TestStorageUploadConfig:
    """Test StorageUploadConfig schema."""

    def test_valid_storage_upload_config(self):
        """Test valid storage upload config creation."""
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-file.zip",
            resp_format="csv",
            max_workers=10,
        )
        assert config.bucket_name == "test-bucket"
        assert config.file_key == "test-file.zip"
        assert config.resp_format == "csv"
        assert config.max_workers == 10

    def test_storage_upload_config_default_max_workers(self):
        """Test default max_workers value."""
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-file.zip",
            resp_format="csv",
        )
        assert config.max_workers == 5

    def test_storage_upload_config_empty_bucket_name_validation(self):
        """Test validation of empty bucket_name."""
        with pytest.raises(
            ValidationError, match="Storage identifier cannot be empty or whitespace"
        ):
            StorageUploadConfig(
                bucket_name="",
                file_key="test-file.zip",
                resp_format="csv",
            )

    def test_storage_upload_config_empty_file_key_validation(self):
        """Test validation of empty file_key."""
        with pytest.raises(
            ValidationError, match="Storage identifier cannot be empty or whitespace"
        ):
            StorageUploadConfig(
                bucket_name="test-bucket",
                file_key="",
                resp_format="csv",
            )

    def test_storage_upload_config_whitespace_validation(self):
        """Test validation of whitespace-only identifiers."""
        with pytest.raises(
            ValidationError, match="Storage identifier cannot be empty or whitespace"
        ):
            StorageUploadConfig(
                bucket_name="   ",
                file_key="test-file.zip",
                resp_format="csv",
            )

    def test_storage_upload_config_strips_identifiers(self):
        """Test that identifiers are stripped of whitespace."""
        config = StorageUploadConfig(
            bucket_name="  test-bucket  ",
            file_key="  test-file.zip  ",
            resp_format="csv",
        )
        assert config.bucket_name == "test-bucket"
        assert config.file_key == "test-file.zip"

    def test_storage_upload_config_max_workers_validation(self):
        """Test max_workers validation."""
        # Test minimum value
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1"
        ):
            StorageUploadConfig(
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="csv",
                max_workers=0,
            )

        # Test maximum value
        with pytest.raises(
            ValidationError, match="Input should be less than or equal to 20"
        ):
            StorageUploadConfig(
                bucket_name="test-bucket",
                file_key="test-file.zip",
                resp_format="csv",
                max_workers=21,
            )


class TestStreamingBufferConfig:
    """Test StreamingBufferConfig schema."""

    def test_valid_streaming_buffer_config(self):
        """Test valid streaming buffer config creation."""
        config = StreamingBufferConfig(
            zip_buffer_threshold=10 * 1024 * 1024,  # 10MB
            stream_buffer_threshold=2 * 1024 * 1024,  # 2MB
            chunk_size_threshold=2 * 1024 * 1024,  # 2MB
        )
        assert config.zip_buffer_threshold == 10 * 1024 * 1024
        assert config.stream_buffer_threshold == 2 * 1024 * 1024
        assert config.chunk_size_threshold == 2 * 1024 * 1024

    def test_streaming_buffer_config_defaults(self):
        """Test default values."""
        config = StreamingBufferConfig()
        assert config.zip_buffer_threshold == 5 * 1024 * 1024  # 5MB
        assert config.stream_buffer_threshold == 1024 * 1024  # 1MB
        assert config.chunk_size_threshold == 1024 * 1024  # 1MB
        assert config.fail_fast_on_attachment_errors is True
        assert config.include_error_details is True

    def test_streaming_buffer_config_min_validation(self):
        """Test minimum threshold validation."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1048576"
        ):
            StreamingBufferConfig(zip_buffer_threshold=1024 * 1024 - 1)

    def test_streaming_buffer_config_error_handling_options(self):
        """Test error handling configuration options."""
        config = StreamingBufferConfig(
            fail_fast_on_attachment_errors=True,
            include_error_details=False,
        )
        assert config.fail_fast_on_attachment_errors is True
        assert config.include_error_details is False


class TestSmartOpenStreamingStorageConfig:
    """Test SmartOpenStreamingStorageConfig schema."""

    def test_valid_config(self):
        """Test valid configuration creation."""
        config = SmartOpenStreamingStorageConfig(chunk_size=1024 * 1024)  # 1MB
        assert config.chunk_size == 1024 * 1024

    def test_default_config(self):
        """Test default configuration values."""
        config = SmartOpenStreamingStorageConfig()
        assert config.chunk_size == 5 * 1024 * 1024  # DEFAULT_CHUNK_SIZE

    def test_minimum_chunk_size(self):
        """Test minimum chunk size validation."""
        config = SmartOpenStreamingStorageConfig(chunk_size=1024)  # 1KB
        assert config.chunk_size == 1024

    def test_maximum_chunk_size(self):
        """Test maximum chunk size validation."""
        config = SmartOpenStreamingStorageConfig(
            chunk_size=2 * 1024 * 1024 * 1024
        )  # 2GB
        assert config.chunk_size == 2 * 1024 * 1024 * 1024

    def test_invalid_chunk_size_too_small(self):
        """Test validation error for chunk size too small."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1024"
        ):
            SmartOpenStreamingStorageConfig(chunk_size=512)

    def test_invalid_chunk_size_too_large(self):
        """Test validation error for chunk size too large."""
        with pytest.raises(
            ValidationError, match="Input should be less than or equal to"
        ):
            SmartOpenStreamingStorageConfig(chunk_size=3 * 1024 * 1024 * 1024)  # 3GB

    def test_boundary_values(self):
        """Test that boundary values are accepted."""
        # Test minimum valid value
        config_min = SmartOpenStreamingStorageConfig(chunk_size=1024)  # 1KB
        assert config_min.chunk_size == 1024

        # Test maximum valid value
        config_max = SmartOpenStreamingStorageConfig(
            chunk_size=2 * 1024 * 1024 * 1024
        )  # 2GB
        assert config_max.chunk_size == 2 * 1024 * 1024 * 1024


class TestAttachmentProcessingInfo:
    """Test AttachmentProcessingInfo schema."""

    def test_valid_attachment_processing_info(self):
        """Test valid attachment processing info creation."""
        attachment = AttachmentInfo(
            storage_key="test/path/file.pdf",
            file_name="test.pdf",
            content_type="application/pdf",
            size=1024,
        )

        processing_info = AttachmentProcessingInfo(
            attachment=attachment,
            base_path="/attachments/",
            item={"id": 1, "name": "test"},
        )
        assert processing_info.attachment == attachment
        assert processing_info.base_path == "/attachments/"
        assert processing_info.item == {"id": 1, "name": "test"}

    def test_attachment_processing_info_empty_base_path_validation(self):
        """Test validation of empty base_path."""
        attachment = AttachmentInfo(
            storage_key="test/path/file.pdf",
            file_name="test.pdf",
            content_type="application/pdf",
            size=1024,
        )

        with pytest.raises(
            ValidationError, match="base_path cannot be empty or whitespace"
        ):
            AttachmentProcessingInfo(
                attachment=attachment,
                base_path="",
                item={"id": 1, "name": "test"},
            )

    def test_attachment_processing_info_strips_base_path(self):
        """Test that base_path is stripped of whitespace."""
        attachment = AttachmentInfo(
            storage_key="test/path/file.pdf",
            file_name="test.pdf",
            content_type="application/pdf",
            size=1024,
        )

        processing_info = AttachmentProcessingInfo(
            attachment=attachment,
            base_path="  /attachments/  ",
            item={"id": 1, "name": "test"},
        )
        assert processing_info.base_path == "/attachments/"


class TestMultipartUploadResponse:
    """Test MultipartUploadResponse schema."""

    def test_valid_multipart_upload_response(self):
        """Test valid multipart upload response creation."""
        response = MultipartUploadResponse(
            upload_id="test-upload-123",
            metadata={"storage_type": "s3", "method": "streaming"},
        )
        assert response.upload_id == "test-upload-123"
        assert response.metadata == {"storage_type": "s3", "method": "streaming"}

    def test_multipart_upload_response_without_metadata(self):
        """Test multipart upload response without metadata."""
        response = MultipartUploadResponse(upload_id="test-upload-123")
        assert response.upload_id == "test-upload-123"
        assert response.metadata is None

    def test_multipart_upload_response_empty_upload_id_validation(self):
        """Test validation of empty upload_id."""
        with pytest.raises(
            ValidationError, match="Upload ID cannot be empty or whitespace"
        ):
            MultipartUploadResponse(upload_id="")

    def test_multipart_upload_response_whitespace_upload_id_validation(self):
        """Test validation of whitespace-only upload_id."""
        with pytest.raises(
            ValidationError, match="Upload ID cannot be empty or whitespace"
        ):
            MultipartUploadResponse(upload_id="   ")

    def test_multipart_upload_response_non_string_upload_id_validation(self):
        """Test validation of non-string upload_id."""
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            MultipartUploadResponse(upload_id=123)

    def test_multipart_upload_response_strips_upload_id(self):
        """Test that upload_id is stripped of whitespace."""
        response = MultipartUploadResponse(upload_id="  test-upload-123  ")
        assert response.upload_id == "test-upload-123"

    def test_multipart_upload_response_is_valid_upload_id(self):
        """Test is_valid_upload_id method."""
        response = MultipartUploadResponse(upload_id="test-upload-123")
        assert response.is_valid_upload_id() is True

        # Test with invalid upload ID
        response.upload_id = ""
        assert response.is_valid_upload_id() is False


class TestUploadPartResponse:
    """Test UploadPartResponse schema."""

    def test_valid_upload_part_response(self):
        """Test valid upload part response creation."""
        response = UploadPartResponse(
            part_number=1,
            etag="test-etag-123",
            metadata={"storage_type": "s3", "method": "streaming"},
        )
        assert response.part_number == 1
        assert response.etag == "test-etag-123"
        assert response.metadata == {"storage_type": "s3", "method": "streaming"}

    def test_upload_part_response_without_metadata(self):
        """Test upload part response without metadata."""
        response = UploadPartResponse(part_number=1, etag="test-etag-123")
        assert response.part_number == 1
        assert response.etag == "test-etag-123"
        assert response.metadata is None

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    AttachmentProcessingInfo,
    PackageSplitConfig,
    StorageUploadConfig,
    StreamingBufferConfig,
)


class TestStreamingStorageSchemas:
    """Test cases for the new streaming storage Pydantic models."""

    def test_attachment_info_validation(self):
        """Test AttachmentInfo model validation."""
        # Valid attachment
        valid_attachment = AttachmentInfo(
            storage_key="test/path/file.pdf",
            file_name="document.pdf",
            size=1024,
            content_type="application/pdf",
        )
        assert valid_attachment.storage_key == "test/path/file.pdf"
        assert valid_attachment.file_name == "document.pdf"
        assert valid_attachment.size == 1024

        # Test storage_key validation
        with pytest.raises(
            ValidationError, match="storage_key cannot be empty or whitespace"
        ):
            AttachmentInfo(storage_key="", file_name="test.pdf")

        with pytest.raises(
            ValidationError, match="storage_key cannot be empty or whitespace"
        ):
            AttachmentInfo(storage_key="   ", file_name="test.pdf")

    def test_storage_upload_config_validation(self):
        """Test StorageUploadConfig model validation."""
        # Valid config
        valid_config = StorageUploadConfig(
            bucket_name="test-bucket", file_key="test/file.zip", resp_format="csv"
        )
        assert valid_config.bucket_name == "test-bucket"
        assert valid_config.max_workers == 5  # default value

        # Test validation - empty string triggers Pydantic's min_length validation
        with pytest.raises(
            ValidationError, match="Storage identifier cannot be empty or whitespace"
        ):
            StorageUploadConfig(
                bucket_name="", file_key="test/file.zip", resp_format="csv"
            )

        # Test validation - whitespace passes min_length but fails custom validator
        with pytest.raises(
            ValidationError, match="Storage identifier cannot be empty or whitespace"
        ):
            StorageUploadConfig(
                bucket_name="test-bucket", file_key="   ", resp_format="csv"
            )

    def test_package_split_config_validation(self):
        """Test PackageSplitConfig model validation."""
        # Valid config
        valid_config = PackageSplitConfig(max_attachments=50)
        assert valid_config.max_attachments == 50

        # Test validation
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1"
        ):
            PackageSplitConfig(max_attachments=0)

    def test_streaming_buffer_config_defaults(self):
        """Test StreamingBufferConfig default values."""
        config = StreamingBufferConfig()
        assert config.zip_buffer_threshold == 5 * 1024 * 1024  # 5MB
        assert config.stream_buffer_threshold == 1024 * 1024  # 512KB
        assert config.chunk_size_threshold == 1024 * 1024  # 1MB

    def test_attachment_processing_info_validation(self):
        """Test AttachmentProcessingInfo model validation."""
        attachment = AttachmentInfo(storage_key="test/file.pdf", file_name="test.pdf")
        item = {"id": 1, "name": "test"}

        # Valid processing info
        processing_info = AttachmentProcessingInfo(
            attachment=attachment, base_path="test/path", item=item
        )
        assert processing_info.attachment == attachment
        assert processing_info.base_path == "test/path"
        assert processing_info.item == item

        # Test base_path validation
        with pytest.raises(
            ValidationError, match="base_path cannot be empty or whitespace"
        ):
            AttachmentProcessingInfo(attachment=attachment, base_path="", item=item)

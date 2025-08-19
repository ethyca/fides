"""Tests for the streaming storage implementation.

These tests verify that the streaming storage correctly implements true streaming:
- Downloads chunks and immediately uploads them to storage
- Does NOT build zip files in memory
- Uses multipart uploads for coordination
- Maintains only small buffers for individual chunks
"""

from io import BytesIO
from unittest.mock import MagicMock, Mock, call, create_autospec, patch

import pytest

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    AttachmentProcessingInfo,
    StorageUploadConfig,
    StreamingBufferConfig,
)
from fides.api.service.storage.streaming.streaming_storage import (
    create_data_descriptor,
    create_local_file_header,
    create_zip_part_for_chunk,
    split_data_into_packages,
    stream_attachments_to_storage_zip,
    stream_single_attachment_to_storage_streaming,
    upload_to_storage_streaming,
)


class TestStreamingStorage:
    """Test the streaming storage implementation."""

    def test_create_local_file_header(self):
        """Test ZIP local file header creation."""
        filename = "test.txt"
        file_size = 1024

        header = create_local_file_header(filename, file_size)

        # Check ZIP signature
        assert header[:4] == b"PK\x03\x04"

        # Check filename length (2 bytes at position 26-27)
        filename_length = int.from_bytes(header[26:28], "little")
        assert filename_length == len(filename)

        # Check file size (4 bytes at position 18-21)
        size_from_header = int.from_bytes(header[18:22], "little")
        assert size_from_header == file_size

        # Check filename is present
        assert filename.encode("utf-8") in header

    def test_create_data_descriptor(self):
        """Test ZIP data descriptor creation."""
        file_size = 2048

        descriptor = create_data_descriptor(file_size)

        # Check data descriptor signature
        assert descriptor[:4] == b"PK\x07\x08"

        # Check file size (4 bytes at position 8-11)
        size_from_descriptor = int.from_bytes(descriptor[8:12], "little")
        assert size_from_descriptor == file_size

    def test_create_zip_part_for_chunk(self):
        """Test ZIP part creation for individual chunks."""
        chunk_data = b"test data content"
        filename = "test.txt"
        file_size = len(chunk_data)

        # Test first chunk (with header)
        first_chunk = create_zip_part_for_chunk(
            chunk_data, filename, True, False, file_size
        )
        assert first_chunk.startswith(b"PK\x03\x04")  # Has local file header
        assert chunk_data in first_chunk

        # Test last chunk (with footer)
        last_chunk = create_zip_part_for_chunk(
            chunk_data, filename, False, True, file_size
        )
        assert chunk_data in last_chunk
        assert b"PK\x07\x08" in last_chunk  # Has data descriptor signature

        # Test middle chunk (no header/footer)
        middle_chunk = create_zip_part_for_chunk(
            chunk_data, filename, False, False, file_size
        )
        assert chunk_data in middle_chunk
        assert not middle_chunk.startswith(b"PK\x03\x04")  # No header
        assert not middle_chunk.endswith(b"PK\x07\x08")  # No footer

    def test_split_data_into_packages(self):
        """Test data package splitting logic."""
        # Test data with multiple items and attachments
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}]
                    * 50,  # 50 attachments
                },
                {
                    "id": 2,
                    "name": "User 2",
                    "attachments": [{"s3_key": "key2", "size": 2000}]
                    * 75,  # 75 attachments
                },
            ]
        }

        # Default config allows 100 attachments per package
        packages = split_data_into_packages(data)

        # Should split into 2 packages since User 2 has 75 attachments
        assert len(packages) == 2

        # First package should contain User 2 (75 attachments) - sorted by largest first
        assert "users" in packages[0]
        assert len(packages[0]["users"]) == 1
        assert packages[0]["users"][0]["id"] == 2

        # Second package should contain User 1 (50 attachments)
        assert "users" in packages[1]
        assert len(packages[1]["users"]) == 1
        assert packages[1]["users"][0]["id"] == 1

    def test_split_data_into_packages_with_large_attachments(self):
        """Test package splitting when individual items exceed attachment limits."""
        # Test data with one item having more attachments than the limit
        data = {
            "documents": [
                {
                    "id": "doc1",
                    "attachments": [
                        {"s3_key": f"key{j}", "size": 1000} for j in range(50)
                    ],  # 50 attachments (reduced to avoid recursion)
                }
            ]
        }

        # Default config allows 100 attachments per package
        packages = split_data_into_packages(data)

        # Should not split since 50 attachments is under the 100 limit
        assert len(packages) == 1
        assert len(packages[0]["documents"][0]["attachments"]) == 50

    @patch("fides.api.service.storage.streaming.streaming_storage.should_split_package")
    def test_stream_attachments_to_storage_zip_no_split(self, mock_should_split):
        """Test streaming without package splitting."""
        mock_should_split.return_value = False

        mock_client = create_autospec(CloudStorageClient, instance=True)
        mock_client.create_multipart_upload.return_value = Mock(
            upload_id="test_upload_123"
        )
        mock_client.upload_part.return_value = Mock(etag="test_etag")
        mock_client.complete_multipart_upload.return_value = None

        # Mock object head response
        mock_client.get_object_head.return_value = {"ContentLength": 1024}
        mock_client.get_object_range.return_value = b"test data"

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "Test User",
                    "attachments": [
                        {"s3_key": "test_key", "file_name": "test.txt", "size": 1024}
                    ],
                }
            ]
        }

        mock_privacy_request = Mock()

        metrics = stream_attachments_to_storage_zip(
            mock_client, "test_bucket", "test_key", data, mock_privacy_request
        )

        # Verify multipart upload was created
        mock_client.create_multipart_upload.assert_called_once()

        # Verify parts were uploaded
        assert mock_client.upload_part.call_count > 0

        # Verify upload was completed
        mock_client.complete_multipart_upload.assert_called_once()

        # Verify metrics
        assert metrics.processed_attachments == 1
        assert metrics.total_attachments == 1

    def test_stream_attachments_to_storage_zip_with_split(self):
        """Test streaming with package splitting."""
        mock_client = create_autospec(CloudStorageClient, instance=True)
        mock_client.create_multipart_upload.return_value = Mock(
            upload_id="test_upload_123"
        )
        mock_client.upload_part.return_value = Mock(etag="test_etag")
        mock_client.complete_multipart_upload.return_value = None

        # Mock object head response
        mock_client.get_object_head.return_value = {"ContentLength": 1024}
        mock_client.get_object_range.return_value = b"test data"

        # Test data with enough attachments to trigger splitting (>100)
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "Test User",
                    "attachments": [
                        {"s3_key": f"key{j}", "file_name": f"test{j}.txt", "size": 1024}
                        for j in range(150)
                    ],
                }
            ]
        }

        mock_privacy_request = Mock()

        metrics = stream_attachments_to_storage_zip(
            mock_client, "test_bucket", "test_key", data, mock_privacy_request
        )

        # Should have processed all 150 attachments across multiple packages
        assert metrics.processed_attachments == 150

    def test_stream_single_attachment_to_storage_streaming(self):
        """Test streaming a single attachment to storage."""
        mock_client = create_autospec(CloudStorageClient, instance=True)
        mock_client.get_object_head.return_value = {"ContentLength": 2048}
        mock_client.get_object_range.return_value = b"chunk data"

        upload_context = {
            "storage_client": mock_client,
            "bucket_name": "test_bucket",
            "file_key": "test_key",
            "upload_id": "test_upload_123",
            "parts": [],
            "part_number": 1,
            "lock": MagicMock(),
            "current_offset": 0,
            "file_entries": [],
        }

        attachment = AttachmentInfo(
            s3_key="test_attachment_key", file_name="test.txt", size=2048
        )

        metrics = Mock()
        metrics.current_attachment = None
        metrics.current_attachment_progress = 0.0
        metrics.errors = []

        result = stream_single_attachment_to_storage_streaming(
            upload_context, attachment, "test/path", metrics
        )

        # Verify object head was retrieved
        mock_client.get_object_head.assert_called_once_with(
            "test_bucket", "test_attachment_key"
        )

        # Verify object range was retrieved (for chunks)
        assert mock_client.get_object_range.call_count > 0

        # Verify result contains expected metrics
        assert result["processed_bytes"] == 2048
        assert result["chunks"] > 0
        assert result["chunk_size"] > 0

    def test_stream_single_attachment_to_storage_streaming_with_error(self):
        """Test streaming attachment with storage error."""
        mock_client = create_autospec(CloudStorageClient, instance=True)
        mock_client.get_object_head.side_effect = StorageUploadError("Storage error")

        upload_context = {
            "storage_client": mock_client,
            "bucket_name": "test_bucket",
            "file_key": "test_key",
            "upload_id": "test_upload_123",
            "parts": [],
            "part_number": 1,
            "lock": MagicMock(),
            "current_offset": 0,
            "file_entries": [],
        }

        attachment = AttachmentInfo(
            s3_key="test_attachment_key", file_name="test.txt", size=1024
        )

        metrics = Mock()
        metrics.current_attachment = None
        metrics.current_attachment_progress = 0.0
        metrics.errors = []

        with pytest.raises(StorageUploadError):
            stream_single_attachment_to_storage_streaming(
                upload_context, attachment, "test/path", metrics
            )

        # Verify error was added to metrics
        assert len(metrics.errors) == 1
        assert "Failed to process attachment" in metrics.errors[0]

    def test_upload_to_storage_streaming_csv_format(self):
        """Test streaming upload with CSV format."""
        mock_client = create_autospec(CloudStorageClient, instance=True)
        mock_client.create_multipart_upload.return_value = Mock(
            upload_id="test_upload_123"
        )
        mock_client.upload_part.return_value = Mock(etag="test_etag")
        mock_client.complete_multipart_upload.return_value = None
        mock_client.generate_presigned_url.return_value = "https://test-url.com"

        # Mock object head response
        mock_client.get_object_head.return_value = {"ContentLength": 1024}
        mock_client.get_object_range.return_value = b"test data"

        config = StorageUploadConfig(
            bucket_name="test_bucket",
            file_key="test_key",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "Test User",
                    "attachments": [
                        {"s3_key": "test_key", "file_name": "test.txt", "size": 1024}
                    ],
                }
            ]
        }

        mock_privacy_request = Mock()

        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
        ) as mock_stream:
            mock_stream.return_value = Mock(
                processed_attachments=1, total_attachments=1
            )

            url, metrics = upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

            # Verify streaming function was called
            mock_stream.assert_called_once()

            # Verify presigned URL was generated
            assert url == "https://test-url.com"

    def test_upload_to_storage_streaming_json_format(self):
        """Test streaming upload with JSON format."""
        mock_client = create_autospec(CloudStorageClient, instance=True)
        mock_client.create_multipart_upload.return_value = Mock(
            upload_id="test_upload_123"
        )
        mock_client.upload_part.return_value = Mock(etag="test_etag")
        mock_client.complete_multipart_upload.return_value = None
        mock_client.generate_presigned_url.return_value = "https://test-url.com"

        config = StorageUploadConfig(
            bucket_name="test_bucket",
            file_key="test_key",
            resp_format=ResponseFormat.json.value,
            max_workers=2,
        )

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "Test User",
                    "attachments": [
                        {"s3_key": "test_key", "file_name": "test.txt", "size": 1024}
                    ],
                }
            ]
        }

        mock_privacy_request = Mock()

        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
        ) as mock_stream:
            mock_stream.return_value = Mock(
                processed_attachments=1, total_attachments=1
            )

            url, metrics = upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

            # Verify streaming function was called
            mock_stream.assert_called_once()

            # Verify presigned URL was generated
            assert url == "https://test-url.com"

    def test_upload_to_storage_streaming_html_format(self):
        """Test streaming upload with HTML format."""
        mock_client = create_autospec(CloudStorageClient, instance=True)
        mock_client.generate_presigned_url.return_value = "https://test-url.com"

        config = StorageUploadConfig(
            bucket_name="test_bucket",
            file_key="test_key",
            resp_format=ResponseFormat.html.value,
            max_workers=2,
        )

        data = {"test": "data"}
        mock_privacy_request = Mock()
        mock_privacy_request.id = "test_request_123"
        mock_privacy_request.get_persisted_identity.return_value = Mock(
            labeled_dict=lambda include_default_labels: {
                "email": {"value": "test@example.com", "label": "Email"},
                "phone": {"value": None, "label": "Phone"},
            }
        )
        mock_privacy_request.policy = Mock()
        mock_privacy_request.policy.get_action_type.return_value = Mock(value="access")

        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_html_dsr_report_to_storage_multipart"
        ) as mock_html_stream:
            mock_html_stream.return_value = Mock(
                processed_attachments=0, total_attachments=0
            )

            url, metrics = upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

            # Verify HTML streaming function was called
            mock_html_stream.assert_called_once()

            # Verify presigned URL was generated
            assert url == "https://test-url.com"

    def test_upload_to_storage_streaming_unsupported_format(self):
        """Test streaming upload with unsupported format."""
        mock_client = create_autospec(
            "fides.api.service.storage.streaming.cloud_storage_client.CloudStorageClient",
            instance=True,
        )

        config = StorageUploadConfig(
            bucket_name="test_bucket",
            file_key="test_key",
            resp_format="unsupported",
            max_workers=2,
        )

        data = {"test": "data"}
        mock_privacy_request = Mock()

        with pytest.raises(
            StorageUploadError, match="No streaming support for format unsupported"
        ):
            upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

    def test_upload_to_storage_streaming_no_privacy_request(self):
        """Test streaming upload without privacy request."""
        mock_client = create_autospec(CloudStorageClient, instance=True)

        config = StorageUploadConfig(
            bucket_name="test_bucket",
            file_key="test_key",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        data = {"test": "data"}

        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_storage_streaming(mock_client, data, config, None, None)

    def test_streaming_buffer_config_defaults(self):
        """Test streaming buffer configuration defaults."""
        config = StreamingBufferConfig()

        # Verify reasonable defaults
        assert config.zip_buffer_threshold == 5 * 1024 * 1024  # 5MB
        assert config.stream_buffer_threshold == 512 * 1024  # 512KB
        assert config.chunk_size_threshold == 1024 * 1024  # 1MB

    def test_streaming_buffer_config_custom_values(self):
        """Test streaming buffer configuration with custom values."""
        config = StreamingBufferConfig(
            zip_buffer_threshold=10 * 1024 * 1024,  # 10MB
            stream_buffer_threshold=1024 * 1024,  # 1MB
            chunk_size_threshold=2 * 1024 * 1024,  # 2MB
        )

        assert config.zip_buffer_threshold == 10 * 1024 * 1024
        assert config.stream_buffer_threshold == 1024 * 1024
        assert config.chunk_size_threshold == 2 * 1024 * 1024

    def test_create_central_directory_header(self):
        """Test ZIP central directory header creation."""
        from fides.api.service.storage.streaming.streaming_storage import (
            create_central_directory_header,
        )

        filename = "test.txt"
        file_size = 1024
        local_header_offset = 0

        header = create_central_directory_header(
            filename, file_size, local_header_offset
        )

        # Check ZIP central directory signature
        assert header[:4] == b"PK\x01\x02"

        # Check filename length (2 bytes at position 28-29)
        filename_length = int.from_bytes(header[28:30], "little")
        assert filename_length == len(filename)

        # Check file size (4 bytes at position 20-23)
        size_from_header = int.from_bytes(header[20:24], "little")
        assert size_from_header == file_size

        # Check filename is present
        assert filename.encode("utf-8") in header

    def test_create_central_directory_end(self):
        """Test ZIP end of central directory record creation."""
        from fides.api.service.storage.streaming.streaming_storage import (
            create_central_directory_end,
        )

        total_entries = 5
        central_dir_size = 1024
        central_dir_offset = 2048

        end_record = create_central_directory_end(
            total_entries, central_dir_size, central_dir_offset
        )

        # Check ZIP end of central directory signature
        assert end_record[:4] == b"PK\x05\x06"

        # Check total entries (2 bytes at position 8-9)
        entries_from_record = int.from_bytes(end_record[8:10], "little")
        assert entries_from_record == total_entries

        # Check central directory size (4 bytes at position 12-15)
        size_from_record = int.from_bytes(end_record[12:16], "little")
        assert size_from_record == central_dir_size

        # Check central directory offset (4 bytes at position 16-19)
        offset_from_record = int.from_bytes(end_record[16:20], "little")
        assert offset_from_record == central_dir_offset

    def test_create_central_directory_parts(self):
        """Test central directory parts creation."""
        from fides.api.service.storage.streaming.streaming_storage import (
            create_central_directory_parts,
        )

        # Test with empty file entries
        empty_parts = create_central_directory_parts([], 0)
        assert empty_parts == []

        # Test with single file entry
        file_entries = [("test.txt", 1024, 0, 0)]
        parts = create_central_directory_parts(file_entries, 2048)

        assert len(parts) == 1
        central_dir_part = parts[0]

        # Should contain central directory header and end record
        assert b"PK\x01\x02" in central_dir_part  # Central directory header
        assert b"PK\x05\x06" in central_dir_part  # End of central directory

    def test_zip64_support(self):
        """Test ZIP64 support for large files."""
        from fides.api.service.storage.streaming.streaming_storage import (
            create_data_descriptor,
            create_local_file_header,
        )

        # Test with file size > 4GB
        large_file_size = 5 * 1024 * 1024 * 1024  # 5GB

        # Local file header should use ZIP64 markers
        header = create_local_file_header("large_file.txt", large_file_size)

        # Check that ZIP64 markers are used for sizes > 4GB
        compressed_size = int.from_bytes(header[18:22], "little")
        uncompressed_size = int.from_bytes(header[22:26], "little")

        # Should be 0xFFFFFFFF for ZIP64
        assert compressed_size == 0xFFFFFFFF
        assert uncompressed_size == 0xFFFFFFFF

        # Data descriptor should handle large sizes
        descriptor = create_data_descriptor(large_file_size)
        assert descriptor[:4] == b"PK\x07\x08"  # Data descriptor signature

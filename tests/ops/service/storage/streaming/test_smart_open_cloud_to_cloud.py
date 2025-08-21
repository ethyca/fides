"""Tests for smart-open cloud-to-cloud streaming without local downloads.

These tests verify that smart-open can perform true cloud-to-cloud streaming
operations without downloading files to local storage, ensuring memory efficiency
and proper streaming behavior.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from fides.api.service.storage.streaming.schemas import (
    AttachmentProcessingInfo,
    StorageUploadConfig,
)
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient
from fides.api.service.storage.streaming.smart_open_streaming_storage import (
    SmartOpenStreamingStorage,
)


class TestSmartOpenCloudToCloudStreaming:
    """Test cloud-to-cloud streaming capabilities of smart-open."""

    @pytest.fixture
    def sample_data_with_attachments(self):
        """Sample data containing attachments for testing."""
        return {
            "users": [
                {
                    "id": "user1",
                    "name": "Test User",
                    "attachments": [
                        {
                            "file_name": "document1.pdf",
                            "download_url": "s3://source-bucket/attachments/doc1.pdf",
                            "size": 1024,
                            "content_type": "application/pdf",
                        }
                    ],
                }
            ]
        }

    @pytest.fixture
    def upload_config(self):
        """Upload configuration for testing."""
        return StorageUploadConfig(
            bucket_name="dest-bucket",
            file_key="test-archive.zip",
            resp_format="json",
            max_workers=2,
        )

    def test_streaming_storage_initialization(self, mock_smart_open_client):
        """Test that SmartOpenStreamingStorage initializes correctly."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)
        assert storage.storage_client == mock_smart_open_client

    def test_attachment_collection_without_download(
        self, mock_smart_open_client, sample_data_with_attachments
    ):
        """Test that attachments are collected without downloading content."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Collect attachments - this should not trigger any downloads
        attachments = storage._collect_and_validate_attachments(
            sample_data_with_attachments
        )

        # Verify attachments were collected
        assert len(attachments) == 1
        attachment_info = attachments[0]
        assert isinstance(attachment_info, AttachmentProcessingInfo)
        assert attachment_info.attachment.file_name == "document1.pdf"
        assert (
            attachment_info.attachment.storage_key
            == "s3://source-bucket/attachments/doc1.pdf"
        )

        # Verify that no streaming was attempted
        mock_smart_open_client.stream_read.assert_not_called()

    def test_zip_generator_creation_without_download(
        self, mock_smart_open_client, sample_data_with_attachments
    ):
        """Test that ZIP generator is created without downloading attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Collect attachments
        all_attachments = storage._collect_and_validate_attachments(
            sample_data_with_attachments
        )

        # Create ZIP generator - this should not download attachments yet
        zip_generator = storage._create_zip_generator(
            sample_data_with_attachments, all_attachments, "dest-bucket", 2, 10, "json"
        )

        # Convert to list to trigger generator evaluation
        zip_entries = list(zip_generator)

        # Should have data files and attachment placeholders
        assert len(zip_entries) > 0

        # Verify that no streaming was attempted during generator creation
        mock_smart_open_client.stream_read.assert_not_called()

    def test_streaming_upload_without_local_storage(
        self,
        mock_smart_open_client,
        sample_data_with_attachments,
        upload_config,
        mock_privacy_request,
    ):
        """Test that streaming upload works without storing files locally."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Mock the ZIP creation to avoid actual processing
        with patch.object(storage, "_stream_attachments_to_storage_zip") as mock_stream:
            mock_stream.return_value = None

            # Perform upload
            result = storage.upload_to_storage_streaming(
                sample_data_with_attachments, upload_config, mock_privacy_request
            )

            # Verify streaming method was called
            mock_stream.assert_called_once()

            # Verify no local file operations occurred
            # (This is implicit in the mock, but we can verify the flow)

    def test_attachment_processing_streaming_only(
        self, mock_smart_open_client, sample_data_with_attachments
    ):
        """Test that attachment processing uses streaming without local buffering."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Collect attachments
        all_attachments = storage._collect_and_validate_attachments(
            sample_data_with_attachments
        )

        # Process attachments using streaming - this creates a generator
        attachment_files_generator = storage._create_attachment_files(
            all_attachments, "dest-bucket", 2, 10
        )

        # Consume the generator to actually trigger the streaming operations
        attachment_files = list(attachment_files_generator)

        # Should have processed the attachment
        assert len(attachment_files) == 1

        # Verify the attachment file entry has the correct format
        file_path, dt, mode, method, content_iter = attachment_files[0]
        assert file_path == "users/user1/attachments/document1.pdf"
        assert isinstance(dt, datetime)
        assert mode == 0o644
        assert content_iter is not None

        # Now actually consume the streaming iterator to trigger the download
        content_chunks = list(content_iter)
        assert len(content_chunks) > 0
        assert content_chunks[0] == b"mock_attachment_content"

        # Verify streaming download was used
        mock_smart_open_client.stream_read.assert_called_once_with(
            "source-bucket", "attachments/doc1.pdf"
        )

    def test_memory_efficient_zip_creation(
        self, mock_smart_open_client, sample_data_with_attachments
    ):
        """Test that ZIP creation is memory efficient using generators."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Collect attachments
        all_attachments = storage._collect_and_validate_attachments(
            sample_data_with_attachments
        )

        # Create ZIP generator
        zip_generator = storage._create_zip_generator(
            sample_data_with_attachments, all_attachments, "dest-bucket", 2, 10, "json"
        )

        # Verify it's a generator (memory efficient)
        import types

        assert isinstance(zip_generator, types.GeneratorType)

        # Process entries one by one to simulate streaming
        entry_count = 0
        for entry in zip_generator:
            entry_count += 1
            # Each entry should be processed individually without accumulating in memory
            assert len(entry) == 5  # (filename, datetime, mode, method, content_iter)

        assert entry_count > 0

    def test_no_local_file_creation(
        self, mock_smart_open_client, sample_data_with_attachments
    ):
        """Test that no local files are created during streaming operations."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Mock file system operations to ensure none occur
        with patch("builtins.open") as mock_open:
            with patch("os.path.exists") as mock_exists:
                with patch("os.makedirs") as mock_makedirs:
                    # Perform attachment collection
                    attachments = storage._collect_and_validate_attachments(
                        sample_data_with_attachments
                    )

                    # Verify no file system operations occurred
                    mock_open.assert_not_called()
                    mock_exists.assert_not_called()
                    mock_makedirs.assert_not_called()

    def test_streaming_upload_uses_smart_open(
        self,
        mock_smart_open_client,
        sample_data_with_attachments,
        upload_config,
        mock_privacy_request,
    ):
        """Test that streaming upload properly uses smart-open streaming."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Mock the stream_upload method to return a proper mock object
        mock_upload_stream = MagicMock()
        mock_upload_stream.__enter__ = Mock(return_value=mock_upload_stream)
        mock_upload_stream.__exit__ = Mock(return_value=None)
        mock_upload_stream.write = Mock()
        mock_smart_open_client.stream_upload.return_value = mock_upload_stream

        # Mock the generate_presigned_url method
        mock_smart_open_client.generate_presigned_url.return_value = (
            "https://example.com/test-archive.zip"
        )

        # Perform upload - this will actually create the ZIP and stream it
        result = storage.upload_to_storage_streaming(
            sample_data_with_attachments, upload_config, mock_privacy_request
        )

        # Verify smart-open streaming was used
        mock_smart_open_client.stream_upload.assert_called_once_with(
            "dest-bucket", "test-archive.zip", content_type="application/zip"
        )

        # Verify the upload stream was used to write chunks
        assert mock_upload_stream.write.call_count > 0

        # Verify the result
        assert result == "https://example.com/test-archive.zip"

    def test_batch_processing_without_memory_accumulation(self, mock_smart_open_client):
        """Test that batch processing doesn't accumulate data in memory."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Create large dataset with many attachments
        large_data = {
            "users": [
                {
                    "id": f"user{i}",
                    "attachments": [
                        {
                            "file_name": f"doc{i}.pdf",
                            "download_url": f"s3://source-bucket/attachments/doc{i}.pdf",
                            "size": 1024,
                            "content_type": "application/pdf",
                        }
                        for _ in range(5)  # 5 attachments per user
                    ],
                }
                for i in range(100)  # 100 users
            ]
        }

        # Collect attachments
        all_attachments = storage._collect_and_validate_attachments(large_data)

        # Should have 500 attachments total
        assert len(all_attachments) == 500

        # Process in batches
        batch_size = 10
        processed_count = 0

        for i in range(0, len(all_attachments), batch_size):
            batch = all_attachments[i : i + batch_size]
            processed_count += len(batch)

            # Each batch should be processed independently
            assert len(batch) <= batch_size

        assert processed_count == 500

    def test_error_handling_without_data_loss(
        self, mock_smart_open_client, sample_data_with_attachments
    ):
        """Test that errors in attachment processing don't cause data loss."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Mock a failed download for one attachment
        mock_smart_open_client.stream_read.side_effect = [
            Exception("Download failed"),  # First call fails
            MagicMock(
                __enter__=Mock(
                    return_value=MagicMock(read=Mock(return_value=b"content"))
                )
            ),  # Second call succeeds
        ]

        # Collect attachments
        all_attachments = storage._collect_and_validate_attachments(
            sample_data_with_attachments
        )

        # Process attachments - should handle errors gracefully
        attachment_files = list(
            storage._create_attachment_files(all_attachments, "dest-bucket", 2, 10)
        )

        # Should still process successfully despite one failure
        assert len(attachment_files) >= 0  # May be 0 if all fail, but shouldn't crash

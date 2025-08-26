"""Tests for the DSR storage streaming functionality."""

import zipfile
from io import BytesIO
from unittest.mock import Mock

import pytest

from fides.api.service.storage.streaming.dsr_storage import (
    create_dsr_report_files_generator,
    stream_dsr_buffer_to_storage,
)
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient


@pytest.fixture
def sample_dsr_data():
    """Create sample DSR data for testing."""
    return {
        "dataset:users": [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
            }
        ],
        "attachments": [
            {
                "file_name": "test_document.pdf",
                "download_url": "https://example.com/test.pdf",
                "file_size": 1024,
            }
        ],
    }


class TestStreamDsrBufferToStorage:
    """Test cases for stream_dsr_buffer_to_storage function."""

    def test_successful_upload_smart_open_streaming(
        self,
        mock_smart_open_client_s3,
    ):
        """Test successful upload using smart-open streaming."""
        # Create a test buffer with content
        content = "This is a test HTML report content"
        test_buffer = BytesIO(content.encode("utf-8"))

        # Mock the streaming upload
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client_s3.stream_upload.return_value = mock_stream

        result = stream_dsr_buffer_to_storage(
            storage_client=mock_smart_open_client_s3,
            bucket_name="test-bucket",
            file_key="test-report.html",
            dsr_buffer=test_buffer,
        )

        # Verify streaming upload was used
        mock_smart_open_client_s3.stream_upload.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            content_type="application/zip",
        )

        # Verify content was written
        mock_stream.write.assert_called_once_with(content.encode("utf-8"))

    def test_successful_upload_with_large_content(
        self,
        mock_smart_open_client_s3,
    ):
        """Test successful upload with large content using smart-open streaming."""
        # Create a test buffer with large content
        large_content = "x" * (1024 * 1024)  # 1MB content
        test_buffer = BytesIO(large_content.encode("utf-8"))

        # Mock the streaming upload
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client_s3.stream_upload.return_value = mock_stream

        stream_dsr_buffer_to_storage(
            storage_client=mock_smart_open_client_s3,
            bucket_name="test-bucket",
            file_key="test-report.html",
            dsr_buffer=test_buffer,
        )

        # Verify streaming upload was used regardless of content size
        mock_smart_open_client_s3.stream_upload.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            content_type="application/zip",
        )

        # Verify content was written
        mock_stream.write.assert_called_once_with(large_content.encode("utf-8"))

    def test_upload_failure_handling(
        self,
        mock_smart_open_client_s3,
    ):
        """Test upload failure handling."""
        # Create a test buffer with content
        content = "Test content"
        test_buffer = BytesIO(content.encode("utf-8"))

        # Mock the streaming upload to fail
        mock_smart_open_client_s3.stream_upload.side_effect = Exception("Upload failed")

        with pytest.raises(Exception, match="Upload failed"):
            stream_dsr_buffer_to_storage(
                storage_client=mock_smart_open_client_s3,
                bucket_name="test-bucket",
                file_key="test-report.html",
                dsr_buffer=test_buffer,
            )

    def test_dsr_builder_integration(
        self,
        mock_smart_open_client_s3,
    ):
        """Test integration with DsrReportBuilder - now handled by caller."""
        # This test is no longer relevant since DSR generation is handled by the caller
        # The storage function now only handles streaming the buffer to storage
        content = "Generated DSR report content"
        test_buffer = BytesIO(content.encode("utf-8"))

        # Mock the streaming upload
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client_s3.stream_upload.return_value = mock_stream

        result = stream_dsr_buffer_to_storage(
            storage_client=mock_smart_open_client_s3,
            bucket_name="test-bucket",
            file_key="test-report.html",
            dsr_buffer=test_buffer,
        )

        # Verify streaming upload was called
        mock_smart_open_client_s3.stream_upload.assert_called_once()

    def test_html_dsr_zip_with_attachments(
        self,
        mock_smart_open_client_s3,
    ):
        """Test that HTML DSR reports can be created as ZIPs with attachments."""
        # This test would verify the new HTML DSR ZIP functionality
        # that includes both the DSR report and actual attachment files
        # For now, we'll just verify the basic functionality works
        content = "HTML DSR report with attachments test"
        test_buffer = BytesIO(content.encode("utf-8"))

        # Mock the streaming upload
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client_s3.stream_upload.return_value = mock_stream

        result = stream_dsr_buffer_to_storage(
            storage_client=mock_smart_open_client_s3,
            bucket_name="test-bucket",
            file_key="test-report.html",
            dsr_buffer=test_buffer,
            content_type="application/zip",  # HTML DSR reports are now ZIPs
        )

        # Verify streaming upload was called
        mock_smart_open_client_s3.stream_upload.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            content_type="application/zip",
        )

        # Verify content was written
        mock_stream.write.assert_called_once_with(content.encode("utf-8"))

    def test_custom_content_type(
        self,
        mock_smart_open_client_s3,
    ):
        """Test that content type can be customized."""
        # Create a test buffer with content
        content = "Custom content type test"
        test_buffer = BytesIO(content.encode("utf-8"))

        # Mock the streaming upload
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client_s3.stream_upload.return_value = mock_stream

        result = stream_dsr_buffer_to_storage(
            storage_client=mock_smart_open_client_s3,
            bucket_name="test-bucket",
            file_key="test-report.html",
            dsr_buffer=test_buffer,
            content_type="text/html",  # Override default
        )

        # Verify custom content type was used
        mock_smart_open_client_s3.stream_upload.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            content_type="text/html",
        )

        # Verify content was written
        mock_stream.write.assert_called_once_with(content.encode("utf-8"))

    def test_different_storage_types(self):
        """Test that the function works with different storage types."""
        # Test with S3
        s3_client = Mock(spec=SmartOpenStorageClient)
        s3_client.storage_type = "s3"

        # Test with GCS
        gcs_client = Mock(spec=SmartOpenStorageClient)
        gcs_client.storage_type = "gcs"

        # Test with Azure
        azure_client = Mock(spec=SmartOpenStorageClient)
        azure_client.storage_type = "azure"

        # All should work the same way
        for client in [s3_client, gcs_client, azure_client]:
            mock_stream = Mock()
            mock_stream.__enter__ = Mock(return_value=mock_stream)
            mock_stream.__exit__ = Mock(return_value=None)
            client.stream_upload.return_value = mock_stream

            # Create test buffer
            test_buffer = BytesIO(b"test content")

            # Should not raise any errors
            stream_dsr_buffer_to_storage(
                storage_client=client,
                bucket_name="test-bucket",
                file_key="test-report.html",
                dsr_buffer=test_buffer,
                content_type="application/zip",
            )

            # Verify streaming upload was called
            client.stream_upload.assert_called_once()
            client.stream_upload.reset_mock()  # Reset for next iteration

    def test_create_dsr_report_files_generator(
        self,
    ):
        """Test the DSR report files generator function."""

        # Create a simple ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            zip_file.writestr("welcome.html", "<html>Welcome</html>")
            zip_file.writestr("data/main.css", "body { color: black; }")
            zip_file.writestr("attachments/index.html", "<html>Attachments</html>")

        zip_buffer.seek(0)

        # Mock attachments
        mock_attachments = [
            Mock(spec=["attachment"]),
            Mock(spec=["attachment"]),
        ]

        # Test the generator
        generator = create_dsr_report_files_generator(
            zip_buffer, mock_attachments, "test-bucket", 4, 10
        )

        # Convert generator to list to test
        files = list(generator)

        # Should have 3 files from the DSR report
        assert len(files) == 3

        # Check file names
        file_names = [file[0] for file in files]
        assert "welcome.html" in file_names
        assert "data/main.css" in file_names
        assert "attachments/index.html" in file_names

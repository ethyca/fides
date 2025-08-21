"""Tests for the DSR storage streaming functionality."""

from io import BytesIO
from unittest.mock import Mock, patch

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.storage.streaming.dsr_storage import (
    stream_html_dsr_report_to_storage_multipart,
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


class TestStreamHtmlDsrReportToStorageMultipart:
    """Test cases for stream_html_dsr_report_to_storage_multipart function."""

    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_successful_upload_smart_open_streaming(
        self,
        mock_dsr_builder_class,
        mock_smart_open_client_s3,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test successful upload using smart-open streaming."""
        # Mock the DsrReportBuilder to return content
        mock_builder = Mock()
        content = "This is a test HTML report content"
        mock_builder.generate.return_value = BytesIO(content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Mock the streaming upload
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client_s3.stream_upload.return_value = mock_stream

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=mock_smart_open_client_s3,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify streaming upload was used
        mock_smart_open_client_s3.stream_upload.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            content_type="text/html",
        )

        # Verify content was written
        mock_stream.write.assert_called_once_with(content.encode("utf-8"))

    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_successful_upload_with_large_content(
        self,
        mock_dsr_builder_class,
        mock_smart_open_client_s3,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test successful upload with large content using smart-open streaming."""
        # Mock the DsrReportBuilder to return large content
        mock_builder = Mock()
        large_content = "x" * (1024 * 1024)  # 1MB content
        mock_builder.generate.return_value = BytesIO(large_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Mock the streaming upload
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client_s3.stream_upload.return_value = mock_stream

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=mock_smart_open_client_s3,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify streaming upload was used regardless of content size
        mock_smart_open_client_s3.stream_upload.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            content_type="text/html",
        )

        # Verify content was written
        mock_stream.write.assert_called_once_with(large_content.encode("utf-8"))

    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_upload_failure_handling(
        self,
        mock_dsr_builder_class,
        mock_smart_open_client_s3,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test upload failure handling."""
        # Mock the DsrReportBuilder to return content
        mock_builder = Mock()
        content = "Test content"
        mock_builder.generate.return_value = BytesIO(content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Mock the streaming upload to fail
        mock_smart_open_client_s3.stream_upload.side_effect = Exception("Upload failed")

        with pytest.raises(Exception, match="Upload failed"):
            stream_html_dsr_report_to_storage_multipart(
                storage_client=mock_smart_open_client_s3,
                bucket_name="test-bucket",
                file_key="test-report.html",
                data=sample_dsr_data,
                privacy_request=mock_privacy_request,
            )

    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_dsr_builder_integration(
        self,
        mock_dsr_builder_class,
        mock_smart_open_client_s3,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test integration with DsrReportBuilder."""
        # Mock the DsrReportBuilder
        mock_builder = Mock()
        content = "Generated DSR report content"
        mock_builder.generate.return_value = BytesIO(content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Mock the streaming upload
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client_s3.stream_upload.return_value = mock_stream

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=mock_smart_open_client_s3,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify DsrReportBuilder was called correctly
        mock_dsr_builder_class.assert_called_once_with(
            privacy_request=mock_privacy_request,
            dsr_data=sample_dsr_data,
        )

        # Verify the report was generated
        mock_builder.generate.assert_called_once()

    def test_different_storage_types(self, mock_privacy_request, sample_dsr_data):
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
            with patch(
                "fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder"
            ) as mock_builder_class:
                mock_builder = Mock()
                mock_builder.generate.return_value = BytesIO(b"test content")
                mock_builder_class.return_value = mock_builder

                mock_stream = Mock()
                mock_stream.__enter__ = Mock(return_value=mock_stream)
                mock_stream.__exit__ = Mock(return_value=None)
                client.stream_upload.return_value = mock_stream

                # Should not raise any errors
                stream_html_dsr_report_to_storage_multipart(
                    storage_client=client,
                    bucket_name="test-bucket",
                    file_key="test-report.html",
                    data=sample_dsr_data,
                    privacy_request=mock_privacy_request,
                )

                # Verify streaming upload was called
                client.stream_upload.assert_called_once()
                client.stream_upload.reset_mock()  # Reset for next iteration

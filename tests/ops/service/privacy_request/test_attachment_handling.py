from unittest.mock import Mock, patch

import pytest

from fides.api.models.attachment import Attachment, AttachmentType
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.privacy_request.attachment_handling import (
    AttachmentData,
    get_attachments_content,
    process_attachments_for_upload,
)


class TestAttachmentData:
    def test_to_upload_dict(self):
        """Test converting AttachmentData to upload dictionary format"""
        attachment_data = AttachmentData(
            file_name="test.txt",
            file_size=100,
            download_url="https://example.com/test.txt",
            content_type="text/plain",
            fileobj=Mock(),
        )
        result = attachment_data.to_upload_dict()
        assert result["file_name"] == "test.txt"
        assert result["file_size"] == 100
        assert result["download_url"] == "https://example.com/test.txt"
        assert result["content_type"] == "text/plain"
        assert result["fileobj"] is not None

    def test_to_storage_dict(self):
        """Test converting AttachmentData to storage dictionary format"""
        attachment_data = AttachmentData(
            file_name="test.txt",
            file_size=100,
            download_url="https://example.com/test.txt",
            content_type="text/plain",
            fileobj=Mock(),
        )
        result = attachment_data.to_storage_dict()
        assert result["file_name"] == "test.txt"
        assert result["file_size"] == 100
        assert result["download_url"] == "https://example.com/test.txt"
        assert result["content_type"] == "text/plain"
        assert "fileobj" not in result


class TestGetAttachmentsContent:
    @pytest.fixture
    def mock_attachment(self):
        """Create a mock attachment for testing"""
        attachment = Mock(spec=Attachment)
        attachment.attachment_type = AttachmentType.include_with_access_package
        attachment.file_name = "test.txt"
        attachment.content_type = "text/plain"
        attachment.config = Mock()
        attachment.config.format.value = ResponseFormat.json.value
        return attachment

    def test_get_attachments_content_success(self, mock_attachment):
        """Test successful attachment content retrieval"""
        mock_attachment.retrieve_attachment.return_value = (
            100,
            "https://example.com/test.txt",
        )

        attachments = [mock_attachment]
        results = list(get_attachments_content(attachments))

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, AttachmentData)
        assert result.file_name == "test.txt"
        assert result.file_size == 100
        assert result.download_url == "https://example.com/test.txt"
        assert result.content_type == "text/plain"
        assert result.fileobj is None

    def test_get_attachments_content_html_format(self, mock_attachment):
        """Test attachment content retrieval for HTML format"""
        mock_attachment.retrieve_attachment.return_value = (
            100,
            "https://example.com/test.txt",
        )
        mock_attachment.config.format.value = ResponseFormat.html.value
        mock_attachment.retrieve_attachment_content.return_value = (100, Mock())

        attachments = [mock_attachment]
        results = list(get_attachments_content(attachments))

        assert len(results) == 1
        result = results[0]
        assert result.fileobj is not None

    def test_get_attachments_content_skip_non_included(self, mock_attachment):
        """Test skipping attachments not marked for inclusion"""
        mock_attachment.attachment_type = AttachmentType.internal_use_only

        attachments = [mock_attachment]
        results = list(get_attachments_content(attachments))

        assert len(results) == 0

    def test_get_attachments_content_error_handling(self, mock_attachment):
        """Test error handling during attachment content retrieval"""
        mock_attachment.retrieve_attachment.side_effect = Exception("Test error")

        attachments = [mock_attachment]
        results = list(get_attachments_content(attachments))

        assert len(results) == 0

    def test_get_attachments_content_html_missing_content(self, mock_attachment):
        """Test handling missing content for HTML format"""
        mock_attachment.retrieve_attachment.return_value = (
            100,
            "https://example.com/test.txt",
        )
        mock_attachment.config.format.value = ResponseFormat.html.value
        mock_attachment.retrieve_attachment_content.return_value = (100, None)

        attachments = [mock_attachment]
        results = list(get_attachments_content(attachments))

        assert len(results) == 0


class TestProcessAttachmentsForUpload:
    @pytest.fixture
    def mock_attachment_data(self):
        """Create a mock AttachmentData for testing"""
        return AttachmentData(
            file_name="test.txt",
            file_size=100,
            download_url="https://example.com/test.txt",
            content_type="text/plain",
            fileobj=Mock(),
        )

    def test_process_attachments_for_upload(self, mock_attachment_data):
        """Test processing attachments for upload"""
        attachments = [mock_attachment_data]
        upload_attachments, storage_attachments = process_attachments_for_upload(
            attachments
        )

        assert len(upload_attachments) == 1
        assert len(storage_attachments) == 1

        upload_attachment = upload_attachments[0]
        assert upload_attachment["file_name"] == "test.txt"
        assert upload_attachment["file_size"] == 100
        assert upload_attachment["download_url"] == "https://example.com/test.txt"
        assert upload_attachment["content_type"] == "text/plain"
        assert upload_attachment["fileobj"] is not None

        storage_attachment = storage_attachments[0]
        assert storage_attachment["file_name"] == "test.txt"
        assert storage_attachment["file_size"] == 100
        assert storage_attachment["download_url"] == "https://example.com/test.txt"
        assert storage_attachment["content_type"] == "text/plain"
        assert "fileobj" not in storage_attachment

    def test_process_attachments_for_upload_empty(self):
        """Test processing empty attachment list"""
        upload_attachments, storage_attachments = process_attachments_for_upload([])

        assert len(upload_attachments) == 0
        assert len(storage_attachments) == 0

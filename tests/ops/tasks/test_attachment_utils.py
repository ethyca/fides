from io import BytesIO
from typing import Any, Dict, List

import pytest

from fides.api.tasks.attachment_utils import (
    create_attachment_csv,
    remove_attachment_content,
)
from fides.config import CONFIG


class TestRemoveAttachmentContent:
    """Tests for the remove_attachment_content function."""

    def test_remove_content_from_simple_attachment(self):
        """Test removing content from a simple attachment structure."""
        data = {
            "attachments": [
                {"content": "secret data", "file_name": "test.txt"},
                {"content": "more secret data", "file_name": "test2.txt"},
            ]
        }
        remove_attachment_content(data)
        assert "content" not in data["attachments"][0]
        assert "content" not in data["attachments"][1]
        assert "file_name" in data["attachments"][0]
        assert "file_name" in data["attachments"][1]

    def test_remove_content_from_nested_structure(self):
        """Test removing content from a nested structure with attachments."""
        data = {
            "level1": {
                "attachments": [{"content": "secret1", "file_name": "test1.txt"}],
                "nested": {
                    "attachments": [{"content": "secret2", "file_name": "test2.txt"}]
                },
            }
        }
        remove_attachment_content(data)
        assert "content" not in data["level1"]["attachments"][0]
        assert "content" not in data["level1"]["nested"]["attachments"][0]

    def test_remove_content_from_list_structure(self):
        """Test removing content from a list structure with attachments."""
        data = [
            {"attachments": [{"content": "secret1", "file_name": "test1.txt"}]},
            {"attachments": [{"content": "secret2", "file_name": "test2.txt"}]},
        ]
        remove_attachment_content(data)
        assert "content" not in data[0]["attachments"][0]
        assert "content" not in data[1]["attachments"][0]

    def test_handle_non_dict_list_input(self):
        """Test handling of non-dict/list input."""
        data = "not a dict or list"
        remove_attachment_content(data)  # Should not raise any errors
        assert data == "not a dict or list"

    def test_handle_empty_attachments(self):
        """Test handling of empty attachments list."""
        data = {"attachments": []}
        remove_attachment_content(data)
        assert data == {"attachments": []}


class TestCreateAttachmentCSV:
    """Tests for the create_attachment_csv function."""

    def test_create_csv_with_valid_attachments(self):
        """Test creating CSV with valid attachment data."""
        attachments = [
            {
                "file_name": "test1.txt",
                "file_size": 100,
                "content_type": "text/plain",
                "download_url": "http://example.com/test1.txt",
            },
            {
                "file_name": "test2.txt",
                "file_size": 200,
                "content_type": "text/plain",
                "download_url": "http://example.com/test2.txt",
            },
        ]
        result = create_attachment_csv(attachments, "privacy_request_123")
        assert result is not None
        assert isinstance(result, BytesIO)

        # Read the CSV content
        result.seek(0)
        content = result.read().decode(CONFIG.security.encoding)
        assert "file_name" in content
        assert "test1.txt" in content
        assert "test2.txt" in content
        assert "100" in content
        assert "200" in content

    def test_create_csv_with_empty_attachments(self):
        """Test creating CSV with empty attachments list."""
        result = create_attachment_csv([], "privacy_request_123")
        assert result is None

    def test_create_csv_with_invalid_attachments(self):
        """Test creating CSV with invalid attachment data."""
        attachments = [
            {"invalid_key": "value"},  # Missing required fields
            None,  # None value
            "not a dict",  # String instead of dict
        ]
        result = create_attachment_csv(attachments, "privacy_request_123")
        assert result is not None
        assert isinstance(result, BytesIO)

        # Read the CSV content
        result.seek(0)
        content = result.read().decode(CONFIG.security.encoding)
        # Should contain headers and one row with default values for the dict attachment
        assert "file_name" in content
        assert "file_size" in content
        assert "content_type" in content
        assert "download_url" in content
        # Should contain one data row with default values
        assert content.count("\n") == 2  # Header row + one data row
        # Verify default values
        assert (
            ",0,application/octet-stream," in content
        )  # Default values for missing fields

    def test_create_csv_with_missing_optional_fields(self):
        """Test creating CSV with missing optional fields."""
        attachments = [
            {
                "file_name": "test.txt",
                # Missing file_size, content_type, and download_url
            }
        ]
        result = create_attachment_csv(attachments, "privacy_request_123")
        assert result is not None
        assert isinstance(result, BytesIO)

        # Read the CSV content
        result.seek(0)
        content = result.read().decode(CONFIG.security.encoding)
        assert "file_name" in content
        assert "test.txt" in content
        assert "0" in content  # Default file_size
        assert "application/octet-stream" in content  # Default content_type
        assert "" in content  # Default download_url

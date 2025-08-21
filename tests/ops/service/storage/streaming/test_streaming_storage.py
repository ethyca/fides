"""Tests for the streaming storage implementation.

These tests verify that the streaming storage correctly implements true streaming
using stream_zip for efficient ZIP creation without memory accumulation.
"""

from datetime import datetime
from io import BytesIO
from unittest.mock import Mock, create_autospec, patch

import pytest

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.retry import PermanentError, TransientError
from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    AttachmentProcessingInfo,
    StorageUploadConfig,
    StreamingBufferConfig,
)
from fides.api.service.storage.streaming.streaming_storage import StreamingStorage


@pytest.fixture
def mock_sleep():
    """Mock time.sleep to speed up retry tests."""
    with patch("time.sleep") as mock:
        yield mock


# =============================================================================
# Package Splitting Tests
# =============================================================================


class TestPackageSplitting:
    """Test package splitting functionality for large datasets."""

    def test_split_data_into_packages_basic(self):
        """Test basic data package splitting logic."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}] * 50,
                },
                {
                    "id": 2,
                    "name": "User 2",
                    "attachments": [{"storage_key": "key2", "size": 2000}] * 75,
                },
            ]
        }

        packages = processor.split_data_into_packages(data)
        assert len(packages) == 2

        # First package should contain User 2 (75 attachments) - largest first
        assert "users" in packages[0]
        assert len(packages[0]["users"]) == 1
        assert packages[0]["users"][0]["id"] == 2

        # Second package should contain User 1 (50 attachments)
        assert "users" in packages[1]
        assert len(packages[1]["users"]) == 1
        assert packages[1]["users"][0]["id"] == 1

    def test_split_data_into_packages_with_large_attachments(self):
        """Test package splitting with items that exceed the attachment limit."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(150)
                    ],
                }
            ]
        }

        packages = processor.split_data_into_packages(data)
        assert len(packages) == 2
        assert "users" in packages[0]
        assert "users" in packages[1]

        # First package should have 100 attachments
        assert len(packages[0]["users"][0]["attachments"]) == 100
        # Second package should have 50 attachments
        assert len(packages[1]["users"][0]["attachments"]) == 50

    def test_split_data_into_packages_with_custom_config(self):
        """Test package splitting with custom configuration."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}] * 30,
                },
                {
                    "id": 2,
                    "name": "User 2",
                    "attachments": [{"storage_key": "key2", "size": 2000}] * 45,
                },
            ]
        }

        config = PackageSplitConfig(max_attachments=40)
        packages = processor.split_data_into_packages(data, config)

        # Should split into 2 packages since User 2 has 45 attachments
        assert len(packages) == 2

    def test_split_data_into_packages_empty_data(self):
        """Test package splitting with empty data."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {}
        packages = processor.split_data_into_packages(data)
        assert packages == []

    def test_split_data_into_packages_no_attachments(self):
        """Test package splitting with data that has no attachments."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}
        packages = processor.split_data_into_packages(data)
        assert packages == []

    def test_split_data_into_packages_with_non_list_values(self):
        """Test package splitting with non-list values."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": "not a list", "items": 123}
        packages = processor.split_data_into_packages(data)
        assert packages == []

    def test_split_data_into_packages_with_empty_lists(self):
        """Test package splitting with empty lists."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [], "items": [{"id": 1, "attachments": []}]}
        packages = processor.split_data_into_packages(data)
        assert packages == []

    def test_split_data_into_packages_edge_cases(self):
        """Test package splitting with various edge cases."""
        # Test with very large attachment counts
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(500)
                    ],
                }
            ]
        }

        packages = processor.split_data_into_packages(data)
        # Should split into 5 packages: 100 + 100 + 100 + 100 + 100
        assert len(packages) == 5

        # Test with mixed data types
        data = {
            "users": [
                {"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}] * 50},
                {"id": 2, "attachments": [{"storage_key": "key2", "size": 2000}] * 75},
            ],
            "items": [
                {"id": 1, "attachments": [{"storage_key": "key3", "size": 3000}] * 25}
            ],
        }

        packages = processor.split_data_into_packages(data)
        # Should split into 2 packages: 75 + 50 + 25 = 150 total
        assert len(packages) == 2


# =============================================================================
# Attachment List Building Tests
# =============================================================================


class TestAttachmentListBuilding:
    """Test building and processing attachment lists."""

    def test_build_attachments_list_basic(self):
        """Test basic attachment list building."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": "key1", "size": 1000},
                        {"storage_key": "key2", "size": 2000},
                    ],
                }
            ]
        }

        config = PackageSplitConfig(max_attachments=100)
        attachments_list = processor.build_attachments_list(data, config)

        assert len(attachments_list) == 1
        key, item, attachment_count = attachments_list[0]
        assert key == "users"
        assert item["id"] == 1
        assert attachment_count == 2

    def test_build_attachments_list_with_splitting(self):
        """Test building attachments list when items exceed max_attachments limit."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(150)
                    ],
                }
            ]
        }

        config = PackageSplitConfig(max_attachments=100)
        attachments_list = processor.build_attachments_list(data, config)

        # Should split into 2 items: 100 + 50 attachments
        assert len(attachments_list) == 2

        # First item should have 100 attachments
        _, item1, count1 = attachments_list[0]
        assert item1["id"] == 1
        assert count1 == 100

        # Second item should have 50 attachments
        _, item2, count2 = attachments_list[1]
        assert item2["id"] == 1
        assert count2 == 50

    def test_build_attachments_list_empty_data(self):
        """Test building attachments list with empty data."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {}
        config = PackageSplitConfig()
        attachments_list = processor.build_attachments_list(data, config)
        assert attachments_list == []

    def test_build_attachments_list_no_attachments(self):
        """Test building attachments list with no attachments."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}
        config = PackageSplitConfig()
        attachments_list = processor.build_attachments_list(data, config)
        assert attachments_list == []

    def test_build_attachments_list_non_list_values(self):
        """Test building attachments list with non-list values."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": "not a list", "items": 123}
        config = PackageSplitConfig()
        attachments_list = processor.build_attachments_list(data, config)
        assert attachments_list == []

    def test_build_attachments_list_empty_lists(self):
        """Test building attachments list with empty lists."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [], "items": [{"id": 1, "attachments": []}]}
        config = PackageSplitConfig()
        attachments_list = processor.build_attachments_list(data, config)
        assert attachments_list == []

    def test_build_attachments_list_mixed_data_types(self):
        """Test building attachments list with mixed data types."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": "key1", "size": 1000},
                        {"storage_key": "key2", "size": 2000},
                    ],
                }
            ],
            "items": [
                {
                    "id": 1,
                    "name": "Item 1",
                    "attachments": [
                        {"storage_key": "key3", "size": 3000},
                    ],
                }
            ],
        }

        config = PackageSplitConfig(max_attachments=100)
        attachments_list = processor.build_attachments_list(data, config)

        assert len(attachments_list) == 2

        # Check users
        key1, item1, count1 = attachments_list[0]
        assert key1 == "users"
        assert item1["id"] == 1
        assert count1 == 2

        # Check items
        key2, item2, count2 = attachments_list[1]
        assert key2 == "items"
        assert item2["id"] == 1
        assert count2 == 1


# =============================================================================
# Attachment Collection and Validation Tests
# =============================================================================


class TestAttachmentCollectionAndValidation:
    """Test collecting and validating attachments from data."""

    def test_collect_and_validate_attachments(self):
        """Test collecting and validating attachments from data."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": "key1", "size": 1000, "file_name": "file1.txt"},
                        {"storage_key": "key2", "size": 2000, "file_name": "file2.txt"},
                    ],
                }
            ]
        }

        attachments = processor._collect_and_validate_attachments(data)
        assert len(attachments) == 2

        # Check first attachment
        assert attachments[0].attachment.storage_key == "key1"
        assert attachments[0].attachment.size == 1000
        assert attachments[0].attachment.file_name == "file1.txt"
        assert attachments[0].base_path == "users/1/attachments"
        assert attachments[0].item["id"] == 1

        # Check second attachment
        assert attachments[1].attachment.storage_key == "key2"
        assert attachments[1].attachment.size == 2000
        assert attachments[1].attachment.file_name == "file2.txt"
        assert attachments[1].base_path == "users/1/attachments"
        assert attachments[1].item["id"] == 1

    def test_collect_and_validate_attachments_missing_storage_key(self):
        """Test collecting attachments with missing storage_key."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"size": 1000, "file_name": "file1.txt"},  # Missing storage_key
                        {"storage_key": "key2", "size": 2000, "file_name": "file2.txt"},
                    ],
                }
            ]
        }

        attachments = processor._collect_and_validate_attachments(data)
        # Should only collect the attachment with storage_key
        assert len(attachments) == 1
        assert attachments[0].attachment.storage_key == "key2"

    def test_collect_and_validate_attachments_invalid_attachment_data(self):
        """Test collecting attachments with invalid data."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": "key1", "size": "invalid_size"},  # Invalid size
                        {"storage_key": "key2", "size": 2000, "file_name": "file2.txt"},
                    ],
                }
            ]
        }

        attachments = processor._collect_and_validate_attachments(data)
        # Should only collect the valid attachment
        assert len(attachments) == 1
        assert attachments[0].attachment.storage_key == "key2"

    def test_collect_and_validate_attachments_non_dict_items(self):
        """Test collecting attachments with non-dict items."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}],
                },
                "not a dict",  # Invalid item
                {
                    "id": 2,
                    "name": "User 2",
                    "attachments": [{"storage_key": "key2", "size": 2000}],
                },
            ]
        }

        attachments = processor._collect_and_validate_attachments(data)
        # Should only collect from valid dict items
        assert len(attachments) == 2

    def test_collect_and_validate_attachments_with_mock_objects(self):
        """Test collecting attachments with mock objects."""
        mock_attachment = {
            "storage_key": "key1",
            "size": 1000,
            "file_name": "file1.txt",
        }

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [mock_attachment],
                }
            ]
        }

        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        attachments = processor._collect_and_validate_attachments(data)
        assert len(attachments) == 1
        assert attachments[0].attachment.storage_key == "key1"

    def test_collect_and_validate_attachments_non_iterable_values(self):
        """Test collecting attachments with non-iterable values."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": "not a list",  # Non-iterable
            "items": [
                {"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}
            ],
        }

        attachments = processor._collect_and_validate_attachments(data)
        # Should only collect from iterable values
        assert len(attachments) == 1
        assert attachments[0].attachment.storage_key == "key1"

    def test_collect_and_validate_attachments_values_that_cause_exceptions(self):
        """Test collecting attachments with values that might cause exceptions."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}],
                }
            ],
            "items": None,  # This might cause issues
        }

        attachments = processor._collect_and_validate_attachments(data)
        # Should handle None gracefully and only collect from valid data
        assert len(attachments) == 1
        assert attachments[0].attachment.storage_key == "key1"

    def test_collect_and_validate_attachments_with_direct_attachments_key(self):
        """Test collecting attachments from the direct 'attachments' key."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "attachments": [
                {
                    "file_name": "test_file_pdf.pdf",
                    "file_size": 11236,
                    "download_url": "https://example.com/file1.pdf",
                    "content_type": "application/pdf",
                },
                {
                    "file_name": "test_file_text.txt",
                    "file_size": 41,
                    "download_url": "https://example.com/file2.txt",
                    "content_type": "text/plain",
                },
            ]
        }

        attachments = processor._collect_and_validate_attachments(data)
        assert len(attachments) == 2

        # Check first attachment
        assert attachments[0].attachment.storage_key == "https://example.com/file1.pdf"
        assert attachments[0].attachment.file_name == "test_file_pdf.pdf"
        assert attachments[0].attachment.size == 11236
        assert attachments[0].base_path == "attachments/1"

        # Check second attachment
        assert attachments[1].attachment.storage_key == "https://example.com/file2.txt"
        assert attachments[1].attachment.file_name == "test_file_text.txt"
        assert attachments[1].attachment.size == 41
        assert attachments[1].base_path == "attachments/2"

    def test_collect_and_validate_attachments_mixed_structure(self):
        """Test collecting attachments from both direct 'attachments' key and nested structures."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": "key1", "size": 1000, "file_name": "file1.txt"},
                    ],
                }
            ],
            "attachments": [
                {
                    "file_name": "direct_file.pdf",
                    "download_url": "https://example.com/direct.pdf",
                    "file_size": 5000,
                }
            ],
        }

        attachments = processor._collect_and_validate_attachments(data)
        assert len(attachments) == 2

        # Check nested attachment
        nested_attachment = next(
            a for a in attachments if a.base_path == "users/1/attachments"
        )
        assert nested_attachment.attachment.storage_key == "key1"

        # Check direct attachment
        direct_attachment = next(
            a for a in attachments if a.base_path == "attachments/1"
        )
        assert (
            direct_attachment.attachment.storage_key == "https://example.com/direct.pdf"
        )
        assert direct_attachment.attachment.file_name == "direct_file.pdf"

    def test_collect_attachments_direct_only(self):
        """Test _collect_attachments method with direct attachments only."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "attachments": [
                {
                    "file_name": "file1.pdf",
                    "download_url": "https://example.com/file1.pdf",
                    "file_size": 1000,
                },
                {
                    "file_name": "file2.txt",
                    "url": "https://example.com/file2.txt",
                    "file_size": 500,
                },
            ]
        }

        raw_attachments = processor._collect_attachments(data)
        assert len(raw_attachments) == 2

        # Check first attachment
        first = raw_attachments[0]
        assert first["type"] == "direct"
        assert first["base_path"] == "attachments/1"
        assert first["attachment"]["file_name"] == "file1.pdf"

        # Check second attachment
        second = raw_attachments[1]
        assert second["type"] == "direct"
        assert second["base_path"] == "attachments/2"
        assert second["attachment"]["file_name"] == "file2.txt"

    def test_collect_attachments_nested_only(self):
        """Test _collect_attachments method with nested attachments only."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": "key1", "file_name": "file1.txt"},
                        {"storage_key": "key2", "file_name": "file2.txt"},
                    ],
                }
            ]
        }

        raw_attachments = processor._collect_attachments(data)
        assert len(raw_attachments) == 2

        # Check first attachment
        first = raw_attachments[0]
        assert first["type"] == "nested"
        assert first["base_path"] == "users/1/attachments"
        assert first["attachment"]["storage_key"] == "key1"

        # Check second attachment
        second = raw_attachments[1]
        assert second["type"] == "nested"
        assert second["attachment"]["storage_key"] == "key2"

    def test_collect_attachments_mixed_types(self):
        """Test _collect_attachments method with both direct and nested attachments."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [{"storage_key": "key1", "file_name": "file1.txt"}],
                }
            ],
            "attachments": [
                {
                    "file_name": "direct_file.pdf",
                    "download_url": "https://example.com/direct.pdf",
                }
            ],
        }

        raw_attachments = processor._collect_attachments(data)
        assert len(raw_attachments) == 2

        # Check nested attachment
        nested = next(a for a in raw_attachments if a["type"] == "nested")
        assert nested["base_path"] == "users/1/attachments"

        # Check direct attachment
        direct = next(a for a in raw_attachments if a["type"] == "direct")
        assert direct["base_path"] == "attachments/1"

    def test_validate_attachment_direct(self):
        """Test _validate_attachment method with direct attachment."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        attachment_data = {
            "attachment": {
                "file_name": "test.pdf",
                "download_url": "https://example.com/test.pdf",
                "file_size": 5000,
                "content_type": "application/pdf",
            },
            "base_path": "attachments/1",
            "item": {"id": 1},
            "type": "direct",
        }

        result = processor._validate_attachment(attachment_data)
        assert result is not None
        assert result.attachment.storage_key == "https://example.com/test.pdf"
        assert result.attachment.file_name == "test.pdf"
        assert result.attachment.size == 5000
        assert result.base_path == "attachments/1"

    def test_validate_attachment_nested(self):
        """Test _validate_attachment method with nested attachment."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        attachment_data = {
            "attachment": {
                "storage_key": "storage_key_123",
                "file_name": "test.txt",
                "size": 100,
            },
            "base_path": "users/1/attachments",
            "item": {"id": 1},
            "type": "nested",
        }

        result = processor._validate_attachment(attachment_data)
        assert result is not None
        assert result.attachment.storage_key == "storage_key_123"
        assert result.attachment.file_name == "test.txt"
        assert result.attachment.size == 100
        assert result.base_path == "users/1/attachments"

    def test_validate_attachment_invalid_data(self):
        """Test _validate_attachment method with invalid attachment data."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Test with missing required fields
        attachment_data = {
            "attachment": {
                "file_name": "test.txt"
                # Missing storage_key for nested type
            },
            "base_path": "users/1/attachments",
            "item": {"id": 1},
            "type": "nested",
        }

        result = processor._validate_attachment(attachment_data)
        assert result is None

        # Test with malformed data
        attachment_data = {
            "attachment": "not a dict",
            "base_path": "attachments/1",
            "item": {"id": 1},
            "type": "direct",
        }

        result = processor._validate_attachment(attachment_data)
        assert result is None

    def test_collect_and_validate_attachments_delegation(self):
        """Test that _collect_and_validate_attachments properly delegates to helper methods."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Mock the helper methods
        with (
            patch.object(processor, "_collect_attachments") as mock_collect,
            patch.object(processor, "_validate_attachment") as mock_validate,
        ):

            mock_collect.return_value = [
                {
                    "attachment": {"storage_key": "key1", "file_name": "file1.txt"},
                    "base_path": "users/1/attachments",
                    "item": {"id": 1},
                    "type": "nested",
                }
            ]

            mock_validate.return_value = AttachmentProcessingInfo(
                attachment=AttachmentInfo(storage_key="key1", file_name="file1.txt"),
                base_path="users/1/attachments",
                item={"id": 1},
            )

            data = {"users": [{"id": 1, "attachments": [{"storage_key": "key1"}]}]}
            result = processor._collect_and_validate_attachments(data)

            # Verify helper methods were called
            mock_collect.assert_called_once_with(data)
            mock_validate.assert_called_once()

            assert len(result) == 1
            assert result[0].attachment.storage_key == "key1"

    def test_transform_data_for_access_package(self):
        """Test that _transform_data_for_access_package correctly transforms download URLs."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Test data with attachments that have download URLs
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {
                            "file_name": "document.pdf",
                            "download_url": "https://s3.amazonaws.com/bucket/document.pdf",
                            "size": 1024,
                            "content_type": "application/pdf",
                        }
                    ],
                }
            ]
        }

        # Create mock attachment processing info
        from fides.api.service.storage.streaming.schemas import (
            AttachmentInfo,
            AttachmentProcessingInfo,
        )

        attachment_info = AttachmentProcessingInfo(
            attachment=AttachmentInfo(
                storage_key="https://s3.amazonaws.com/bucket/document.pdf",
                file_name="document.pdf",
                size=1024,
                content_type="application/pdf",
            ),
            base_path="users/1/attachments",
            item=data["users"][0],
            type="nested",
        )

        all_attachments = [attachment_info]

        # Transform the data
        transformed_data = processor._transform_data_for_access_package(
            data, all_attachments
        )

        # The download_url should now contain the internal path, but keep the same key name
        assert "download_url" in transformed_data["users"][0]["attachments"][0]
        assert (
            transformed_data["users"][0]["attachments"][0]["download_url"]
            == "attachments/document.pdf"
        )

        # The original data should not be modified
        assert (
            data["users"][0]["attachments"][0]["download_url"]
            == "https://s3.amazonaws.com/bucket/document.pdf"
        )

    def test_transform_data_for_access_package_no_attachments(self):
        """Test that _transform_data_for_access_package returns original data when no attachments."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}

        # Transform with no attachments
        transformed_data = processor._transform_data_for_access_package(data, [])

        # Should return the same data unchanged
        assert transformed_data == data

    def test_transform_data_for_access_package_nested_urls(self):
        """Test that _transform_data_for_access_package handles nested URL structures."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Test data with nested structures containing URLs
        data = {
            "users": [
                {
                    "id": 1,
                    "profile": {
                        "avatar": {
                            "download_url": "https://s3.amazonaws.com/bucket/avatar.jpg"
                        }
                    },
                }
            ]
        }

        # Create mock attachment processing info
        from fides.api.service.storage.streaming.schemas import (
            AttachmentInfo,
            AttachmentProcessingInfo,
        )

        attachment_info = AttachmentProcessingInfo(
            attachment=AttachmentInfo(
                storage_key="https://s3.amazonaws.com/bucket/avatar.jpg",
                file_name="avatar.jpg",
                size=512,
                content_type="image/jpeg",
            ),
            base_path="users/1/profile/avatar",
            item=data["users"][0],
            type="nested",
        )

        all_attachments = [attachment_info]

        # Transform the data
        transformed_data = processor._transform_data_for_access_package(
            data, all_attachments
        )

        # download_url should contain the internal path, keeping the same key name
        assert "download_url" in transformed_data["users"][0]["profile"]["avatar"]
        assert (
            transformed_data["users"][0]["profile"]["avatar"]["download_url"]
            == "attachments/avatar.jpg"
        )

        # The original data should not be modified
        assert (
            data["users"][0]["profile"]["avatar"]["download_url"]
            == "https://s3.amazonaws.com/bucket/avatar.jpg"
        )

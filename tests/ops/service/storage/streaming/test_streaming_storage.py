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


# =============================================================================
# Streaming ZIP Creation Tests
# =============================================================================


class TestStreamingZipCreation:
    """Test streaming ZIP creation functionality."""

    def test_stream_attachments_to_storage_zip_creation_failure(self):
        """Test streaming ZIP creation when ZIP creation fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.side_effect = Exception("ZIP creation failed")
        mock_privacy_request = Mock()
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [{"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}]
        }

        # Mock the _collect_and_validate_attachments function
        with patch.object(
            processor, "_collect_and_validate_attachments"
        ) as mock_collect:
            # Create proper processing info object
            attachment = AttachmentInfo(
                storage_key="key1", size=1000, file_name="file1.txt"
            )
            mock_processing_info = AttachmentProcessingInfo(
                attachment=attachment, base_path="users", item=data["users"][0]
            )

            mock_collect.return_value = [mock_processing_info]

            mock_storage_client.get_object.return_value = b"test content"

            with pytest.raises(Exception, match="ZIP creation failed"):
                processor.stream_attachments_to_storage_zip(
                    mock_storage_client,
                    "test-bucket",
                    "test-key.zip",
                    data,
                    mock_privacy_request,
                    max_workers=2,
                )

    def test_stream_attachments_to_storage_zip_no_attachments(self):
        """Test streaming ZIP creation with no attachments."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [{"id": 1, "name": "User 1"}],  # No attachments
            "items": [{"id": 1, "name": "Item 1"}],  # No attachments
        }

        # Mock the _collect_and_validate_attachments function
        with patch.object(
            processor, "_collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = []  # No attachments

            processor.stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
            )

            # Should call put_object with the data files
            # Note: put_object may be called multiple times due to retry logic
            assert mock_storage_client.put_object.call_count >= 1
            call_args = mock_storage_client.put_object.call_args
            assert call_args[0][0] == "test-bucket"
            assert call_args[0][1] == "test-key.zip"

    def test_create_data_files_json_format(self):
        """Test _create_data_files method with JSON format data."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "data": [
                {"id": 1, "name": "User 1", "attachments": [{"key": "value"}]},
                {"id": 2, "name": "User 2", "attachments": [{"key": "value2"}]},
            ],
            "items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
        }

        # Test with JSON format (default)
        files = list(processor._create_data_files(data, resp_format="json"))

        # Should create 2 files: data.json and items.json
        assert len(files) == 2

        # Check data.json
        data_file = files[0]
        assert data_file[0] == "data.json"
        assert isinstance(data_file[1], BytesIO)
        content = data_file[1].read().decode("utf-8")
        assert '"attachments"' in content

        # Check items.json
        items_file = files[1]
        assert items_file[0] == "items.json"
        assert isinstance(items_file[1], BytesIO)
        content = items_file[1].read().decode("utf-8")
        assert '"id"' in content
        assert '"Item 1"' in content

    def test_create_data_files_csv_format(self):
        """Test _create_data_files method with CSV format data."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "data": [
                {"id": 1, "name": "User 1", "attachments": [{"key": "value"}]},
                {"id": 2, "name": "User 2", "attachments": [{"key": "value2"}]},
            ],
            "items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
        }

        # Test with CSV format
        files = list(processor._create_data_files(data, resp_format="csv"))

        # Should create 2 files: data.csv and items.csv
        assert len(files) == 2

        # Check data.csv (with attachments, but still CSV as requested)
        data_file = files[0]
        assert data_file[0] == "data.csv"
        assert isinstance(data_file[1], BytesIO)
        content = data_file[1].read().decode("utf-8")
        assert "id,name,attachments" in content
        assert "1,User 1," in content

        # Check items.csv
        items_file = files[1]
        assert items_file[0] == "items.csv"
        assert isinstance(items_file[1], BytesIO)
        content = items_file[1].read().decode("utf-8")
        assert "id,name" in content
        assert "1,Item 1" in content

    def test_create_data_files_empty_data(self):
        """Test _create_data_files method with empty data."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {}
        files = list(processor._create_data_files(data))
        assert len(files) == 0

    def test_create_data_files_no_lists(self):
        """Test _create_data_files method with non-list data."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"config": {"setting": "value"}, "metadata": "string_value"}
        files = list(processor._create_data_files(data))
        assert len(files) == 0

    def test_create_data_files_with_records_key(self):
        """Test _create_data_files method with 'records' key."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "records": [
                {"id": 1, "name": "Record 1", "attachments": [{"key": "value"}]},
                {"id": 2, "name": "Record 2"},
            ]
        }

        files = list(processor._create_data_files(data))

        # Should create 1 file: records.json (has attachments, so JSON format)
        assert len(files) == 1

        records_file = files[0]
        assert records_file[0] == "records.json"
        assert isinstance(records_file[1], BytesIO)
        content = records_file[1].read().decode("utf-8")
        assert '"attachments"' in content

    def test_get_attachment_batches(self):
        """Test _get_attachment_batches method."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Create mock processing info objects
        mock_infos = []
        for i in range(7):  # 7 total attachments
            attachment = AttachmentInfo(
                storage_key=f"key{i}", size=1000, file_name=f"file{i}.txt"
            )
            mock_info = AttachmentProcessingInfo(
                attachment=attachment, base_path="users", item={"id": i}
            )
            mock_infos.append(mock_info)

        # Test with batch size 3
        batches = processor._get_attachment_batches(mock_infos, 3)
        assert len(batches) == 3  # ceil(7/3) = 3

        # First batch should have 3 items
        assert len(batches[0]) == 3
        assert batches[0][0].attachment.storage_key == "key0"
        assert batches[0][2].attachment.storage_key == "key2"

        # Second batch should have 3 items
        assert len(batches[1]) == 3
        assert batches[1][0].attachment.storage_key == "key3"
        assert batches[1][2].attachment.storage_key == "key5"

        # Third batch should have 1 item
        assert len(batches[2]) == 1
        assert batches[2][0].attachment.storage_key == "key6"

    def test_get_attachment_batches_exact_multiple(self):
        """Test _get_attachment_batches method with exact batch size multiple."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Create 6 mock processing info objects
        mock_infos = []
        for i in range(6):
            attachment = AttachmentInfo(
                storage_key=f"key{i}", size=1000, file_name=f"file{i}.txt"
            )
            mock_info = AttachmentProcessingInfo(
                attachment=attachment, base_path="users", item={"id": i}
            )
            mock_infos.append(mock_info)

        # Test with batch size 2
        batches = processor._get_attachment_batches(mock_infos, 2)
        assert len(batches) == 3  # 6/2 = 3

        # Each batch should have exactly 2 items
        for batch in batches:
            assert len(batch) == 2

    def test_create_zip_generator_integration(self):
        """Test _create_zip_generator method integration."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.return_value = b"test content"
        processor = StreamingStorage(mock_storage_client)

        data = {
            "data": [{"id": 1, "name": "User 1", "attachments": [{"key": "value"}]}],
            "items": [{"id": 1, "name": "Item 1"}],
        }

        # Create mock processing info objects
        mock_infos = []
        for i in range(4):
            attachment = AttachmentInfo(
                storage_key=f"key{i}", size=1000, file_name=f"file{i}.txt"
            )
            mock_info = AttachmentProcessingInfo(
                attachment=attachment, base_path="users", item={"id": i}
            )
            mock_infos.append(mock_info)

        # Create ZIP generator
        generator = processor._create_zip_generator(
            data, mock_infos, mock_storage_client, "test-bucket", 2, 2
        )

        # Collect all files
        files = list(generator)

        # Should have 2 data files + 4 attachment files = 6 total
        assert len(files) == 6

        # Check data files (first 2 files)
        data_files = [f[0] for f in files[:2]]
        assert "data.json" in data_files
        assert (
            "items.json" in data_files
        )  # Changed from .csv to .json since resp_format defaults to json

        # Check attachment files (last 4 files)
        attachment_files = [f[0] for f in files[2:]]
        assert all(f.startswith("file") for f in attachment_files)
        assert len(attachment_files) == 4

        # Verify all files are in stream_zip format: (filename, datetime, mode, method, content_iter)
        for file_info in files:
            assert len(file_info) == 5
            filename, dt, mode, method, content_iter = file_info
            assert isinstance(dt, datetime)
            assert mode == 0o644
            # _ZIP_32_TYPE() is a compression method object, not callable
            assert "ZIP_32_TYPE" in str(type(method))  # method should be _ZIP_32_TYPE
            assert hasattr(content_iter, "__iter__")  # content_iter should be iterable

    def test_upload_data_only_zip(self):
        """Test _upload_data_only_zip method."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "data": [{"id": 1, "name": "User 1", "attachments": [{"key": "value"}]}],
            "items": [{"id": 1, "name": "Item 1"}],
        }

        processor._upload_data_only_zip(
            mock_storage_client, "test-bucket", "test-key.zip", data
        )

        # Should call put_object once
        assert mock_storage_client.put_object.call_count == 1

        call_args = mock_storage_client.put_object.call_args
        # Check positional arguments
        assert call_args[0][0] == "test-bucket"
        assert call_args[0][1] == "test-key.zip"
        # Check keyword arguments
        assert call_args.kwargs["content_type"] == "application/zip"

    def test_convert_to_stream_zip_format(self):
        """Test _convert_to_stream_zip_format method."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Create test data
        test_files = [
            ("file1.txt", BytesIO(b"content1"), {"size": 100}),
            ("file2.csv", BytesIO(b"content2"), {"size": 200}),
        ]

        # Convert to stream zip format
        result = list(processor._convert_to_stream_zip_format(test_files))

        # Should have 2 files
        assert len(result) == 2

        # Check first file
        filename1, datetime1, mode1, method1, content_iter1 = result[0]
        assert filename1 == "file1.txt"
        assert mode1 == 0o644
        assert isinstance(datetime1, datetime)
        assert list(content_iter1) == [b"content1"]

        # Check second file
        filename2, datetime2, mode2, method2, content_iter2 = result[1]
        assert filename2 == "file2.csv"
        assert mode2 == 0o644
        assert isinstance(datetime2, datetime)
        assert list(content_iter2) == [b"content2"]

    def test_convert_to_stream_zip_format_empty_generator(self):
        """Test _convert_to_stream_zip_format method with empty generator."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Empty generator
        empty_files = []

        result = list(processor._convert_to_stream_zip_format(empty_files))
        assert len(result) == 0

    def test_convert_to_stream_zip_format_preserves_bytesio_position(self):
        """Test that _convert_to_stream_zip_format preserves BytesIO position."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Create BytesIO with content
        content = BytesIO(b"test content")
        original_position = content.tell()

        test_files = [("test.txt", content, {})]

        # Convert to stream zip format
        result = list(processor._convert_to_stream_zip_format(test_files))

        # Should have 1 file
        assert len(result) == 1

        # Check that BytesIO position is preserved
        assert content.tell() == original_position

        # Content should still be readable
        filename, datetime_obj, mode, method, content_iter = result[0]
        assert filename == "test.txt"
        assert list(content_iter) == [b"test content"]

    def test_streaming_storage_initialization(self):
        """Test StreamingStorage class initialization."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        assert processor.storage_client == mock_storage_client

    def test_streaming_storage_methods_are_instance_methods(self):
        """Test that StreamingStorage methods are properly bound instance methods."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Check that methods are bound to the instance
        assert processor._convert_to_stream_zip_format.__self__ == processor
        assert processor.build_attachments_list.__self__ == processor
        assert processor.split_data_into_packages.__self__ == processor
        assert processor._collect_and_validate_attachments.__self__ == processor
        assert processor.upload_to_storage_streaming.__self__ == processor
        assert processor.stream_attachments_to_storage_zip.__self__ == processor

    def test_upload_to_storage_streaming_html_format(self):
        """Test uploading data in HTML format."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Create a properly configured mock privacy request
        mock_privacy_request = Mock()
        mock_privacy_request.id = "test-request-id"

        # Mock the policy and action type
        mock_policy = Mock()
        mock_policy.get_action_type.return_value = Mock()
        mock_policy.get_action_type.return_value.value = "access"
        mock_privacy_request.policy = mock_policy

        # Mock the get_persisted_identity method to return a proper structure
        mock_identity = Mock()
        mock_identity.labeled_dict.return_value = {
            "email": {"value": "test@example.com", "label": "Email"},
            "phone": {"value": None, "label": "Phone"},
        }
        mock_privacy_request.get_persisted_identity.return_value = mock_identity

        data = {
            "users": [
                {"id": 1, "name": "User 1", "email": "user1@example.com"},
                {"id": 2, "name": "User 2", "email": "user2@example.com"},
            ]
        }

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.html,
        )

        # Mock successful upload (HTML format uses different streaming approach)
        # No need to mock generate_presigned_url since we now use _generate_access_package_url

        result = processor.upload_to_storage_streaming(
            mock_storage_client, data, config, mock_privacy_request
        )

        # Should return an access package URL
        assert result is not None
        assert "test-bucket" in result
        assert "test-data" in result

        # HTML format uses different streaming approach, so put_object may not be called
        # We no longer call generate_presigned_url directly, so no need to assert on it

    def test_upload_to_storage_streaming_with_buffer_config(self):
        """Test upload_to_storage_streaming method with custom buffer config."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.csv",
            max_workers=5,
            resp_format=ResponseFormat.csv.value,
        )
        mock_privacy_request = Mock()
        buffer_config = StreamingBufferConfig(
            zip_buffer_threshold=10 * 1024 * 1024,  # 10MB
            stream_buffer_threshold=1024 * 1024,  # 1MB
            chunk_size_threshold=2 * 1024 * 1024,  # 2MB
        )

        # Mock the streaming ZIP function
        with patch.object(
            processor, "stream_attachments_to_storage_zip"
        ) as mock_stream_zip:
            result = processor.upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                mock_privacy_request,
                buffer_config=buffer_config,
                batch_size=20,
            )

            # Should call stream_attachments_to_storage_zip with custom config
            mock_stream_zip.assert_called_once_with(
                mock_storage_client,
                "test-bucket",
                "test-key.csv",
                data,
                mock_privacy_request,
                5,  # max_workers
                buffer_config,
                20,  # batch_size
            )


# =============================================================================
# Upload to Storage Tests
# =============================================================================


class TestUploadToStorage:
    """Test uploading data to storage with different formats."""

    def test_upload_to_storage_streaming_csv_format(self):
        """Test uploading data in CSV format."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {"id": 1, "name": "User 1", "email": "user1@example.com"},
                {"id": 2, "name": "User 2", "email": "user2@example.com"},
            ]
        }

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.csv,
        )

        # Mock successful upload
        # No need to mock generate_presigned_url since we now use _generate_access_package_url

        result = processor.upload_to_storage_streaming(
            mock_storage_client, data, config, mock_privacy_request
        )

        # Should return an access package URL
        assert result is not None
        assert "test-bucket" in result
        assert "test-data" in result

        # Should have called put_object but not generate_presigned_url
        mock_storage_client.put_object.assert_called_once()
        # We no longer call generate_presigned_url directly, so no need to assert on it

    def test_upload_to_storage_streaming_json_format(self):
        """Test uploading data in JSON format."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [
                {"id": 1, "name": "User 1", "email": "user1@example.com"},
                {"id": 2, "name": "User 2", "email": "user2@example.com"},
            ]
        }

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.json,
        )

        # Mock successful upload
        # No need to mock generate_presigned_url since we now use _generate_access_package_url

        result = processor.upload_to_storage_streaming(
            mock_storage_client, data, config, mock_privacy_request
        )

        # Should return an access package URL
        assert result is not None
        assert "test-bucket" in result
        assert "test-data" in result

        # Should have called put_object but not generate_presigned_url
        mock_storage_client.put_object.assert_called_once()
        # We no longer call generate_presigned_url directly, so no need to assert on it

    def test_upload_to_storage_streaming_html_format(self):
        """Test uploading data in HTML format."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Create a properly configured mock privacy request
        mock_privacy_request = Mock()
        mock_privacy_request.id = "test-request-id"

        # Mock the policy and action type
        mock_policy = Mock()
        mock_policy.get_action_type.return_value = Mock()
        mock_policy.get_action_type.return_value.value = "access"
        mock_privacy_request.policy = mock_policy

        # Mock the get_persisted_identity method to return a proper structure
        mock_identity = Mock()
        mock_identity.labeled_dict.return_value = {
            "email": {"value": "test@example.com", "label": "Email"},
            "phone": {"value": None, "label": "Phone"},
        }
        mock_privacy_request.get_persisted_identity.return_value = mock_identity

        data = {
            "users": [
                {"id": 1, "name": "User 1", "email": "user1@example.com"},
                {"id": 2, "name": "User 2", "email": "user2@example.com"},
            ]
        }

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.html,
        )

        # Mock successful upload (HTML format uses different streaming approach)
        # No need to mock generate_presigned_url since we now use _generate_access_package_url

        result = processor.upload_to_storage_streaming(
            mock_storage_client, data, config, mock_privacy_request
        )

        # Should return an access package URL
        assert result is not None
        assert "test-bucket" in result
        assert "test-data" in result

        # HTML format uses different streaming approach, so put_object may not be called
        # We no longer call generate_presigned_url directly, so no need to assert on it

    def test_upload_to_storage_streaming_unsupported_format(self):
        """Test uploading data with unsupported format."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format="UNSUPPORTED",  # Invalid format
        )

        with pytest.raises(StorageUploadError, match="unsupported format UNSUPPORTED"):
            processor.upload_to_storage_streaming(
                mock_storage_client, data, config, mock_privacy_request
            )

    def test_upload_to_storage_streaming_no_privacy_request(self):
        """Test uploading data without privacy request."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.json,
        )

        # Should raise error when no privacy request is provided
        with pytest.raises(ValueError, match="Privacy request must be provided"):
            processor.upload_to_storage_streaming(
                mock_storage_client, data, config, privacy_request=None
            )

    def test_upload_to_storage_streaming_document_only_not_implemented(self):
        """Test that document-only upload is not implemented."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.json,
        )

        # Mock document object
        mock_document = Mock()

        with pytest.raises(
            NotImplementedError, match="Document-only uploads not yet implemented"
        ):
            processor.upload_to_storage_streaming(
                mock_storage_client, data, config, mock_privacy_request, mock_document
            )

    def test_upload_to_storage_streaming_upload_failure(self):
        """Test upload failure when storage upload fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.json,
        )

        # Mock upload failure
        mock_storage_client.put_object.side_effect = Exception("Upload failed")

        with pytest.raises(
            StorageUploadError,
            match="Unexpected error during true streaming upload: Upload failed",
        ):
            processor.upload_to_storage_streaming(
                mock_storage_client, data, config, mock_privacy_request
            )

        # Should have called put_object at least once (the initial attempt)
        assert mock_storage_client.put_object.call_count >= 1

    def test_upload_to_storage_streaming_access_package_url_generation_success(self):
        """Test that access package URL generation succeeds and returns a valid URL."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.json,
        )

        # Mock successful upload
        mock_storage_client.put_object.return_value = None
        # We no longer call generate_presigned_url directly, so no need to mock it

        # Should successfully generate access package URL
        result = processor.upload_to_storage_streaming(
            mock_storage_client, data, config, mock_privacy_request
        )

        # Should return a valid access package URL
        assert result is not None
        assert "test-bucket" in result
        assert "test-data" in result
        assert result.startswith("https://")


# =============================================================================
# Retry Mechanism Tests
# =============================================================================


class TestRetryMechanism:
    """Test retry mechanisms for transient failures."""

    def test_streaming_function_retry_on_storage_failure(self, mock_sleep):
        """Test that streaming functions retry on storage failures."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.side_effect = [
            TransientError("Storage temporarily unavailable"),  # First call fails
            None,  # Second call succeeds
        ]
        processor = StreamingStorage(mock_storage_client)

        data = {"users": [{"id": 1, "name": "User 1"}]}
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-data",
            resp_format=ResponseFormat.csv,
        )
        mock_privacy_request = Mock()

        # Mock the _collect_and_validate_attachments function
        with patch.object(
            processor, "_collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = []  # No attachments

            result = processor.upload_to_storage_streaming(
                mock_storage_client, data, config, mock_privacy_request
            )

            # Should have retried and succeeded
            assert mock_storage_client.put_object.call_count == 2
            assert result is not None


# =============================================================================
# Helper Method Tests
# =============================================================================


class TestHelperMethods:
    """Test the new helper methods for cleaner code organization."""

    def test_yield_data_files(self):
        """Test _yield_data_files method."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        data = {
            "users": [{"id": 1, "name": "User 1"}],
            "items": [{"id": 1, "name": "Item 1"}],
        }

        # Test with JSON format
        generator = processor._yield_data_files(data, "json")
        files = list(generator)

        assert len(files) == 2
        assert files[0][0] == "users.json"  # filename
        assert files[1][0] == "items.json"  # filename

        # Check stream_zip format: (filename, datetime, mode, method, content_iter)
        for file_info in files:
            filename, dt, mode, method, content_iter = file_info
            assert isinstance(dt, datetime)
            assert mode == 0o644
            # _ZIP_32_TYPE() is a compression method object, not callable
            assert "ZIP_32_TYPE" in str(type(method))  # method should be _ZIP_32_TYPE
            assert hasattr(content_iter, "__iter__")  # content_iter should be iterable

    def test_yield_attachments(self):
        """Test _yield_attachments method."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Create mock attachments
        attachments = []
        for i in range(3):
            attachment = AttachmentInfo(
                storage_key=f"https://example.com/file{i}.pdf",
                file_name=f"file{i}.pdf",
                size=1000 + i * 100,
            )
            processing_info = AttachmentProcessingInfo(
                attachment=attachment, base_path=f"attachments/{i+1}", item={"id": i}
            )
            attachments.append(processing_info)

        # Test with batch size 2
        generator = processor._yield_attachments(
            attachments, mock_storage_client, "test-bucket", 2
        )
        files = list(generator)

        assert len(files) == 3
        assert all(
            f[0].startswith("file") for f in files
        )  # All filenames start with "file"

    def test_yield_single_attachment_url(self):
        """Test _yield_single_attachment method with URL attachments."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        attachment = AttachmentInfo(
            storage_key="https://example.com/test.pdf", file_name="test.pdf", size=5000
        )
        processing_info = AttachmentProcessingInfo(
            attachment=attachment, base_path="attachments/1", item={"id": 1}
        )

        # Test URL attachment (should create streaming generator)
        generator = processor._yield_single_attachment(
            processing_info, 1, mock_storage_client, "test-bucket"
        )
        files = list(generator)

        assert len(files) == 1
        filename, dt, mode, method, content_iter = files[0]
        assert filename == "test.pdf"
        assert mode == 0o644
        assert hasattr(content_iter, "__iter__")  # Should be iterable

    def test_yield_single_attachment_storage(self):
        """Test _yield_single_attachment method with storage-based attachments."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.return_value = b"test content"
        processor = StreamingStorage(mock_storage_client)

        attachment = AttachmentInfo(
            storage_key="storage_key_123", file_name="test.txt", size=100
        )
        processing_info = AttachmentProcessingInfo(
            attachment=attachment, base_path="users/1/attachments", item={"id": 1}
        )

        # Test storage attachment (should download and yield content)
        generator = processor._yield_single_attachment(
            processing_info, 1, mock_storage_client, "test-bucket"
        )
        files = list(generator)

        assert len(files) == 1
        filename, dt, mode, method, content_iter = files[0]
        assert filename == "test.txt"
        assert mode == 0o644

        # Verify storage client was called
        mock_storage_client.get_object.assert_called_once_with(
            "test-bucket", "storage_key_123"
        )

    def test_create_url_stream(self):
        """Test _create_url_stream method creates a lazy generator."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        url = "https://example.com/test.pdf"

        # This should return a generator, not a callable function
        stream_generator = processor._create_url_stream(url)

        # Should be iterable (returns a generator)
        assert hasattr(stream_generator, "__iter__")

        # Should not have made any HTTP requests yet
        # (We can't easily test this without mocking requests, but the key point
        # is that it returns a generator, not executes the request)

    def test_streaming_behavior_no_downloading(self):
        """Test that URL attachments create lazy generators without downloading."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Create attachment with URL
        attachment = AttachmentInfo(
            storage_key="https://example.com/large_file.pdf",
            file_name="large_file.pdf",
            size=1000000,  # 1MB file
        )
        processing_info = AttachmentProcessingInfo(
            attachment=attachment, base_path="attachments/1", item={"id": 1}
        )

        # This should NOT download the file, just create a generator
        generator = processor._yield_single_attachment(
            processing_info, 1, mock_storage_client, "test-bucket"
        )
        files = list(generator)

        assert len(files) == 1
        filename, dt, mode, method, content_iter = files[0]

        # The content_iter should be iterable, not necessarily callable
        assert hasattr(content_iter, "__iter__")

        # No HTTP requests should have been made yet
        # The generator is lazy and only executes when called by stream_zip

    def test_mixed_attachment_types(self):
        """Test handling of both URL and storage-based attachments."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.return_value = b"storage content"
        processor = StreamingStorage(mock_storage_client)

        attachments = []

        # URL-based attachment
        url_attachment = AttachmentInfo(
            storage_key="https://example.com/url_file.pdf",
            file_name="url_file.pdf",
            size=5000,
        )
        url_processing_info = AttachmentProcessingInfo(
            attachment=url_attachment, base_path="attachments/1", item={"id": 1}
        )
        attachments.append(url_processing_info)

        # Storage-based attachment
        storage_attachment = AttachmentInfo(
            storage_key="storage_key_123", file_name="storage_file.txt", size=100
        )
        storage_processing_info = AttachmentProcessingInfo(
            attachment=storage_attachment,
            base_path="users/1/attachments",
            item={"id": 1},
        )
        attachments.append(storage_processing_info)

        # Process both types
        generator = processor._yield_attachments(
            attachments, mock_storage_client, "test-bucket", 2
        )
        files = list(generator)

        assert len(files) == 2

        # Check URL attachment (should be iterable generator)
        url_file = next(f for f in files if f[0] == "url_file.pdf")
        assert hasattr(url_file[4], "__iter__")  # content_iter should be iterable

        # Check storage attachment (should have actual content)
        storage_file = next(f for f in files if f[0] == "storage_file.txt")
        assert list(storage_file[4]) == [
            b"storage content"
        ]  # content_iter should yield content

        # Verify storage client was only called for storage attachment
        mock_storage_client.get_object.assert_called_once_with(
            "test-bucket", "storage_key_123"
        )

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

    def test_collect_attachments_task_based_structure(self):
        """Test _collect_attachments method with task-based attachment structure."""
        mock_storage_client = create_autospec(CloudStorageClient)
        processor = StreamingStorage(mock_storage_client)

        # Data structure similar to real manualtask:manual_data format
        data = {
            "postgres_example_test_dataset:customer": [
                {"email": "jane@example.com", "name": "Jane Customer", "id": 3}
            ],
            "manualtask:manual_data": [
                {
                    "access_task": {
                        "test_file_pdf.pdf": {
                            "url": "https://fides-data-test-ethyca-demos.s3.amazonaws.com/att_a944763b-6453-4546-899a-8a7cead22418/test_file_pdf.pdf",
                            "size": "11.0 KB",
                            "content_type": "application/pdf",
                        },
                        "test_file_text.txt": {
                            "url": "https://fides-data-test-ethyca-demos.s3.amazonaws.com/att_bdaaed43-e49d-4921-aa7a-d4875afb34ba/test_file_text.txt",
                            "size": "5.0 KB",
                            "content_type": "text/plain",
                        },
                    },
                    "erasure_task": {
                        "deletion_log.csv": {
                            "url": "https://example.com/deletion_log.csv",
                            "size": "2.0 KB",
                            "content_type": "text/csv",
                        }
                    },
                }
            ],
        }

        raw_attachments = processor._collect_attachments(data)
        assert len(raw_attachments) == 3

        # Check PDF attachment from access_task
        pdf_attachment = next(
            a
            for a in raw_attachments
            if a["attachment"]["file_name"] == "test_file_pdf.pdf"
        )
        assert pdf_attachment["type"] == "nested"
        assert pdf_attachment["base_path"] == "manualtask:manual_data/1/access_task"
        assert (
            pdf_attachment["attachment"]["storage_key"]
            == "https://fides-data-test-ethyca-demos.s3.amazonaws.com/att_a944763b-6453-4546-899a-8a7cead22418/test_file_pdf.pdf"
        )
        assert pdf_attachment["attachment"]["content_type"] == "application/pdf"

        # Check text file attachment from access_task
        txt_attachment = next(
            a
            for a in raw_attachments
            if a["attachment"]["file_name"] == "test_file_text.txt"
        )
        assert txt_attachment["type"] == "nested"
        assert txt_attachment["base_path"] == "manualtask:manual_data/1/access_task"
        assert (
            txt_attachment["attachment"]["storage_key"]
            == "https://fides-data-test-ethyca-demos.s3.amazonaws.com/att_bdaaed43-e49d-4921-aa7a-d4875afb34ba/test_file_text.txt"
        )
        assert txt_attachment["attachment"]["content_type"] == "text/plain"

        # Check CSV attachment from erasure_task
        csv_attachment = next(
            a
            for a in raw_attachments
            if a["attachment"]["file_name"] == "deletion_log.csv"
        )
        assert csv_attachment["type"] == "nested"
        assert csv_attachment["base_path"] == "manualtask:manual_data/1/erasure_task"
        assert (
            csv_attachment["attachment"]["storage_key"]
            == "https://example.com/deletion_log.csv"
        )
        assert csv_attachment["attachment"]["content_type"] == "text/csv"

        # Verify no regular attachments were found (since we don't have standard "attachments" keys)
        assert not any(a["type"] == "direct" for a in raw_attachments)

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

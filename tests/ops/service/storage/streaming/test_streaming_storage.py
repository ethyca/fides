"""Tests for the streaming storage implementation.

These tests verify that the streaming storage correctly implements true streaming
using stream_zip for efficient ZIP creation without memory accumulation.
"""

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
from fides.api.service.storage.streaming.streaming_storage import (
    _collect_and_validate_attachments,
    _download_attachment_parallel,
    _handle_package_splitting,
    build_attachments_list,
    split_data_into_packages,
    stream_attachments_to_storage_zip,
    stream_attachments_to_storage_zip_memory_efficient,
    upload_to_storage_streaming,
)
from fides.api.service.storage.streaming.util import should_split_package


class TestStreamingStorage:
    """Test the streaming storage implementation."""

    def test_split_data_into_packages(self):
        """Test data package splitting logic."""
        # Test data with multiple items and attachments
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}]
                    * 50,  # 50 attachments
                },
                {
                    "id": 2,
                    "name": "User 2",
                    "attachments": [{"storage_key": "key2", "size": 2000}]
                    * 75,  # 75 attachments
                },
            ]
        }

        # Default config allows 100 attachments per package
        packages = split_data_into_packages(data)

        # Should split into 2 packages since User 2 has 75 attachments
        # The logic uses best-fit decreasing algorithm: sorts by attachment count (largest first)
        assert len(packages) == 2

        # First package should contain User 2 (75 attachments) - largest first
        assert "users" in packages[0]
        assert len(packages[0]["users"]) == 1
        assert packages[0]["users"][0]["id"] == 2

        # Second package should contain User 1 (50 attachments) - smaller second
        assert "users" in packages[1]
        assert len(packages[1]["users"]) == 1
        assert packages[1]["users"][0]["id"] == 1

    def test_split_data_into_packages_with_large_attachments(self):
        """Test package splitting with items that exceed the attachment limit."""
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(150)
                    ],  # 150 attachments (exceeds default 100 limit)
                }
            ]
        }

        packages = split_data_into_packages(data)

        # Should split into 2 packages: 100 + 50 attachments
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

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}]
                    * 25,  # 25 attachments
                },
                {
                    "id": 2,
                    "name": "User 2",
                    "attachments": [{"storage_key": "key2", "size": 2000}]
                    * 30,  # 30 attachments
                },
            ]
        }

        # Custom config with 40 attachments per package
        config = PackageSplitConfig(max_attachments=40)
        packages = split_data_into_packages(data, config)

        # Should fit in 1 package since 25 + 30 = 55 <= 40 (but we split by item)
        assert len(packages) == 2

    def test_split_data_into_packages_empty_data(self):
        """Test package splitting with empty data."""
        data = {}
        packages = split_data_into_packages(data)
        assert packages == []

    def test_split_data_into_packages_no_attachments(self):
        """Test package splitting with data that has no attachments."""
        data = {
            "users": [
                {"id": 1, "name": "User 1", "attachments": []},
                {"id": 2, "name": "User 2", "attachments": []},
            ]
        }

        packages = split_data_into_packages(data)
        assert len(packages) == 1  # Should fit in one package

    def test_split_data_into_packages_with_non_list_values(self):
        """Test package splitting with non-list values in data."""
        data = {
            "users": "not_a_list",
            "products": [
                {"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}
            ],
        }

        packages = split_data_into_packages(data)
        # Should only process the products list, ignore non-list users
        assert len(packages) == 1
        assert "products" in packages[0]

    def test_split_data_into_packages_with_empty_lists(self):
        """Test package splitting with empty lists in data."""
        data = {
            "users": [],
            "products": [
                {"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}
            ],
        }

        packages = split_data_into_packages(data)
        # Should only process the products list, ignore empty users list
        assert len(packages) == 1
        assert "products" in packages[0]

    def test_should_split_package(self):
        """Test package splitting decision logic."""
        # Test data that should trigger splitting
        large_data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(150)
                    ],  # 150 attachments
                }
            ]
        }

        assert should_split_package(large_data) is True

        # Test data that should not trigger splitting
        small_data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}]
                    * 50,  # 50 attachments
                }
            ]
        }

        assert should_split_package(small_data) is False

    def test_build_attachments_list_basic(self):
        """Test basic functionality of build_attachments_list."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": "key1", "size": 1000},
                        {"storage_key": "key2", "size": 2000},
                    ],
                },
                {
                    "id": 2,
                    "name": "User 2",
                    "attachments": [
                        {"storage_key": "key3", "size": 3000},
                    ],
                },
            ]
        }

        config = PackageSplitConfig(max_attachments=100)
        result = build_attachments_list(data, config)

        # Should return 2 items: (key, item, attachment_count)
        assert len(result) == 2

        # First item: users, User 1, 2 attachments
        assert result[0][0] == "users"  # key
        assert result[0][1]["id"] == 1  # item
        assert result[0][2] == 2  # attachment_count

        # Second item: users, User 2, 1 attachment
        assert result[1][0] == "users"  # key
        assert result[1][1]["id"] == 2  # item
        assert result[1][2] == 1  # attachment_count

    def test_build_attachments_list_with_splitting(self):
        """Test build_attachments_list when items exceed max_attachments limit."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(150)
                    ],  # 150 attachments
                }
            ]
        }

        config = PackageSplitConfig(
            max_attachments=50
        )  # Small limit to force splitting
        result = build_attachments_list(data, config)

        # Should split into 3 items: 50 + 50 + 50 attachments
        assert len(result) == 3

        # All items should have the same key and base item data
        for key, item, count in result:
            assert key == "users"
            assert item["id"] == 1
            assert item["name"] == "User 1"
            assert count == 50  # Each split should have 50 attachments

        # Verify the attachments are properly split
        all_attachments = []
        for _, item, _ in result:
            all_attachments.extend(item["attachments"])

        # Should have all 150 original attachments
        assert len(all_attachments) == 150
        # Should have unique storage keys
        storage_keys = [att["storage_key"] for att in all_attachments]
        assert len(set(storage_keys)) == 150

    def test_build_attachments_list_empty_data(self):
        """Test build_attachments_list with empty data."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        data = {}
        config = PackageSplitConfig()
        result = build_attachments_list(data, config)

        assert result == []

    def test_build_attachments_list_no_attachments(self):
        """Test build_attachments_list with data that has no attachments."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        data = {
            "users": [
                {"id": 1, "name": "User 1", "attachments": []},
                {"id": 2, "name": "User 2", "attachments": []},
            ]
        }

        config = PackageSplitConfig()
        result = build_attachments_list(data, config)

        # Should return 2 items with 0 attachments each
        assert len(result) == 2
        assert result[0][2] == 0  # attachment_count for first item
        assert result[1][2] == 0  # attachment_count for second item

    def test_build_attachments_list_non_list_values(self):
        """Test build_attachments_list with non-list values in data."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        data = {
            "users": "not_a_list",
            "products": [
                {"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}
            ],
        }

        config = PackageSplitConfig()
        result = build_attachments_list(data, config)

        # Should only process the products list, ignore non-list users
        assert len(result) == 1
        assert result[0][0] == "products"  # key
        assert result[0][1]["id"] == 1  # item
        assert result[0][2] == 1  # attachment_count

    def test_build_attachments_list_empty_lists(self):
        """Test build_attachments_list with empty lists in data."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        data = {
            "users": [],
            "products": [
                {"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}
            ],
        }

        config = PackageSplitConfig()
        result = build_attachments_list(data, config)

        # Should only process the products list, ignore empty users list
        assert len(result) == 1
        assert result[0][0] == "products"  # key
        assert result[0][1]["id"] == 1  # item
        assert result[0][2] == 1  # attachment_count

    def test_build_attachments_list_mixed_data_types(self):
        """Test build_attachments_list with mixed data types and edge cases."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}],
                },
                {"id": 2, "name": "User 2"},  # No attachments key
                {"id": 3, "name": "User 3", "attachments": None},  # None attachments
            ],
            "products": [
                {"id": 1, "attachments": [{"storage_key": "key2", "size": 2000}]},
            ],
        }

        config = PackageSplitConfig()
        result = build_attachments_list(data, config)

        # Should handle missing attachments gracefully
        assert len(result) == 4

        # Check that items without attachments get 0 count
        user_without_attachments = next(
            item for _, item, _ in result if item["id"] == 2
        )
        user_with_none_attachments = next(
            item for _, item, _ in result if item["id"] == 3
        )

        # Find their counts in the result
        user2_count = next(count for _, item, count in result if item["id"] == 2)
        user3_count = next(count for _, item, count in result if item["id"] == 3)

        assert user2_count == 0  # No attachments key
        assert user3_count == 0  # None attachments

    def test_collect_and_validate_attachments(self):
        """Test the _collect_and_validate_attachments helper function."""
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"storage_key": "key1", "size": 1000, "file_name": "file1.txt"},
                        {"storage_key": "key2", "size": 2000, "file_name": "file2.txt"},
                    ],
                }
            ]
        }

        attachments = _collect_and_validate_attachments(data)

        assert len(attachments) == 2

        # Check first attachment
        assert attachments[0].attachment.storage_key == "key1"
        assert attachments[0].attachment.file_name == "file1.txt"
        assert attachments[0].base_path == "users/1/attachments"
        assert attachments[0].item["id"] == 1

    def test_collect_and_validate_attachments_missing_storage_key(self):
        """Test _collect_and_validate_attachments with missing storage_key."""
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"size": 1000, "file_name": "file1.txt"}  # Missing storage_key
                    ],
                }
            ]
        }

        attachments = _collect_and_validate_attachments(data)

        assert len(attachments) == 0

    def test_collect_and_validate_attachments_invalid_attachment_data(self):
        """Test _collect_and_validate_attachments with invalid attachment data."""
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"storage_key": None, "size": "invalid_size"}  # Invalid data
                    ],
                }
            ]
        }

        attachments = _collect_and_validate_attachments(data)

        assert len(attachments) == 0

    def test_collect_and_validate_attachments_non_dict_items(self):
        """Test _collect_and_validate_attachments with non-dict items."""
        data = {
            "users": [
                "not_a_dict",  # Non-dict item
                {"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]},
            ]
        }

        attachments = _collect_and_validate_attachments(data)

        # Should process the valid item and skip the invalid one
        assert len(attachments) == 1

    def test_collect_and_validate_attachments_with_mock_objects(self):
        """Test _collect_and_validate_attachments with mock objects."""
        # Create a mock item that will cause errors
        mock_item = Mock()
        mock_item.get.side_effect = AttributeError("Mock error")

        data = {"users": [mock_item]}

        attachments = _collect_and_validate_attachments(data)

        assert len(attachments) == 0

    def test_collect_and_validate_attachments_non_iterable_values(self):
        """Test _collect_and_validate_attachments with values that cause exceptions during processing."""
        # Create a mock object that will raise an exception when len() is called
        mock_value = Mock()
        mock_value.__iter__ = Mock(return_value=Mock())
        mock_value.__len__ = Mock(side_effect=TypeError("Cannot get length"))

        data = {"users": mock_value}

        attachments = _collect_and_validate_attachments(data)

        assert len(attachments) == 0

    def test_collect_and_validate_attachments_values_that_cause_exceptions(self):
        """Test _collect_and_validate_attachments with values that cause exceptions during processing."""
        # Create a mock object that has __iter__ and __len__ but raises an exception when iterated
        mock_value = Mock()
        mock_value.__iter__ = Mock(return_value=Mock())
        mock_value.__len__ = Mock(return_value=1)
        # The iterator itself will raise an exception when accessed
        mock_iterator = Mock()
        mock_iterator.__next__ = Mock(side_effect=TypeError("Iterator error"))
        mock_value.__iter__ = Mock(return_value=mock_iterator)

        data = {"users": mock_value}

        attachments = _collect_and_validate_attachments(data)

        assert len(attachments) == 0

    def test_download_attachment_parallel(self):
        """Test the _download_attachment_parallel helper function."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.return_value = b"test file content"

        attachment = AttachmentInfo(
            storage_key="test-key", size=1000, file_name="test.txt"
        )

        filename, content = _download_attachment_parallel(
            mock_storage_client, "test-bucket", attachment
        )

        assert filename == "test.txt"
        assert content == b"test file content"
        mock_storage_client.get_object.assert_called_once_with(
            "test-bucket", "test-key"
        )

    def test_download_attachment_parallel_no_filename(self):
        """Test _download_attachment_parallel with attachment that has no filename."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.return_value = b"test file content"

        attachment = AttachmentInfo(storage_key="test-key", size=1000, file_name=None)

        filename, content = _download_attachment_parallel(
            mock_storage_client, "test-bucket", attachment
        )

        assert filename == "attachment"  # Default filename
        assert content == b"test file content"

    def test_download_attachment_parallel_download_failure(self):
        """Test _download_attachment_parallel when download fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.side_effect = Exception("Download failed")

        attachment = AttachmentInfo(
            storage_key="test-key", size=1000, file_name="test.txt"
        )

        with pytest.raises(
            StorageUploadError, match="Failed to download attachment test.txt"
        ):
            _download_attachment_parallel(
                mock_storage_client, "test-bucket", attachment
            )

    def test_download_attachment_parallel_transient_error(self):
        """Test _download_attachment_parallel with transient error raises TransientError."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.side_effect = Exception("Connection timeout")

        attachment = AttachmentInfo(
            storage_key="test-key", size=1000, file_name="test.txt"
        )

        with pytest.raises(
            TransientError, match="Transient error downloading attachment test.txt"
        ):
            _download_attachment_parallel(
                mock_storage_client, "test-bucket", attachment
            )

    def test_download_attachment_parallel_permanent_error(self):
        """Test _download_attachment_parallel with permanent error raises PermanentError."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.side_effect = ValueError("Invalid configuration")

        attachment = AttachmentInfo(
            storage_key="test-key", size=1000, file_name="test.txt"
        )

        with pytest.raises(
            PermanentError, match="Configuration error downloading attachment test.txt"
        ):
            _download_attachment_parallel(
                mock_storage_client, "test-bucket", attachment
            )

    def test_handle_package_splitting(self):
        """Test the _handle_package_splitting helper function."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()

        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(150)
                    ],
                }
            ]
        }

        # Mock the stream_attachments_to_storage_zip function
        with (
            patch(
                "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
            ) as mock_stream,
        ):

            _handle_package_splitting(
                data,
                "test-key",
                mock_storage_client,
                "test-bucket",
                mock_privacy_request,
                2,
                StreamingBufferConfig(),
            )

            # Should call stream_attachments_to_storage_zip for each package
            assert mock_stream.call_count == 2  # Split into 2 packages

    def test_stream_attachments_to_storage_zip(self):
        """Test the streaming ZIP approach using stream_zip with parallel processing."""
        # Mock storage client with proper put_object method
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()

        # Mock privacy request
        mock_privacy_request = Mock()

        # Test data with attachments
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}],
                }
            ]
        }

        # Mock attachment info
        mock_attachment = Mock()
        mock_attachment.file_name = "test.txt"
        mock_attachment.storage_key = "key1"
        mock_attachment.size = 1000

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            # Create proper autospec object with the correct structure
            mock_processing_info = create_autospec(AttachmentProcessingInfo)
            mock_processing_info.attachment = mock_attachment
            mock_processing_info.base_path = "users"
            mock_processing_info.item = data["users"][0]

            mock_collect.return_value = [mock_processing_info]

            # Mock get_object to return test content
            mock_storage_client.get_object.return_value = b"test file content"

            # Call the function
            stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
            )

            # Verify put_object was called with stream_zip
            mock_storage_client.put_object.assert_called_once()
            call_args = mock_storage_client.put_object.call_args
            assert call_args[0][0] == "test-bucket"  # bucket
            assert call_args[0][1] == "test-key.zip"  # key
            assert call_args[1]["content_type"] == "application/zip"

            # The third argument should be a generator from stream_zip
            zip_generator = call_args[0][2]
            # Verify it's a generator (we can't easily test the exact content without more complex mocking)
            assert hasattr(zip_generator, "__iter__")

    def test_stream_attachments_to_storage_zip_no_attachments(self):
        """Test streaming ZIP creation with no attachments."""
        # Mock storage client with proper put_object method
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()

        # Mock privacy request
        mock_privacy_request = Mock()

        # Test data with no attachments
        data = {"users": [{"id": 1, "name": "User 1", "attachments": []}]}

        # Mock the _collect_and_validate_attachments function to return empty list
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = []

            # Call the function
            stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
            )

            # Verify put_object was called (for ZIP with just data files)
            mock_storage_client.put_object.assert_called_once()

    def test_stream_attachments_to_storage_zip_with_package_splitting(self):
        """Test streaming ZIP creation when package splitting is triggered."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()

        # Data that will trigger package splitting
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(150)
                    ],
                }
            ]
        }

        # Mock the _handle_package_splitting function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._handle_package_splitting"
        ) as mock_handle:

            stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
            )

            # Should call package splitting instead of direct processing
            mock_handle.assert_called_once()

    def test_stream_attachments_to_storage_zip_creation_failure(self):
        """Test streaming ZIP creation when ZIP creation fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.side_effect = Exception("ZIP creation failed")
        mock_privacy_request = Mock()

        data = {
            "users": [{"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}]
        }

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            # Create proper autospec object with the correct structure
            mock_processing_info = create_autospec(AttachmentProcessingInfo)
            mock_processing_info.attachment = create_autospec(AttachmentInfo)
            mock_processing_info.attachment.file_name = "file1.txt"
            mock_processing_info.attachment.storage_key = "key1"
            mock_processing_info.attachment.size = 1000
            mock_processing_info.base_path = "users"
            mock_processing_info.item = data["users"][0]

            mock_collect.return_value = [mock_processing_info]

            mock_storage_client.get_object.return_value = b"test content"

            with pytest.raises(
                StorageUploadError,
                match="Failed to create controlled streaming ZIP file",
            ):
                stream_attachments_to_storage_zip(
                    mock_storage_client,
                    "test-bucket",
                    "test-key.zip",
                    data,
                    mock_privacy_request,
                    max_workers=2,
                )

    def test_upload_to_storage_streaming_csv_format(self):
        """Test the main upload function with CSV format."""
        # Mock storage client with proper put_object method
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()
        mock_storage_client.generate_presigned_url.return_value = (
            "https://example.com/test.zip"
        )

        # Mock privacy request
        mock_privacy_request = Mock()

        # Test data
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}],
                }
            ]
        }

        # Mock attachment info
        mock_attachment = Mock()
        mock_attachment.file_name = "test.txt"
        mock_attachment.storage_key = "key1"
        mock_attachment.size = 1000

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            # Create proper autospec object with the correct structure
            mock_processing_info = create_autospec(AttachmentProcessingInfo)
            mock_processing_info.attachment = mock_attachment
            mock_processing_info.base_path = "users"
            mock_processing_info.item = data["users"][0]

            mock_collect.return_value = [mock_processing_info]

            # Mock get_object to return test content
            mock_storage_client.get_object.return_value = b"test file content"

            # Create config
            config = StorageUploadConfig(
                bucket_name="test-bucket",
                file_key="test-key.zip",
                resp_format=ResponseFormat.csv.value,
                max_workers=2,
            )

            # Call the function
            url = upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                mock_privacy_request,
                None,  # no document
                None,  # no progress callback
                StreamingBufferConfig(),
            )

            # Verify results
            assert url == "https://example.com/test.zip"

    def test_upload_to_storage_streaming_json_format(self):
        """Test the main upload function with JSON format."""
        # Mock storage client with proper put_object method
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()
        mock_storage_client.generate_presigned_url.return_value = (
            "https://example.com/test.zip"
        )

        # Mock privacy request
        mock_privacy_request = Mock()

        # Test data
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"storage_key": "key1", "size": 1000}],
                }
            ]
        }

        # Mock attachment info
        mock_attachment = Mock()
        mock_attachment.file_name = "test.txt"
        mock_attachment.storage_key = "key1"
        mock_attachment.size = 1000

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            # Create proper autospec object with the correct structure
            mock_processing_info = create_autospec(AttachmentProcessingInfo)
            mock_processing_info.attachment = mock_attachment
            mock_processing_info.base_path = "users"
            mock_processing_info.item = data["users"][0]

            mock_collect.return_value = [mock_processing_info]

            # Mock get_object to return test content
            mock_storage_client.get_object.return_value = b"test file content"

            # Create config
            config = StorageUploadConfig(
                bucket_name="test-bucket",
                file_key="test-key.zip",
                resp_format=ResponseFormat.json.value,
                max_workers=2,
            )

            # Call the function
            url = upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                mock_privacy_request,
                None,  # no document
                None,  # no progress callback
                StreamingBufferConfig(),
            )

            # Verify results
            assert url == "https://example.com/test.zip"

    def test_upload_to_storage_streaming_html_format(self):
        """Test the main upload function with HTML format."""
        # Mock storage client
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.generate_presigned_url.return_value = (
            "https://example.com/test.html"
        )

        # Mock privacy request
        mock_privacy_request = Mock()

        # Test data
        data = {"html_content": "<html>test</html>"}

        # Create config
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.html",
            resp_format=ResponseFormat.html.value,
            max_workers=2,
        )

        # Mock the HTML streaming function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_html_dsr_report_to_storage_multipart"
        ):

            # Call the function
            url = upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                mock_privacy_request,
                None,  # no document
                None,  # no progress callback
                StreamingBufferConfig(),
            )

            # Verify results
            assert url == "https://example.com/test.html"

    def test_upload_to_storage_streaming_unsupported_format(self):
        """Test the main upload function with unsupported format."""
        # Mock storage client
        mock_storage_client = create_autospec(CloudStorageClient)

        # Mock privacy request
        mock_privacy_request = Mock()

        # Test data
        data = {"test": "data"}

        # Create config with unsupported format
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.txt",
            resp_format="txt",  # unsupported
            max_workers=2,
        )

        # Call the function and expect StorageUploadError with the correct message
        with pytest.raises(
            StorageUploadError, match="Unexpected error during true streaming upload"
        ):
            upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                mock_privacy_request,
                None,  # no document
                None,  # no progress callback
                StreamingBufferConfig(),
            )

    def test_upload_to_storage_streaming_no_privacy_request(self):
        """Test the main upload function without privacy request."""
        # Mock storage client
        mock_storage_client = create_autospec(CloudStorageClient)

        # Test data
        data = {"test": "data"}

        # Create config
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        # Call the function without privacy request and expect ValueError
        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                None,  # no privacy request
                None,  # no document
                None,  # no progress callback
                StreamingBufferConfig(),
            )

    def test_upload_to_storage_streaming_document_only_not_implemented(self):
        """Test the main upload function with document-only upload (not implemented)."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = None
        mock_document = Mock()

        data = {"test": "data"}
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                mock_privacy_request,
                mock_document,
                None,
                StreamingBufferConfig(),
            )

    def test_upload_to_storage_streaming_presigned_url_generation_failure(self):
        """Test the main upload function when presigned URL generation fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()
        mock_storage_client.generate_presigned_url.side_effect = Exception(
            "URL generation failed"
        )

        mock_privacy_request = Mock()
        data = {
            "users": [{"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}]
        }

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        # Mock the stream_attachments_to_storage_zip function to succeed
        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip",
        ):
            url = upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                mock_privacy_request,
                None,
                None,
                StreamingBufferConfig(),
            )

            assert url is None

    def test_upload_to_storage_streaming_upload_failure(self):
        """Test the main upload function when upload fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()

        data = {
            "users": [{"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}]
        }

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        # Mock the stream_attachments_to_storage_zip_memory_efficient function to fail
        # (this is the default function called when use_memory_efficient=True)
        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip_memory_efficient",
            side_effect=Exception("Upload failed"),
        ):
            with pytest.raises(
                StorageUploadError,
                match="Unexpected error during true streaming upload: Upload failed",
            ):
                upload_to_storage_streaming(
                    mock_storage_client,
                    data,
                    config,
                    mock_privacy_request,
                    None,
                    None,
                    StreamingBufferConfig(),
                )

    def test_split_data_into_packages_edge_cases(self):
        """Test package splitting with various edge cases."""
        # Test with missing attachments key (should handle gracefully)
        data = {
            "users": [
                {"id": 1},  # Missing attachments key
                {"id": 2, "attachments": [{"storage_key": "key1", "size": 1000}]},
            ]
        }

        packages = split_data_into_packages(data)
        # Should handle missing attachments gracefully and only process valid attachments
        assert len(packages) == 1

        # Test with empty strings as keys
        data = {"": [{"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}]}

        packages = split_data_into_packages(data)
        assert len(packages) == 1
        assert "" in packages[0]

        # Test with very large attachment counts
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(1000)
                    ],
                }
            ]
        }

        packages = split_data_into_packages(data)
        # Should split into 10 packages (1000 / 100)
        assert len(packages) == 10
        for package in packages:
            assert "users" in package
            assert len(package["users"]) == 1
            assert len(package["users"][0]["attachments"]) <= 100

    def test_stream_attachments_to_storage_zip_memory_efficient(self):
        """Test the memory-efficient streaming ZIP approach with batch processing."""
        # Mock storage client with proper put_object method
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()

        # Mock privacy request
        mock_privacy_request = Mock()

        # Test data with multiple attachments
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(25)
                    ],  # 25 attachments
                }
            ]
        }

        # Mock attachment info
        mock_attachments = []
        for i in range(25):
            mock_attachment = Mock()
            mock_attachment.file_name = f"test{i}.txt"
            mock_attachment.storage_key = f"key{i}"
            mock_attachment.size = 1000
            mock_attachments.append(mock_attachment)

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=mock_attachment, base_path="users", item=data["users"][0]
                )
                for mock_attachment in mock_attachments
            ]

            # Mock get_object to return test content
            mock_storage_client.get_object.return_value = b"test file content"

            # Call the memory-efficient function with batch size of 10
            stream_attachments_to_storage_zip_memory_efficient(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=3,
                batch_size=10,
            )

            # Verify put_object was called with stream_zip
            mock_storage_client.put_object.assert_called_once()
            call_args = mock_storage_client.put_object.call_args
            assert call_args[0][0] == "test-bucket"  # bucket
            assert call_args[0][1] == "test-key.zip"  # key
            assert call_args[1]["content_type"] == "application/zip"

            # The third argument should be a generator from stream_zip
            zip_generator = call_args[0][2]
            # Verify it's a generator (we can't easily test the exact content without more complex mocking)
            assert hasattr(zip_generator, "__iter__")

    def test_stream_attachments_to_storage_zip_memory_efficient_no_attachments(self):
        """Test memory-efficient streaming ZIP creation with no attachments."""
        # Mock storage client with proper put_object method
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()

        # Mock privacy request
        mock_privacy_request = Mock()

        # Test data with no attachments
        data = {"users": [{"id": 1, "name": "User 1", "attachments": []}]}

        # Mock the _collect_and_validate_attachments function to return empty list
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = []

            # Call the function
            stream_attachments_to_storage_zip_memory_efficient(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
                batch_size=10,
            )

            # Verify put_object was called (for ZIP with just data files)
            mock_storage_client.put_object.assert_called_once()

    def test_controlled_streaming_generator_sliding_window(self):
        """Test that the controlled streaming generator maintains proper sliding window concurrency."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()

        # Test data with many attachments to verify sliding window behavior
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(20)
                    ],  # 20 attachments
                }
            ]
        }

        # Mock attachment info
        mock_attachments = []
        for i in range(20):
            mock_attachment = Mock()
            mock_attachment.file_name = f"test{i}.txt"
            mock_attachment.storage_key = f"key{i}"
            mock_attachment.size = 1000
            mock_attachments.append(mock_attachment)

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=mock_attachment, base_path="users", item=data["users"][0]
                )
                for mock_attachment in mock_attachments
            ]

            # Mock get_object to return test content
            mock_storage_client.get_object.return_value = b"test file content"

            # Test with max_workers=3 to verify sliding window behavior
            stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=3,  # Only 3 workers
            )

            # Verify put_object was called with stream_zip
            mock_storage_client.put_object.assert_called_once()
            call_args = mock_storage_client.put_object.call_args
            assert call_args[0][0] == "test-bucket"  # bucket
            assert call_args[0][1] == "test-key.zip"  # key
            assert call_args[1]["content_type"] == "application/zip"

            # The third argument should be a generator from stream_zip
            zip_generator = call_args[0][2]
            assert hasattr(zip_generator, "__iter__")

    def test_memory_efficient_batch_controlled_concurrency(self):
        """Test that the memory-efficient version also uses controlled concurrency within batches."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()

        # Test data with many attachments
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"storage_key": f"key{x}", "size": 1000} for x in range(25)
                    ],  # 25 attachments
                }
            ]
        }

        # Mock attachment info
        mock_attachments = []
        for i in range(25):
            mock_attachment = Mock()
            mock_attachment.file_name = f"test{i}.txt"
            mock_attachment.storage_key = f"key{i}"
            mock_attachment.size = 1000
            mock_attachments.append(mock_attachment)

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=mock_attachment, base_path="users", item=data["users"][0]
                )
                for mock_attachment in mock_attachments
            ]

            # Mock get_object to return test content
            mock_storage_client.get_object.return_value = b"test file content"

            # Test with batch_size=10 and max_workers=3
            # This should create 3 batches: [10], [10], [5]
            stream_attachments_to_storage_zip_memory_efficient(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=3,
                batch_size=10,
            )

            # Verify put_object was called with stream_zip
            mock_storage_client.put_object.assert_called_once()
            call_args = mock_storage_client.put_object.call_args
            assert call_args[0][0] == "test-bucket"  # bucket
            assert call_args[0][1] == "test-key.zip"  # key
            assert call_args[1]["content_type"] == "application/zip"

            # The third argument should be a generator from stream_zip
            zip_generator = call_args[0][2]
            assert hasattr(zip_generator, "__iter__")

    def test_upload_to_storage_streaming_upload_failure_non_memory_efficient(self):
        """Test the main upload function when upload fails in non-memory-efficient mode."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()

        data = {
            "users": [{"id": 1, "attachments": [{"storage_key": "key1", "size": 1000}]}]
        }

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        # Mock the stream_attachments_to_storage_zip function to fail
        # (this is called when use_memory_efficient=False)
        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip",
            side_effect=Exception("Upload failed"),
        ):
            with pytest.raises(
                StorageUploadError,
                match="Unexpected error during true streaming upload: Upload failed",
            ):
                upload_to_storage_streaming(
                    mock_storage_client,
                    data,
                    config,
                    mock_privacy_request,
                    None,
                    StreamingBufferConfig(),
                    use_memory_efficient=False,  # Use non-memory-efficient path
                )


class TestStreamingStorageRetry:
    """Test retry functionality in streaming storage."""

    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_download_attachment_with_retry_success_after_failure(self, mock_sleep):
        """Test that download retries on transient errors and succeeds."""
        mock_storage_client = create_autospec(CloudStorageClient)

        # First call fails with transient error, second succeeds
        mock_storage_client.get_object.side_effect = [
            Exception("Connection timeout"),  # Transient error
            b"test file content",  # Success
        ]

        attachment = AttachmentInfo(
            storage_key="test-key", size=1000, file_name="test.txt"
        )

        filename, content = _download_attachment_parallel(
            mock_storage_client, "test-bucket", attachment
        )

        assert filename == "test.txt"
        assert content == b"test file content"

        # Should have been called twice (initial + 1 retry)
        assert mock_storage_client.get_object.call_count == 2
        mock_sleep.assert_called_once()  # Should sleep between retries

    @patch("time.sleep")
    def test_download_attachment_retry_permanent_error_no_retry(self, mock_sleep):
        """Test that permanent errors are not retried."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.side_effect = ValueError("Invalid configuration")

        attachment = AttachmentInfo(
            storage_key="test-key", size=1000, file_name="test.txt"
        )

        with pytest.raises(PermanentError):
            _download_attachment_parallel(
                mock_storage_client, "test-bucket", attachment
            )

        # Should only be called once (no retry for permanent errors)
        assert mock_storage_client.get_object.call_count == 1
        mock_sleep.assert_not_called()  # No sleep for permanent errors

    @patch("time.sleep")
    def test_download_attachment_max_retries_exceeded(self, mock_sleep):
        """Test that download fails after max retries are exceeded."""
        mock_storage_client = create_autospec(CloudStorageClient)

        # Always fail with transient error
        mock_storage_client.get_object.side_effect = Exception("Connection timeout")

        attachment = AttachmentInfo(
            storage_key="test-key", size=1000, file_name="test.txt"
        )

        with pytest.raises(TransientError):
            _download_attachment_parallel(
                mock_storage_client, "test-bucket", attachment
            )

        # Should be called max_retries + 1 times (3 retries + 1 initial = 4 total)
        assert mock_storage_client.get_object.call_count == 4
        # Should sleep 3 times (between retries)
        assert mock_sleep.call_count == 3

    @patch("time.sleep")
    def test_streaming_function_retry_on_storage_failure(self, mock_sleep):
        """Test that streaming functions retry on storage failures."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()

        # First call to put_object fails, second succeeds
        mock_storage_client.put_object.side_effect = [
            Exception("Service unavailable"),  # Transient error
            Mock(),  # Success
        ]
        mock_storage_client.generate_presigned_url.return_value = (
            "https://example.com/test.zip"
        )

        data = {
            "users": [{"id": 1, "attachments": []}]
        }  # No attachments for simplicity

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=1,
        )

        # Should succeed after retry
        url = upload_to_storage_streaming(
            mock_storage_client,
            data,
            config,
            mock_privacy_request,
        )

        assert url == "https://example.com/test.zip"
        # Should have been called twice (initial + 1 retry)
        assert mock_storage_client.put_object.call_count == 2
        mock_sleep.assert_called_once()

    def test_streaming_preserves_memory_efficiency(self):
        """Test that streaming still works efficiently without memory accumulation."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()
        mock_storage_client.generate_presigned_url.return_value = (
            "https://example.com/test.zip"
        )
        mock_privacy_request = Mock()

        # Large dataset that would cause memory issues if not streaming
        large_data = {
            "users": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "attachments": [{"storage_key": f"key{i}", "size": 1000}],
                }
                for i in range(100)  # 100 users with attachments
            ]
        }

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        # Mock the download to return content
        mock_storage_client.get_object.return_value = b"test content"

        # This should work without memory issues due to streaming
        url = upload_to_storage_streaming(
            mock_storage_client,
            large_data,
            config,
            mock_privacy_request,
        )

        assert url == "https://example.com/test.zip"
        # Verify put_object was called (streaming worked)
        mock_storage_client.put_object.assert_called_once()

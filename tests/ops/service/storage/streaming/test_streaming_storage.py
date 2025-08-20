"""Tests for the streaming storage implementation.

These tests verify that the streaming storage correctly implements true streaming
using stream_zip for efficient ZIP creation without memory accumulation.
"""

from unittest.mock import Mock, create_autospec, patch

import pytest

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    ProcessingMetrics,
    StorageUploadConfig,
    StreamingBufferConfig,
)
from fides.api.service.storage.streaming.streaming_storage import (
    _calculate_data_metrics,
    _collect_and_validate_attachments,
    _download_attachment_parallel,
    _handle_package_splitting,
    split_data_into_packages,
    stream_attachments_to_storage_zip,
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
                        {"s3_key": f"key{x}", "size": 1000} for x in range(150)
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
                    "attachments": [{"s3_key": "key1", "size": 1000}]
                    * 25,  # 25 attachments
                },
                {
                    "id": 2,
                    "name": "User 2",
                    "attachments": [{"s3_key": "key2", "size": 2000}]
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
            "products": [{"id": 1, "attachments": [{"s3_key": "key1", "size": 1000}]}],
        }

        packages = split_data_into_packages(data)
        # Should only process the products list, ignore non-list users
        assert len(packages) == 1
        assert "products" in packages[0]

    def test_split_data_into_packages_with_empty_lists(self):
        """Test package splitting with empty lists in data."""
        data = {
            "users": [],
            "products": [{"id": 1, "attachments": [{"s3_key": "key1", "size": 1000}]}],
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
                        {"s3_key": f"key{x}", "size": 1000} for x in range(150)
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
                    "attachments": [{"s3_key": "key1", "size": 1000}]
                    * 50,  # 50 attachments
                }
            ]
        }

        assert should_split_package(small_data) is False

    def test_calculate_data_metrics(self):
        """Test the _calculate_data_metrics helper function."""
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"s3_key": "key1", "size": 1000},
                        {"s3_key": "key2", "size": 2000},
                    ],
                },
                {"id": 2, "attachments": [{"s3_key": "key3", "size": 1500}]},
            ],
            "products": [{"id": 1, "attachments": [{"s3_key": "key4", "size": 3000}]}],
        }

        metrics = _calculate_data_metrics(data)

        assert metrics.total_attachments == 4
        assert metrics.total_bytes == 7500  # 1000 + 2000 + 1500 + 3000

    def test_calculate_data_metrics_with_mock_objects(self):
        """Test _calculate_data_metrics with mock objects that might cause errors."""
        # Create a mock object that will cause AttributeError when accessing attachments
        mock_item = Mock()
        mock_item.get.side_effect = AttributeError("Mock error")

        data = {"users": [mock_item]}

        metrics = _calculate_data_metrics(data)

        # Should handle the error gracefully and return empty metrics
        assert metrics.total_attachments == 0
        assert metrics.total_bytes == 0

    def test_calculate_data_metrics_with_non_iterable_values(self):
        """Test _calculate_data_metrics with non-iterable values."""
        data = {"users": "not_iterable", "count": 42}

        metrics = _calculate_data_metrics(data)

        # Should handle non-iterable values gracefully
        assert metrics.total_attachments == 0
        assert metrics.total_bytes == 0

    def test_collect_and_validate_attachments(self):
        """Test the _collect_and_validate_attachments helper function."""
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"s3_key": "key1", "size": 1000, "file_name": "file1.txt"},
                        {"s3_key": "key2", "size": 2000, "file_name": "file2.txt"},
                    ],
                }
            ]
        }

        metrics = ProcessingMetrics()
        attachments = _collect_and_validate_attachments(data, metrics)

        assert len(attachments) == 2
        assert len(metrics.errors) == 0

        # Check first attachment
        assert attachments[0].attachment.s3_key == "key1"
        assert attachments[0].attachment.file_name == "file1.txt"
        assert attachments[0].base_path == "users/1/attachments"
        assert attachments[0].item["id"] == 1

    def test_collect_and_validate_attachments_missing_s3_key(self):
        """Test _collect_and_validate_attachments with missing s3_key."""
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"size": 1000, "file_name": "file1.txt"}  # Missing s3_key
                    ],
                }
            ]
        }

        metrics = ProcessingMetrics()
        attachments = _collect_and_validate_attachments(data, metrics)

        assert len(attachments) == 0
        assert len(metrics.errors) == 1
        assert "missing required field 's3_key'" in metrics.errors[0]

    def test_collect_and_validate_attachments_invalid_attachment_data(self):
        """Test _collect_and_validate_attachments with invalid attachment data."""
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"s3_key": None, "size": "invalid_size"}  # Invalid data
                    ],
                }
            ]
        }

        metrics = ProcessingMetrics()
        attachments = _collect_and_validate_attachments(data, metrics)

        assert len(attachments) == 0
        assert len(metrics.errors) == 1
        assert "Invalid attachment data" in metrics.errors[0]

    def test_collect_and_validate_attachments_non_dict_items(self):
        """Test _collect_and_validate_attachments with non-dict items."""
        data = {
            "users": [
                "not_a_dict",  # Non-dict item
                {"id": 1, "attachments": [{"s3_key": "key1", "size": 1000}]},
            ]
        }

        metrics = ProcessingMetrics()
        attachments = _collect_and_validate_attachments(data, metrics)

        # Should process the valid item and skip the invalid one
        assert len(attachments) == 1
        assert len(metrics.errors) == 1
        assert "not a dict-like object" in metrics.errors[0]

    def test_collect_and_validate_attachments_with_mock_objects(self):
        """Test _collect_and_validate_attachments with mock objects."""
        # Create a mock item that will cause errors
        mock_item = Mock()
        mock_item.get.side_effect = AttributeError("Mock error")

        data = {"users": [mock_item]}

        metrics = ProcessingMetrics()
        attachments = _collect_and_validate_attachments(data, metrics)

        assert len(attachments) == 0
        assert len(metrics.errors) == 1
        assert "Failed to process item" in metrics.errors[0]

    def test_collect_and_validate_attachments_non_iterable_values(self):
        """Test _collect_and_validate_attachments with non-iterable values."""
        data = {"users": "not_iterable"}

        metrics = ProcessingMetrics()
        attachments = _collect_and_validate_attachments(data, metrics)

        assert len(attachments) == 0
        assert len(metrics.errors) == 1
        assert "Failed to process value" in metrics.errors[0]

    def test_download_attachment_parallel(self):
        """Test the _download_attachment_parallel helper function."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.return_value = b"test file content"

        attachment = AttachmentInfo(s3_key="test-key", size=1000, file_name="test.txt")

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

        attachment = AttachmentInfo(s3_key="test-key", size=1000, file_name=None)

        filename, content = _download_attachment_parallel(
            mock_storage_client, "test-bucket", attachment
        )

        assert filename == "attachment"  # Default filename
        assert content == b"test file content"

    def test_download_attachment_parallel_download_failure(self):
        """Test _download_attachment_parallel when download fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.get_object.side_effect = Exception("Download failed")

        attachment = AttachmentInfo(s3_key="test-key", size=1000, file_name="test.txt")

        with pytest.raises(
            StorageUploadError, match="Failed to download attachment test.txt"
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
                        {"s3_key": f"key{x}", "size": 1000} for x in range(150)
                    ],
                }
            ]
        }

        # Mock the stream_attachments_to_storage_zip function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
        ) as mock_stream:
            mock_metrics = ProcessingMetrics(
                total_attachments=150,
                processed_attachments=100,
                total_bytes=150000,
                processed_bytes=100000,
            )
            mock_stream.return_value = mock_metrics

            metrics = _handle_package_splitting(
                data,
                "test-key",
                mock_storage_client,
                "test-bucket",
                mock_privacy_request,
                2,
                None,
                StreamingBufferConfig(),
            )

            # Should call stream_attachments_to_storage_zip for each package
            assert mock_stream.call_count == 2  # Split into 2 packages

            # Metrics should be combined
            assert metrics.total_attachments == 150
            assert metrics.processed_attachments == 200  # 100 * 2 packages
            assert metrics.processed_bytes == 200000  # 100000 * 2 packages

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
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        # Mock attachment info
        mock_attachment = Mock()
        mock_attachment.file_name = "test.txt"
        mock_attachment.s3_key = "key1"
        mock_attachment.size = 1000

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=mock_attachment, base_path="users", item=data["users"][0]
                )
            ]

            # Mock get_object to return test content
            mock_storage_client.get_object.return_value = b"test file content"

            # Call the function
            metrics = stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
            )

            # Verify metrics
            assert metrics.processed_attachments == 1
            assert metrics.processed_bytes == 1000

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
            metrics = stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
            )

            # Verify metrics
            assert metrics.processed_attachments == 0
            assert metrics.processed_bytes == 0

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
                        {"s3_key": f"key{x}", "size": 1000} for x in range(150)
                    ],
                }
            ]
        }

        # Mock the _handle_package_splitting function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._handle_package_splitting"
        ) as mock_handle:
            mock_metrics = ProcessingMetrics(
                total_attachments=150,
                processed_attachments=150,
                total_bytes=150000,
                processed_bytes=150000,
            )
            mock_handle.return_value = mock_metrics

            metrics = stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
            )

            # Should call package splitting instead of direct processing
            mock_handle.assert_called_once()
            assert metrics == mock_metrics

    def test_stream_attachments_to_storage_zip_download_failure(self):
        """Test streaming ZIP creation when some downloads fail."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()
        mock_privacy_request = Mock()

        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"s3_key": "key1", "size": 1000},
                        {"s3_key": "key2", "size": 2000},
                    ],
                }
            ]
        }

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=Mock(file_name="file1.txt", s3_key="key1", size=1000),
                    base_path="users",
                    item=data["users"][0],
                ),
                Mock(
                    attachment=Mock(file_name="file2.txt", s3_key="key2", size=2000),
                    base_path="users",
                    item=data["users"][0],
                ),
            ]

            # Mock get_object to fail for the second attachment
            def mock_get_object(bucket, key):
                if key == "key1":
                    return b"content1"
                else:
                    raise Exception("Download failed")

            mock_storage_client.get_object.side_effect = mock_get_object

            metrics = stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
            )

            # Should process one attachment successfully, one with error
            assert metrics.processed_attachments == 1
            assert metrics.processed_bytes == 1000
            assert len(metrics.errors) == 1
            assert "Failed to download attachment" in metrics.errors[0]

    def test_stream_attachments_to_storage_zip_creation_failure(self):
        """Test streaming ZIP creation when ZIP creation fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.side_effect = Exception("ZIP creation failed")
        mock_privacy_request = Mock()

        data = {"users": [{"id": 1, "attachments": [{"s3_key": "key1", "size": 1000}]}]}

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=Mock(file_name="file1.txt", s3_key="key1", size=1000),
                    base_path="users",
                    item=data["users"][0],
                )
            ]

            mock_storage_client.get_object.return_value = b"test content"

            with pytest.raises(
                StorageUploadError, match="Failed to create streaming ZIP file"
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
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        # Mock attachment info
        mock_attachment = Mock()
        mock_attachment.file_name = "test.txt"
        mock_attachment.s3_key = "key1"
        mock_attachment.size = 1000

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=mock_attachment, base_path="users", item=data["users"][0]
                )
            ]

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
            url, metrics = upload_to_storage_streaming(
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
            assert metrics.processed_attachments == 1
            assert metrics.processed_bytes == 1000

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
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        # Mock attachment info
        mock_attachment = Mock()
        mock_attachment.file_name = "test.txt"
        mock_attachment.s3_key = "key1"
        mock_attachment.size = 1000

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=mock_attachment, base_path="users", item=data["users"][0]
                )
            ]

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
            url, metrics = upload_to_storage_streaming(
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
            assert metrics.processed_attachments == 1
            assert metrics.processed_bytes == 1000

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
        ) as mock_html:
            mock_metrics = Mock()
            mock_metrics.processed_attachments = 0
            mock_metrics.processed_bytes = 0
            mock_html.return_value = mock_metrics

            # Call the function
            url, metrics = upload_to_storage_streaming(
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
            assert metrics == mock_metrics

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

        with pytest.raises(
            NotImplementedError, match="Document-only uploads not yet implemented"
        ):
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
        data = {"users": [{"id": 1, "attachments": [{"s3_key": "key1", "size": 1000}]}]}

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=Mock(file_name="file1.txt", s3_key="key1", size=1000),
                    base_path="users",
                    item=data["users"][0],
                )
            ]

            mock_storage_client.get_object.return_value = b"test content"

            # Should return None for URL but still return metrics
            url, metrics = upload_to_storage_streaming(
                mock_storage_client,
                data,
                config,
                mock_privacy_request,
                None,
                None,
                StreamingBufferConfig(),
            )

            assert url is None
            assert metrics is not None
            assert metrics.processed_attachments == 1

    def test_upload_to_storage_streaming_upload_failure(self):
        """Test the main upload function when upload fails."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_privacy_request = Mock()

        data = {"users": [{"id": 1, "attachments": [{"s3_key": "key1", "size": 1000}]}]}

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test-key.zip",
            resp_format=ResponseFormat.csv.value,
            max_workers=2,
        )

        # Mock the stream_attachments_to_storage_zip function to fail
        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
        ) as mock_stream:
            mock_stream.side_effect = Exception("Upload failed")

            with pytest.raises(
                StorageUploadError,
                match="Unexpected error during true streaming upload",
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

    def test_stream_attachments_to_storage_zip_with_progress_callback(self):
        """Test streaming ZIP creation with progress callback."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()
        mock_privacy_request = Mock()
        mock_progress_callback = Mock()

        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"s3_key": "key1", "size": 1000},
                        {"s3_key": "key2", "size": 2000},
                    ],
                }
            ]
        }

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=Mock(file_name="file1.txt", s3_key="key1", size=1000),
                    base_path="users",
                    item=data["users"][0],
                ),
                Mock(
                    attachment=Mock(file_name="file2.txt", s3_key="key2", size=2000),
                    base_path="users",
                    item=data["users"][0],
                ),
            ]

            mock_storage_client.get_object.return_value = b"test content"

            metrics = stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
                progress_callback=mock_progress_callback,
            )

            # Progress callback should be called for each attachment
            assert mock_progress_callback.call_count == 2
            assert metrics.processed_attachments == 2
            assert metrics.processed_bytes == 3000

    def test_stream_attachments_to_storage_zip_with_custom_buffer_config(self):
        """Test streaming ZIP creation with custom buffer configuration."""
        mock_storage_client = create_autospec(CloudStorageClient)
        mock_storage_client.put_object.return_value = Mock()
        mock_privacy_request = Mock()

        data = {"users": [{"id": 1, "attachments": [{"s3_key": "key1", "size": 1000}]}]}

        custom_buffer_config = StreamingBufferConfig(
            chunk_size=1024 * 1024,  # 1MB chunks
            max_memory_usage=5 * 1024 * 1024,  # 5MB max
        )

        # Mock the _collect_and_validate_attachments function
        with patch(
            "fides.api.service.storage.streaming.streaming_storage._collect_and_validate_attachments"
        ) as mock_collect:
            mock_collect.return_value = [
                Mock(
                    attachment=Mock(file_name="file1.txt", s3_key="key1", size=1000),
                    base_path="users",
                    item=data["users"][0],
                )
            ]

            mock_storage_client.get_object.return_value = b"test content"

            metrics = stream_attachments_to_storage_zip(
                mock_storage_client,
                "test-bucket",
                "test-key.zip",
                data,
                mock_privacy_request,
                max_workers=2,
                buffer_config=custom_buffer_config,
            )

            assert metrics.processed_attachments == 1
            assert metrics.processed_bytes == 1000

    def test_split_data_into_packages_edge_cases(self):
        """Test package splitting with various edge cases."""
        # Test with None values in data - should handle gracefully
        data = {
            "users": [
                {"id": 1, "attachments": None},  # None attachments
                {"id": 2, "attachments": [{"s3_key": "key1", "size": 1000}]},
            ]
        }

        packages = split_data_into_packages(data)
        # Should handle None gracefully and only process valid attachments
        assert len(packages) == 1

        # Test with empty strings as keys
        data = {"": [{"id": 1, "attachments": [{"s3_key": "key1", "size": 1000}]}]}

        packages = split_data_into_packages(data)
        assert len(packages) == 1
        assert "" in packages[0]

        # Test with very large attachment counts
        data = {
            "users": [
                {
                    "id": 1,
                    "attachments": [
                        {"s3_key": f"key{x}", "size": 1000} for x in range(1000)
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

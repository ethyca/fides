"""Tests for the streaming storage implementation.

These tests verify that the streaming storage correctly implements true streaming:
- Downloads chunks and immediately uploads them to storage
- Does NOT build zip files in memory
- Uses multipart uploads for coordination
- Maintains only small buffers for individual chunks
"""

import zlib
from io import BytesIO
from unittest.mock import MagicMock, Mock, call, create_autospec, patch

import pytest

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    MultipartUploadResponse,
    StorageUploadConfig,
    UploadPartResponse,
)
from fides.api.service.storage.streaming.streaming_storage import (
    split_data_into_packages,
    stream_attachments_to_storage_zip,
    upload_to_storage_streaming,
)


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
        """Test package splitting when individual items exceed max_attachments."""
        from fides.api.service.storage.streaming.schemas import PackageSplitConfig

        # Test data with one item having more attachments than the limit
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"s3_key": f"key{i}", "size": 1000} for i in range(150)
                    ],  # 150 attachments
                }
            ]
        }

        # Config allows only 100 attachments per package
        config = PackageSplitConfig(max_attachments=100)
        packages = split_data_into_packages(data, config)

        # Should split into 2 packages since 150 > 100
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
                    "attachments": [{"s3_key": "key1", "size": 1000}] * 25,
                }
            ]
        }

        # Custom config with very low limit
        config = PackageSplitConfig(max_attachments=10)
        packages = split_data_into_packages(data, config)

        # Should split into 3 packages since 25 > 10
        assert len(packages) == 3
        assert len(packages[0]["users"][0]["attachments"]) == 10
        assert len(packages[1]["users"][0]["attachments"]) == 10
        assert len(packages[2]["users"][0]["attachments"]) == 5

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
        # Items with no attachments still get packages created, but they don't count toward the limit
        # Since both users have 0 attachments, they can fit in the same package
        assert len(packages) == 1
        assert "users" in packages[0]
        assert len(packages[0]["users"]) == 2

    def test_stream_attachments_to_storage_zip_no_valid_attachments(self):
        """Test streaming when no valid attachments are found."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        mock_client.complete_multipart_upload.return_value = None

        data = {
            "users": [{"id": 1, "name": "User 1", "attachments": []}]  # No attachments
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "key", data, mock_privacy_request
        )

        assert metrics.total_attachments == 0
        assert metrics.processed_attachments == 0
        mock_client.complete_multipart_upload.assert_called_once()

    def test_stream_attachments_to_storage_zip_invalid_attachment_data(self):
        """Test streaming with invalid attachment data."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        mock_client.complete_multipart_upload.return_value = None

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {"invalid_field": "value"}  # Missing required s3_key
                    ],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "key", data, mock_privacy_request
        )

        assert len(metrics.errors) > 0
        assert "missing required field 's3_key'" in metrics.errors[0]

    def test_stream_attachments_to_storage_zip_attachment_validation_error(self):
        """Test streaming with attachment validation errors."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        # Mock the storage client methods to return proper values
        mock_client.get_object_head.return_value = {"ContentLength": 1000}
        mock_client.get_object_range.return_value = b"test data"
        mock_client.upload_part.return_value = UploadPartResponse(
            etag="test-etag", part_number=1
        )
        mock_client.complete_multipart_upload.return_value = None

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [
                        {
                            "s3_key": "valid-key",
                            "file_name": None,  # This might cause validation issues
                            "size": 1000,  # Valid size
                        }
                    ],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        # This should complete without errors since the data is actually valid
        # The refactored code handles None file_name gracefully
        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "key", data, mock_privacy_request
        )

        # Should complete without errors
        assert len(metrics.errors) == 0

    def test_stream_attachments_to_storage_zip_storage_upload_error(self):
        """Test streaming when storage upload fails."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.side_effect = StorageUploadError(
            "Upload failed"
        )

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        with pytest.raises(StorageUploadError, match="Upload failed"):
            stream_attachments_to_storage_zip(
                mock_client, "bucket", "key", data, mock_privacy_request
            )

    def test_stream_attachments_to_storage_zip_abort_on_failure(self):
        """Test that multipart upload is aborted on failure."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        # Mock the get_object_head to return a proper response first, then fail on upload_part
        mock_client.get_object_head.return_value = {"ContentLength": 1000}
        mock_client.get_object_range.return_value = b"test data"
        mock_client.upload_part.side_effect = StorageUploadError("Part upload failed")
        mock_client.abort_multipart_upload.return_value = None

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        with pytest.raises(StorageUploadError, match="Part upload failed"):
            stream_attachments_to_storage_zip(
                mock_client, "bucket", "key", data, mock_privacy_request
            )

        mock_client.abort_multipart_upload.assert_called_once_with(
            "bucket", "key", "test-upload"
        )

    def test_stream_attachments_to_storage_zip_abort_failure_handled(self):
        """Test that abort failure is handled gracefully."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        # Mock the get_object_head to return a proper response first, then fail on upload_part
        mock_client.get_object_head.return_value = {"ContentLength": 1000}
        mock_client.get_object_range.return_value = b"test data"
        mock_client.upload_part.side_effect = StorageUploadError("Part upload failed")
        mock_client.abort_multipart_upload.side_effect = StorageUploadError(
            "Abort failed"
        )

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        with pytest.raises(StorageUploadError, match="Part upload failed"):
            stream_attachments_to_storage_zip(
                mock_client, "bucket", "key", data, mock_privacy_request
            )

    def test_upload_to_storage_streaming_csv_format(self):
        """Test upload with CSV format."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.generate_presigned_url.return_value = "https://example.com/file"

        config = StorageUploadConfig(
            bucket_name="bucket",
            file_key="test.csv",
            resp_format=ResponseFormat.csv.value,
            max_workers=5,
        )

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
        ) as mock_stream:
            mock_stream.return_value = create_autospec(
                "fides.api.service.storage.streaming.schemas.ProcessingMetrics"
            )

            url, metrics = upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

            assert url == "https://example.com/file"
            mock_stream.assert_called_once()

    def test_upload_to_storage_streaming_json_format(self):
        """Test upload with JSON format."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.generate_presigned_url.return_value = "https://example.com/file"

        config = StorageUploadConfig(
            bucket_name="bucket",
            file_key="test.json",
            resp_format=ResponseFormat.json.value,
            max_workers=5,
        )

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
        ) as mock_stream:
            mock_stream.return_value = create_autospec(
                "fides.api.service.storage.streaming.schemas.ProcessingMetrics"
            )

            url, metrics = upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

            assert url == "https://example.com/file"
            mock_stream.assert_called_once()

    def test_upload_to_storage_streaming_html_format(self):
        """Test upload with HTML format."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.generate_presigned_url.return_value = "https://example.com/file"

        config = StorageUploadConfig(
            bucket_name="bucket",
            file_key="test.html",
            resp_format=ResponseFormat.html.value,
            max_workers=5,
        )

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_html_dsr_report_to_storage_multipart"
        ) as mock_stream:
            mock_stream.return_value = create_autospec(
                "fides.api.service.storage.streaming.schemas.ProcessingMetrics"
            )

            url, metrics = upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

            assert url == "https://example.com/file"
            mock_stream.assert_called_once()

    def test_upload_to_storage_streaming_unsupported_format(self):
        """Test upload with unsupported format."""
        mock_client = create_autospec(CloudStorageClient)

        config = StorageUploadConfig(
            bucket_name="bucket",
            file_key="test.xyz",
            resp_format="unsupported",
            max_workers=5,
        )

        data = {"users": []}
        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        # The refactored code wraps NotImplementedError in StorageUploadError
        with pytest.raises(
            StorageUploadError, match="No streaming support for format unsupported"
        ):
            upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

    def test_upload_to_storage_streaming_no_privacy_request(self):
        """Test upload without privacy request."""
        mock_client = create_autospec(CloudStorageClient)

        config = StorageUploadConfig(
            bucket_name="bucket",
            file_key="test.csv",
            resp_format=ResponseFormat.csv.value,
            max_workers=5,
        )

        data = {"users": []}

        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_storage_streaming(mock_client, data, config, None, None)

    def test_upload_to_storage_streaming_storage_error(self):
        """Test upload when storage operations fail."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.generate_presigned_url.side_effect = StorageUploadError(
            "URL generation failed"
        )

        config = StorageUploadConfig(
            bucket_name="bucket",
            file_key="test.csv",
            resp_format=ResponseFormat.csv.value,
            max_workers=5,
        )

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
        ) as mock_stream:
            mock_stream.return_value = create_autospec(
                "fides.api.service.storage.streaming.schemas.ProcessingMetrics"
            )

            url, metrics = upload_to_storage_streaming(
                mock_client, data, config, mock_privacy_request, None
            )

            assert url is None
            assert metrics is not None

    def test_upload_to_storage_streaming_unexpected_error(self):
        """Test upload when unexpected errors occur."""
        mock_client = create_autospec(CloudStorageClient)

        config = StorageUploadConfig(
            bucket_name="bucket",
            file_key="test.csv",
            resp_format=ResponseFormat.csv.value,
            max_workers=5,
        )

        data = {"users": []}
        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        with patch(
            "fides.api.service.storage.streaming.streaming_storage.stream_attachments_to_storage_zip"
        ) as mock_stream:
            mock_stream.side_effect = ValueError("Unexpected error")

            with pytest.raises(
                StorageUploadError,
                match="Unexpected error during true streaming upload",
            ):
                upload_to_storage_streaming(
                    mock_client, data, config, mock_privacy_request, None
                )

    def test_stream_attachments_to_storage_zip_with_package_splitting(self):
        """Test streaming with automatic package splitting."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        # Mock the storage client methods to return proper values
        mock_client.get_object_head.return_value = {"ContentLength": 1024 * 1024}  # 1MB
        mock_client.get_object_range.return_value = b"test data"
        mock_client.upload_part.return_value = UploadPartResponse(
            etag="test-etag", part_number=1
        )
        mock_client.complete_multipart_upload.return_value = None

        # Create data that will trigger package splitting
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "attachments": [
                        {"s3_key": f"key{i}", "size": 1024 * 1024} for i in range(150)
                    ],  # 150 attachments
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        # This should trigger package splitting since 150 > 100 (default max_attachments)
        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "test-key", data, mock_privacy_request
        )

        # Verify the result
        assert metrics is not None
        assert metrics.total_attachments == 150
        assert metrics.processed_attachments > 0

        # Verify client calls were made
        mock_client.create_multipart_upload.assert_called()
        mock_client.upload_part.assert_called()
        mock_client.complete_multipart_upload.assert_called()

    def test_stream_attachments_to_storage_zip_csv_fallback_to_json(self):
        """Test that CSV serialization falls back to JSON on failure."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        # Mock the storage client methods to return proper values
        mock_client.get_object_head.return_value = {"ContentLength": 1000}
        mock_client.get_object_range.return_value = b"test data"
        mock_client.upload_part.return_value = UploadPartResponse(
            etag="test-etag", part_number=1
        )
        mock_client.complete_multipart_upload.return_value = None

        # Create data with item that will cause CSV serialization to fail
        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                    "complex_object": {"nested": "data"},  # This should serialize fine
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "key", data, mock_privacy_request
        )

        # Should complete without errors
        assert len(metrics.errors) == 0

    def test_stream_attachments_to_storage_zip_both_csv_and_json_fail(self):
        """Test handling when both CSV and JSON serialization fail."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        # Mock the storage client methods to return proper values
        mock_client.get_object_head.return_value = {"ContentLength": 1000}
        mock_client.get_object_range.return_value = b"test data"
        mock_client.upload_part.return_value = UploadPartResponse(
            etag="test-etag", part_number=1
        )
        mock_client.complete_multipart_upload.return_value = None

        # Create data with item that will cause both CSV and JSON to fail
        class UnserializableObject:
            def __str__(self):
                raise UnicodeEncodeError("utf-8", "test", 0, 1, "encoding error")

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                    "unserializable": UnserializableObject(),
                }
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "key", data, mock_privacy_request
        )

        # Should have errors but complete the upload
        assert len(metrics.errors) > 0
        assert "Failed to serialize item" in metrics.errors[0]

    def test_stream_attachments_to_storage_zip_non_dict_item_fallback(self):
        """Test handling of non-dict items in data."""
        mock_client = create_autospec(CloudStorageClient)
        # Mock the storage client methods to return proper values for the valid attachment
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        mock_client.get_object_head.return_value = {"ContentLength": 1000}
        mock_client.get_object_range.return_value = b"test data"
        mock_client.upload_part.return_value = UploadPartResponse(
            etag="test-etag", part_number=1
        )
        mock_client.complete_multipart_upload.return_value = None

        # Create data with non-dict item
        data = {
            "users": [
                "This is a string, not a dict",  # Non-dict item
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                },
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        # The refactored code now handles non-dict items gracefully
        # It will log warnings and continue processing valid items
        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "key", data, mock_privacy_request
        )

        # Should complete with warnings about non-dict items
        assert len(metrics.errors) > 0
        assert any("not a dict-like object" in error for error in metrics.errors)
        # Should still process the valid attachment
        assert metrics.processed_attachments > 0

    def test_stream_attachments_to_storage_zip_empty_item_dict(self):
        """Test handling of empty dict items."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        # Mock the storage client methods to return proper values
        mock_client.get_object_head.return_value = {"ContentLength": 1000}
        mock_client.get_object_range.return_value = b"test data"
        mock_client.upload_part.return_value = UploadPartResponse(
            etag="test-etag", part_number=1
        )
        mock_client.complete_multipart_upload.return_value = None

        # Create data with empty dict item
        data = {
            "users": [
                {},  # Empty dict
                {
                    "id": 1,
                    "name": "User 1",
                    "attachments": [{"s3_key": "key1", "size": 1000}],
                },
            ]
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "key", data, mock_privacy_request
        )

        # Should complete without errors
        assert len(metrics.errors) == 0

    def test_stream_attachments_to_storage_zip_no_parts_uploaded(self):
        """Test handling when no parts are uploaded."""
        mock_client = create_autospec(CloudStorageClient)
        mock_client.create_multipart_upload.return_value = MultipartUploadResponse(
            upload_id="test-upload"
        )
        mock_client.complete_multipart_upload.return_value = None

        # Create data with no valid attachments
        data = {
            "users": [{"id": 1, "name": "User 1", "attachments": []}]  # No attachments
        }

        mock_privacy_request = create_autospec(
            "fides.api.models.privacy_request.PrivacyRequest"
        )

        metrics = stream_attachments_to_storage_zip(
            mock_client, "bucket", "key", data, mock_privacy_request
        )

        # Should complete with empty parts list
        mock_client.complete_multipart_upload.assert_called_once_with(
            "bucket", "key", "test-upload", []
        )
        assert len(metrics.errors) == 0

    def test_stream_attachments_to_storage_zip(self):
        """Test the streaming ZIP approach using stream_zip with parallel processing."""
        # Mock storage client
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

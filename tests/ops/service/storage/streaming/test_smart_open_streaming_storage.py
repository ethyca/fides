"""Tests for SmartOpenStreamingStorage class."""

import json
from datetime import datetime
from io import BytesIO, StringIO
from unittest.mock import MagicMock, Mock, create_autospec, patch

import pytest
from stream_zip import _ZIP_32_TYPE

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.service.storage.streaming.schemas import (
    AttachmentInfo,
    AttachmentProcessingInfo,
    PackageSplitConfig,
    StorageUploadConfig,
    StreamingBufferConfig,
)
from fides.api.service.storage.streaming.smart_open_streaming_storage import (
    SmartOpenStreamingStorage,
)


class TestSmartOpenStreamingStorage:
    """Test SmartOpenStreamingStorage class."""

    def test_init(self, mock_smart_open_client):
        """Test initialization with default and custom chunk size."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)
        assert storage.storage_client == mock_smart_open_client
        assert storage.chunk_size == 5 * 1024 * 1024  # CHUNK_SIZE_THRESHOLD (5MB)

        storage = SmartOpenStreamingStorage(mock_smart_open_client, chunk_size=4096)
        assert storage.chunk_size == 4096

    def test_convert_to_stream_zip_format(self, mock_smart_open_client):
        """Test conversion to stream_zip format."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Create test generator
        def test_generator():
            yield "test.json", BytesIO(b'{"test": "data"}'), {"metadata": "test"}
            yield "test2.csv", BytesIO(b"test,csv,data"), {"metadata": "test2"}

        result = list(storage._convert_to_stream_zip_format(test_generator()))

        assert len(result) == 2
        assert result[0][0] == "test.json"
        assert result[0][1] is not None  # datetime
        assert result[0][2] == 0o644
        assert result[0][3] is not None  # _ZIP_32_TYPE instance
        assert list(result[0][4]) == [b'{"test": "data"}']

    def test_build_attachments_list(self, mock_smart_open_client):
        """Test building attachments list from data."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "attachments": [
                        {
                            "file_name": "doc1.pdf",
                            "download_url": "http://example.com/doc1.pdf",
                        },
                        {
                            "file_name": "doc2.pdf",
                            "download_url": "http://example.com/doc2.pdf",
                        },
                    ],
                },
                {
                    "id": "2",
                    "attachments": [
                        {
                            "file_name": "doc3.pdf",
                            "download_url": "http://example.com/doc3.pdf",
                        },
                    ],
                },
            ]
        }

        config = PackageSplitConfig(max_attachments=2)
        result = storage.build_attachments_list(data, config)

        assert len(result) == 2
        assert result[0][0] == "users"
        assert result[0][2] == 2  # attachment count
        assert result[1][0] == "users"
        assert result[1][2] == 1  # attachment count

    def test_build_attachments_list_with_splitting(self, mock_smart_open_client):
        """Test building attachments list with package splitting."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "attachments": [
                        {
                            "file_name": f"doc{i}.pdf",
                            "download_url": f"http://example.com/doc{i}.pdf",
                        }
                        for i in range(5)  # More than max_attachments
                    ],
                }
            ]
        }

        config = PackageSplitConfig(max_attachments=2)
        result = storage.build_attachments_list(data, config)

        # Should split into 3 packages (2+2+1)
        assert len(result) == 3
        assert result[0][2] == 2
        assert result[1][2] == 2
        assert result[2][2] == 1

    def test_build_attachments_list_no_attachments(self, mock_smart_open_client):
        """Test building attachments list with no attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {"id": "1", "name": "Test User"},
                {"id": "2", "name": "Test User 2"},
            ]
        }

        config = PackageSplitConfig(max_attachments=2)
        result = storage.build_attachments_list(data, config)

        assert len(result) == 0

    def test_split_data_into_packages(self, mock_smart_open_client):
        """Test splitting data into packages."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "attachments": [
                        {
                            "file_name": "doc1.pdf",
                            "download_url": "http://example.com/doc1.pdf",
                        },
                        {
                            "file_name": "doc2.pdf",
                            "download_url": "http://example.com/doc2.pdf",
                        },
                    ],
                },
                {
                    "id": "2",
                    "attachments": [
                        {
                            "file_name": "doc3.pdf",
                            "download_url": "http://example.com/doc3.pdf",
                        },
                    ],
                },
            ]
        }

        config = PackageSplitConfig(max_attachments=3)
        result = storage.split_data_into_packages(data, config)

        assert len(result) == 1  # Should fit in one package
        assert "users" in result[0]
        assert len(result[0]["users"]) == 2

    def test_split_data_into_packages_default_config(self, mock_smart_open_client):
        """Test splitting data with default config."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "attachments": [
                        {
                            "file_name": "doc1.pdf",
                            "download_url": "http://example.com/doc1.pdf",
                        },
                    ],
                }
            ]
        }

        result = storage.split_data_into_packages(data)

        assert len(result) == 1
        assert "users" in result[0]

    def test_split_data_into_packages_requires_splitting(self, mock_smart_open_client):
        """Test splitting data that requires multiple packages."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "attachments": [
                        {
                            "file_name": f"doc{i}.pdf",
                            "download_url": f"http://example.com/doc{i}.pdf",
                        }
                        for i in range(5)
                    ],
                },
                {
                    "id": "2",
                    "attachments": [
                        {
                            "file_name": "doc6.pdf",
                            "download_url": "http://example.com/doc6.pdf",
                        },
                    ],
                },
            ]
        }

        config = PackageSplitConfig(max_attachments=2)
        result = storage.split_data_into_packages(data, config)

        assert len(result) == 3  # 2+2+1+1 split

    def test_collect_attachments(self, mock_smart_open_client):
        """Test collecting attachments from data."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "attachments": [
                        {
                            "file_name": "doc1.pdf",
                            "download_url": "http://example.com/doc1.pdf",
                        },
                    ],
                }
            ],
            "attachments": [
                {
                    "file_name": "global.pdf",
                    "download_url": "http://example.com/global.pdf",
                }
            ],
        }

        result = storage._collect_attachments(data)

        assert len(result) == 2
        # Check that direct attachments are processed
        assert any("global.pdf" in str(att) for att in result)
        # Check that nested attachments are processed
        assert any("doc1.pdf" in str(att) for att in result)

    def test_collect_direct_attachments(self, mock_smart_open_client):
        """Test collecting direct attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        attachments_list = [
            {"file_name": "doc1.pdf", "download_url": "http://example.com/doc1.pdf"},
            {"file_name": "doc2.pdf", "download_url": "http://example.com/doc2.pdf"},
            {"invalid": "attachment"},  # Should be skipped
        ]

        result = storage._collect_direct_attachments(attachments_list)

        assert len(result) == 2
        assert result[0]["file_name"] == "doc1.pdf"
        assert result[0]["download_url"] == "attachments/doc1.pdf"
        assert result[0]["original_download_url"] == "http://example.com/doc1.pdf"

    def test_collect_direct_attachments_no_file_name(self, mock_smart_open_client):
        """Test collecting direct attachments without file_name."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        attachments_list = [
            {"download_url": "http://example.com/doc1.pdf"},
        ]

        result = storage._collect_direct_attachments(attachments_list)

        assert len(result) == 1
        assert result[0]["download_url"] == "attachments/attachment_0"

    def test_collect_nested_attachments(self, mock_smart_open_client):
        """Test collecting nested attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        key = "users"
        items = [
            {
                "id": "1",
                "attachments": [
                    {
                        "file_name": "doc1.pdf",
                        "download_url": "http://example.com/doc1.pdf",
                    },
                ],
            }
        ]

        result = storage._collect_nested_attachments(key, items)

        assert len(result) == 1
        assert result[0]["file_name"] == "doc1.pdf"
        assert result[0]["_context"]["key"] == "users"
        assert result[0]["_context"]["item_id"] == "1"

    def test_find_attachments_recursive(self, mock_smart_open_client):
        """Test recursive attachment finding."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        item = {
            "id": "1",
            "attachments": [
                {
                    "file_name": "doc1.pdf",
                    "download_url": "http://example.com/doc1.pdf",
                },
            ],
            "nested": {
                "attachments": [
                    {
                        "file_name": "doc2.pdf",
                        "download_url": "http://example.com/doc2.pdf",
                    },
                ]
            },
        }

        result = storage._find_attachments_recursive(item, "users")

        assert len(result) == 2
        assert result[0]["file_name"] == "doc1.pdf"
        assert result[1]["file_name"] == "doc2.pdf"
        assert result[1]["_context"]["path"] == "nested"

    def test_validate_attachment_valid(self, mock_smart_open_client):
        """Test validating a valid attachment."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        attachment = {
            "file_name": "test.pdf",
            "download_url": "http://example.com/test.pdf",
            "size": 1024,
            "content_type": "application/pdf",
        }

        result = storage._validate_attachment(attachment)

        assert result is not None
        assert result.attachment.file_name == "test.pdf"
        assert result.attachment.storage_key == "http://example.com/test.pdf"
        assert result.base_path == "attachments"

    def test_validate_attachment_with_context(self, mock_smart_open_client):
        """Test validating attachment with context."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        attachment = {
            "file_name": "test.pdf",
            "download_url": "http://example.com/test.pdf",
            "_context": {"key": "users", "item_id": "123", "path": "nested"},
        }

        result = storage._validate_attachment(attachment)

        assert result is not None
        assert result.base_path == "users/123/attachments"

    def test_validate_attachment_no_storage_key(self, mock_smart_open_client):
        """Test validating attachment without storage key."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        attachment = {
            "size": 1024
            # No file_name, download_url, or original_download_url
        }

        result = storage._validate_attachment(attachment)

        assert result is None

    def test_validate_attachment_invalid(self, mock_smart_open_client):
        """Test validating invalid attachment."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # This should cause a KeyError when trying to access missing keys
        attachment = {}

        result = storage._validate_attachment(attachment)

        assert result is None

    def test_create_attachment_content_stream(self, mock_smart_open_client):
        """Test creating attachment content stream."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Mock the stream_read to return our mock stream
        mock_stream = MagicMock()
        mock_stream.read.side_effect = [b"chunk1", b"chunk2", b""]
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_smart_open_client.stream_read.return_value = mock_stream

        result = list(
            storage._create_attachment_content_stream("bucket", "key", "storage_key")
        )

        assert result == [b"chunk1", b"chunk2"]
        mock_smart_open_client.stream_read.assert_called_once_with("bucket", "key")

    def test_create_attachment_content_stream_exception(self, mock_smart_open_client):
        """Test creating attachment content stream with exception."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Mock stream_read to raise an exception
        mock_smart_open_client.stream_read.side_effect = Exception("Storage error")

        result = list(
            storage._create_attachment_content_stream("bucket", "key", "storage_key")
        )

        assert result == [b""]

    def test_collect_and_validate_attachments(self, mock_smart_open_client):
        """Test collecting and validating attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "attachments": [
                        {
                            "file_name": "doc1.pdf",
                            "download_url": "http://example.com/doc1.pdf",
                        },
                    ],
                }
            ]
        }

        result = storage._collect_and_validate_attachments(data)

        assert len(result) == 1
        assert result[0].attachment.file_name == "doc1.pdf"

    @patch(
        "fides.api.service.storage.streaming.smart_open_streaming_storage.stream_html_dsr_report_to_storage_multipart"
    )
    def test_upload_to_storage_streaming_csv(
        self, mock_html_report, mock_smart_open_client, mock_privacy_request
    ):
        """Test uploading CSV data to storage."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.csv",
            resp_format=ResponseFormat.csv.value,
            max_workers=4,
        )

        data = {"users": [{"id": "1", "name": "Test"}]}

        result = storage.upload_to_storage_streaming(data, config, mock_privacy_request)

        assert result == "https://example.com/test.zip"
        mock_html_report.assert_not_called()

    @patch(
        "fides.api.service.storage.streaming.smart_open_streaming_storage.stream_html_dsr_report_to_storage_multipart"
    )
    def test_upload_to_storage_streaming_json(
        self, mock_html_report, mock_smart_open_client, mock_privacy_request
    ):
        """Test uploading JSON data to storage."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.json",
            resp_format=ResponseFormat.json.value,
            max_workers=4,
        )

        data = {"users": [{"id": "1", "name": "Test"}]}

        result = storage.upload_to_storage_streaming(data, config, mock_privacy_request)

        assert result == "https://example.com/test.zip"
        mock_html_report.assert_not_called()

    @patch(
        "fides.api.service.storage.streaming.smart_open_streaming_storage.stream_html_dsr_report_to_storage_multipart"
    )
    def test_upload_to_storage_streaming_html(
        self, mock_html_report, mock_smart_open_client, mock_privacy_request
    ):
        """Test uploading HTML data to storage."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.html",
            resp_format=ResponseFormat.html.value,
            max_workers=4,
        )

        data = {"users": [{"id": "1", "name": "Test"}]}

        result = storage.upload_to_storage_streaming(data, config, mock_privacy_request)

        assert result == "https://example.com/test.zip"
        mock_html_report.assert_called_once()

    def test_upload_to_storage_streaming_no_privacy_request(
        self, mock_smart_open_client
    ):
        """Test uploading without privacy request raises error."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.csv",
            resp_format=ResponseFormat.csv.value,
            max_workers=4,
        )

        data = {"users": [{"id": "1", "name": "Test"}]}

        with pytest.raises(ValueError, match="Privacy request must be provided"):
            storage.upload_to_storage_streaming(data, config, None)

    def test_upload_to_storage_streaming_with_document(
        self, mock_smart_open_client, mock_privacy_request
    ):
        """Test uploading with document raises NotImplementedError."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.csv",
            resp_format=ResponseFormat.csv.value,
            max_workers=4,
        )

        data = {"users": [{"id": "1", "name": "Test"}]}

        with pytest.raises(
            NotImplementedError, match="Document-only uploads not yet implemented"
        ):
            storage.upload_to_storage_streaming(
                data, config, mock_privacy_request, document="test"
            )

    def test_upload_to_storage_streaming_unsupported_format(
        self, mock_smart_open_client, mock_privacy_request
    ):
        """Test uploading with unsupported format raises error."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.txt",
            resp_format="txt",
            max_workers=4,
        )

        data = {"users": [{"id": "1", "name": "Test"}]}

        with pytest.raises(
            StorageUploadError,
            match="Storage upload failed: Unsupported response format: txt",
        ):
            storage.upload_to_storage_streaming(data, config, mock_privacy_request)

    def test_upload_to_storage_streaming_storage_error(
        self, mock_smart_open_client, mock_privacy_request
    ):
        """Test uploading with storage error raises StorageUploadError."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Mock storage client to raise an exception
        mock_smart_open_client.generate_presigned_url.side_effect = Exception(
            "Storage error"
        )

        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.csv",
            resp_format=ResponseFormat.csv.value,
            max_workers=4,
        )

        data = {"users": [{"id": "1", "name": "Test"}]}

        with pytest.raises(
            StorageUploadError, match="Storage upload failed: Storage error"
        ):
            storage.upload_to_storage_streaming(data, config, mock_privacy_request)

    def test_stream_attachments_to_storage_zip_no_attachments(
        self, mock_smart_open_client, mock_privacy_request
    ):
        """Test streaming ZIP with no attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}

        storage._stream_attachments_to_storage_zip(
            "test-bucket",
            "test.zip",
            data,
            mock_privacy_request,
            4,
            StreamingBufferConfig(),
            10,
            "csv",
        )

        # Should call _upload_data_only_zip
        mock_smart_open_client.stream_upload.assert_called_once()

    def test_stream_attachments_to_storage_zip_with_attachments(
        self, mock_smart_open_client, mock_privacy_request
    ):
        """Test streaming ZIP with attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "attachments": [
                        {
                            "file_name": "doc1.pdf",
                            "download_url": "http://example.com/doc1.pdf",
                        },
                    ],
                }
            ]
        }

        storage._stream_attachments_to_storage_zip(
            "test-bucket",
            "test.zip",
            data,
            mock_privacy_request,
            4,
            StreamingBufferConfig(),
            10,
            "csv",
        )

        # Should call stream_upload for ZIP with attachments
        mock_smart_open_client.stream_upload.assert_called_once()

    def test_upload_data_only_zip(self, mock_smart_open_client):
        """Test uploading data-only ZIP."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}

        storage._upload_data_only_zip("test-bucket", "test.zip", data, "csv")

        mock_smart_open_client.stream_upload.assert_called_once()

    def test_create_zip_generator(self, mock_smart_open_client):
        """Test creating ZIP generator."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}
        attachments = [
            AttachmentProcessingInfo(
                attachment=AttachmentInfo(
                    storage_key="http://example.com/doc1.pdf", file_name="doc1.pdf"
                ),
                base_path="attachments",
                item={},
            )
        ]

        result = list(
            storage._create_zip_generator(
                data, attachments, "test-bucket", 4, 10, "csv"
            )
        )

        assert len(result) > 0

    def test_create_data_files_json(self, mock_smart_open_client):
        """Test creating JSON data files."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}

        result = list(storage._create_data_files(data, "json"))

        assert len(result) == 1
        assert result[0][0] == "users.json"
        assert json.loads(result[0][1].getvalue().decode()) == [
            {"id": "1", "name": "Test"}
        ]

    def test_create_data_files_csv(self, mock_smart_open_client):
        """Test creating CSV data files."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}

        result = list(storage._create_data_files(data, "csv"))

        assert len(result) == 1
        assert result[0][0] == "users.csv"
        csv_content = result[0][1].getvalue().decode()
        assert "id,name" in csv_content
        assert "1,Test" in csv_content

    def test_create_data_files_csv_non_dict_list(self, mock_smart_open_client):
        """Test creating CSV data files with non-dict list items."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": ["user1", "user2"]}

        result = list(storage._create_data_files(data, "csv"))

        assert len(result) == 1
        assert result[0][0] == "users.json"  # Falls back to JSON

    def test_create_data_files_html(self, mock_smart_open_client):
        """Test creating HTML data files."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}

        result = list(storage._create_data_files(data, "html"))

        assert len(result) == 1
        assert result[0][0] == "users.json"  # HTML uses JSON for data files

    def test_create_data_files_unsupported_format(self, mock_smart_open_client):
        """Test creating data files with unsupported format."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}

        result = list(storage._create_data_files(data, "txt"))

        assert len(result) == 1
        assert result[0][0] == "users.json"  # Defaults to JSON

    def test_create_data_files_with_attachments(self, mock_smart_open_client):
        """Test creating data files with attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}
        attachments = [
            AttachmentProcessingInfo(
                attachment=AttachmentInfo(
                    storage_key="http://example.com/doc1.pdf", file_name="doc1.pdf"
                ),
                base_path="attachments",
                item={},
            )
        ]

        result = list(storage._create_data_files(data, "json", attachments))

        assert len(result) == 1
        assert result[0][0] == "users.json"

    def test_create_attachment_files(self, mock_smart_open_client):
        """Test creating attachment files."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        attachments = [
            AttachmentProcessingInfo(
                attachment=AttachmentInfo(
                    storage_key="http://example.com/doc1.pdf", file_name="doc1.pdf"
                ),
                base_path="attachments",
                item={},
            )
        ]

        result = list(
            storage._create_attachment_files(attachments, "test-bucket", 4, 10)
        )

        assert len(result) == 1
        assert result[0][0] == "attachments/doc1.pdf"

    def test_create_attachment_files_s3_url(self, mock_smart_open_client):
        """Test creating attachment files with S3 URL."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        attachments = [
            AttachmentProcessingInfo(
                attachment=AttachmentInfo(
                    storage_key="s3://source-bucket/path/doc1.pdf", file_name="doc1.pdf"
                ),
                base_path="attachments",
                item={},
            )
        ]

        result = list(
            storage._create_attachment_files(attachments, "test-bucket", 4, 10)
        )

        assert len(result) == 1
        assert result[0][0] == "attachments/doc1.pdf"

    def test_create_attachment_files_exception(self, mock_smart_open_client):
        """Test creating attachment files with exception."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        # Mock _create_attachment_content_stream to raise exception
        with patch.object(
            storage,
            "_create_attachment_content_stream",
            side_effect=Exception("Test error"),
        ):
            attachments = [
                AttachmentProcessingInfo(
                    attachment=AttachmentInfo(
                        storage_key="http://example.com/doc1.pdf", file_name="doc1.pdf"
                    ),
                    base_path="attachments",
                    item={},
                )
            ]

            result = list(
                storage._create_attachment_files(attachments, "test-bucket", 4, 10)
            )

            # Should continue with other attachments
            assert len(result) == 0

    def test_transform_data_for_access_package(self, mock_smart_open_client):
        """Test transforming data for access package."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {
                    "id": "1",
                    "name": "Test",
                    "document_url": "http://example.com/doc1.pdf",
                }
            ]
        }

        attachments = [
            AttachmentProcessingInfo(
                attachment=AttachmentInfo(
                    storage_key="http://example.com/doc1.pdf", file_name="doc1.pdf"
                ),
                base_path="attachments",
                item={},
            )
        ]

        result = storage._transform_data_for_access_package(data, attachments)

        # Should replace external URL with internal path
        assert result["users"][0]["document_url"] == "attachments/doc1.pdf"

    def test_transform_data_for_access_package_no_attachments(
        self, mock_smart_open_client
    ):
        """Test transforming data with no attachments."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}

        result = storage._transform_data_for_access_package(data, [])

        # Should return original data unchanged
        assert result == data

    def test_transform_data_for_access_package_no_urls(self, mock_smart_open_client):
        """Test transforming data with no URLs to replace."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {"users": [{"id": "1", "name": "Test"}]}

        attachments = [
            AttachmentProcessingInfo(
                attachment=AttachmentInfo(
                    storage_key="s3://bucket/path/doc1.pdf", file_name="doc1.pdf"
                ),
                base_path="attachments",
                item={},
            )
        ]

        result = storage._transform_data_for_access_package(data, attachments)

        # Should return original data unchanged (no HTTP URLs)
        assert result == data

    def test_transform_data_for_access_package_nested(self, mock_smart_open_client):
        """Test transforming nested data for access package."""
        storage = SmartOpenStreamingStorage(mock_smart_open_client)

        data = {
            "users": [
                {"id": "1", "profile": {"avatar_url": "http://example.com/avatar.jpg"}}
            ]
        }

        attachments = [
            AttachmentProcessingInfo(
                attachment=AttachmentInfo(
                    storage_key="http://example.com/avatar.jpg", file_name="avatar.jpg"
                ),
                base_path="attachments",
                item={},
            )
        ]

        result = storage._transform_data_for_access_package(data, attachments)

        # Should replace nested URL
        assert result["users"][0]["profile"]["avatar_url"] == "attachments/avatar.jpg"

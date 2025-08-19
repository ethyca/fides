"""
Tests for streaming S3 upload functionality.

These tests verify that the streaming S3 upload functions work correctly
and provide better memory efficiency for large datasets.
"""

import pytest
from unittest.mock import patch, MagicMock, create_autospec
from io import BytesIO
import zipfile
import boto3
from moto import mock_aws
from botocore.exceptions import ClientError, ParamValidationError

from fides.api.service.storage.streaming.streaming_s3 import (
    upload_to_s3_streaming,
    upload_to_s3_streaming_advanced,
    split_data_into_packages,
    stream_attachments_to_s3_zip,
    stream_single_attachment_to_zip_streaming_with_metrics,
    download_chunk_with_retry,
    upload_zip_part,
    stream_html_to_s3_multipart,
)
from fides.api.schemas.storage.storage import ResponseFormat, StorageSecrets, AWSAuthMethod
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.common_exceptions import StorageUploadError
from fides.api.service.storage.streaming.schemas import ProcessingMetrics


@pytest.fixture
def mock_privacy_request():
    """Create a mock PrivacyRequest for testing."""
    mock_pr = create_autospec(PrivacyRequest)
    mock_pr.id = "test-privacy-request-id"
    return mock_pr


@pytest.fixture
def sample_data():
    """Sample data structure for testing."""
    return {
        "users": [
            {
                "id": "user1",
                "name": "Test User 1",
                "attachments": [
                    {"key": "file1.txt", "size": 1024, "url": "s3://bucket/file1.txt"},
                    {"key": "file2.txt", "size": 2048, "url": "s3://bucket/file2.txt"},
                ]
            },
            {
                "id": "user2",
                "name": "Test User 2",
                "attachments": [
                    {"key": "file3.txt", "size": 3072, "url": "s3://bucket/file3.txt"},
                ]
            }
        ],
        "orders": [
            {
                "id": "order1",
                "amount": 100.00,
                "attachments": [
                    {"key": "receipt.pdf", "size": 5120, "url": "s3://bucket/receipt.pdf"},
                ]
            }
        ]
    }


@pytest.fixture
def storage_secrets():
    """Sample storage secrets for testing."""
    return {
        StorageSecrets.AWS_ACCESS_KEY_ID: "test-access-key",
        StorageSecrets.AWS_SECRET_ACCESS_KEY: "test-secret-key",
        StorageSecrets.REGION_NAME: "us-east-1",
    }


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client for testing."""
    mock_client = create_autospec(boto3.client("s3"))

    # Mock multipart upload operations
    mock_client.create_multipart_upload.return_value = {"UploadId": "test-upload-id"}
    mock_client.upload_part.return_value = {"ETag": "test-etag"}
    mock_client.complete_multipart_upload.return_value = {"Location": "s3://bucket/test-key"}
    mock_client.abort_multipart_upload.return_value = {}

    # Mock object operations
    mock_client.head_object.return_value = {"ContentLength": 1024}
    mock_client.get_object.return_value = {"Body": BytesIO(b"test content")}

    return mock_client


class BaseStreamingTest:
    """Base class for streaming tests with common setup methods."""

    def setup_mock_chunk_download(self, mock_download_chunk, mock_adaptive_chunk_size, chunk_size=1024, chunk_data=b"test chunk data"):
        """Helper method to setup mock chunk download behavior."""
        mock_adaptive_chunk_size.return_value = chunk_size
        mock_download_chunk.return_value = chunk_data

    def setup_mock_s3_head(self, mock_s3_client, file_size):
        """Helper method to setup mock S3 head_object response."""
        mock_s3_client.head_object.return_value = {"ContentLength": file_size}

    def create_test_attachment(self, s3_key="test-bucket/test-file.txt", file_name="test-file.txt"):
        """Helper method to create test attachment data."""
        return {
            's3_key': s3_key,
            'file_name': file_name
        }

    def verify_zip_file_contents(self, zip_buffer, expected_file_count):
        """Helper method to verify zip file contents."""
        zip_buffer.seek(0)
        zip_content = zipfile.ZipFile(zip_buffer)
        file_list = zip_content.namelist()
        assert len(file_list) == expected_file_count
        zip_content.close()

    def verify_metrics_reset(self, metrics):
        """Helper method to verify metrics were reset."""
        assert metrics.current_attachment is None
        assert metrics.current_attachment_progress == 0.0

    def setup_upload_mocks(self, mock_get_client, mock_s3_client, mock_stream_func=None, mock_create_url=None):
        """Helper method to setup common upload test mocks."""
        mock_get_client.return_value = mock_s3_client
        if mock_stream_func:
            mock_stream_func.return_value = ProcessingMetrics()
        if mock_create_url:
            mock_create_url.return_value = "https://presigned-url.com"

    def call_upload_function(
            self, upload_func, storage_secrets, sample_data, mock_privacy_request, resp_format, file_key="test-file.json"
    ):
        """Helper method to call upload functions with common parameters."""
        return upload_func(
            storage_secrets=storage_secrets,
            data=sample_data,
            bucket_name="test-bucket",
            file_key=file_key,
            resp_format=resp_format,
            privacy_request=mock_privacy_request,
            document=None,
            auth_method=AWSAuthMethod.SECRET_KEYS.value,
        )

    def call_upload_function_with_none_privacy_request(
            self, upload_func, storage_secrets, sample_data, resp_format, file_key="test-file.json"
    ):
        """Helper method to call upload functions with None privacy request for error testing."""
        return upload_func(
            storage_secrets=storage_secrets,
            data=sample_data,
            bucket_name="test-bucket",
            file_key=file_key,
            resp_format=resp_format,
            privacy_request=None,
            document=None,
            auth_method=AWSAuthMethod.SECRET_KEYS.value,
        )


@pytest.fixture
def create_zip_file():
    """Helper fixture to create and manage zip files for testing."""
    zip_buffer = BytesIO()
    zip_file = zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED)
    return zip_buffer, zip_file


@pytest.fixture
def create_metrics():
    """Helper fixture to create ProcessingMetrics for testing."""
    return ProcessingMetrics()


class TestSplitDataIntoPackages:
    """Test the split_data_into_packages function."""

    def test_split_data_with_small_dataset(self, sample_data):
        """Test that small datasets are not split."""
        packages = split_data_into_packages(sample_data, max_attachments=100)
        assert len(packages) == 1
        assert packages[0] == sample_data

    def test_split_data_with_large_dataset(self):
        """Test that large datasets are split correctly."""
        # Create a large dataset with many attachments
        large_data = {
            "users": [
                {
                    "id": f"user{i}",
                    "attachments": [{"key": f"file{j}.txt", "size": 1024} for j in range(50)]
                }
                for i in range(10)  # 10 users * 50 attachments = 500 total
            ]
        }

        packages = split_data_into_packages(large_data, max_attachments=100)
        assert len(packages) == 5  # Should split into 5 packages of ~100 attachments each

    def test_split_data_with_mixed_attachment_counts(self):
        """Test splitting with varying attachment counts per item."""
        mixed_data = {
            "users": [
                {"id": "user1", "attachments": [{"key": "file1.txt"} for _ in range(80)]},
                {"id": "user2", "attachments": [{"key": "file2.txt"} for _ in range(30)]},
                {"id": "user3", "attachments": [{"key": "file3.txt"} for _ in range(60)]},
            ]
        }

        packages = split_data_into_packages(mixed_data, max_attachments=100)
        assert len(packages) == 2
        # First package should have user1 (80 attachments)
        # Second package should have user2 (30) + user3 (60) = 90 attachments

    def test_split_data_with_no_attachments(self):
        """Test splitting data with no attachments."""
        data_without_attachments = {
            "users": [
                {"id": "user1", "name": "Test User"},
                {"id": "user2", "name": "Test User 2"},
            ]
        }

        packages = split_data_into_packages(data_without_attachments, max_attachments=100)
        assert len(packages) == 1
        assert packages[0] == data_without_attachments

    def test_split_data_with_empty_lists(self):
        """Test splitting data with empty lists."""
        data_with_empty_lists = {
            "users": [],
            "orders": []
        }

        packages = split_data_into_packages(data_with_empty_lists, max_attachments=100)
        # Empty data should result in no packages since there are no attachments
        assert len(packages) == 0


class TestStreamingS3Upload(BaseStreamingTest):
    """Test the main streaming S3 upload functions."""

    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    @patch("fides.api.service.storage.streaming_s3.create_presigned_url_for_s3")
    @patch("fides.api.service.storage.streaming_s3.stream_attachments_to_s3_zip")
    def test_upload_to_s3_streaming_json_success(
        self, mock_stream_zip, mock_create_url, mock_get_client,
        mock_privacy_request, sample_data, storage_secrets, mock_s3_client
    ):
        """Test successful JSON upload with streaming."""
        self.setup_upload_mocks(mock_get_client, mock_s3_client, mock_stream_zip, mock_create_url)

        url, metrics = self.call_upload_function(
            upload_to_s3_streaming, storage_secrets, sample_data, mock_privacy_request,
            ResponseFormat.json.value, "test-file.json"
        )

        assert url == "https://presigned-url.com"
        assert isinstance(metrics, ProcessingMetrics)
        mock_stream_zip.assert_called_once()

    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    @patch("fides.api.service.storage.streaming_s3.create_presigned_url_for_s3")
    @patch("fides.api.service.storage.streaming_s3.stream_attachments_to_s3_zip")
    def test_upload_to_s3_streaming_csv_success(
        self, mock_stream_zip, mock_create_url, mock_get_client,
        mock_privacy_request, sample_data, storage_secrets, mock_s3_client
    ):
        """Test successful CSV upload with streaming."""
        self.setup_upload_mocks(mock_get_client, mock_s3_client, mock_stream_zip, mock_create_url)

        url, metrics = self.call_upload_function(
            upload_to_s3_streaming, storage_secrets, sample_data, mock_privacy_request,
            ResponseFormat.csv.value, "test-file.csv"
        )

        assert url == "https://presigned-url.com"
        assert isinstance(metrics, ProcessingMetrics)
        mock_stream_zip.assert_called_once()

    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    @patch("fides.api.service.storage.streaming_s3.create_presigned_url_for_s3")
    @patch("fides.api.service.storage.streaming_s3.stream_html_to_s3_multipart")
    def test_upload_to_s3_streaming_html_success(
        self, mock_stream_html, mock_create_url, mock_get_client,
        mock_privacy_request, sample_data, storage_secrets, mock_s3_client
    ):
        """Test successful HTML upload with streaming."""
        self.setup_upload_mocks(mock_get_client, mock_s3_client, mock_create_url=mock_create_url)

        url, metrics = self.call_upload_function(
            upload_to_s3_streaming, storage_secrets, sample_data, mock_privacy_request,
            ResponseFormat.html.value, "test-file.html"
        )

        assert url == "https://presigned-url.com"
        assert isinstance(metrics, ProcessingMetrics)
        mock_stream_html.assert_called_once()

    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    def test_upload_to_s3_streaming_unsupported_format(
        self, mock_get_client, mock_privacy_request, sample_data,
        storage_secrets, mock_s3_client
    ):
        """Test upload with unsupported format raises error."""
        self.setup_upload_mocks(mock_get_client, mock_s3_client)

        with pytest.raises(StorageUploadError, match="Unexpected error during streaming upload"):
            self.call_upload_function(
                upload_to_s3_streaming, storage_secrets, sample_data, mock_privacy_request,
                "xml", "test-file.xml"
            )

    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    def test_upload_to_s3_streaming_no_privacy_request(
        self, mock_get_client, sample_data, storage_secrets
    ):
        """Test upload without privacy request raises error."""
        mock_get_client.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameter", "Message": "Invalid credentials"}},
            "GetObject"
        )

        with pytest.raises(ValueError, match="Privacy request must be provided"):
            self.call_upload_function_with_none_privacy_request(
                upload_to_s3_streaming, storage_secrets, sample_data,
                ResponseFormat.json.value, "test-file.json"
            )

    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    def test_upload_to_s3_streaming_s3_client_error(
        self, mock_get_client, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test upload with S3 client error raises StorageUploadError."""
        mock_get_client.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameter", "Message": "Invalid credentials"}},
            "GetObject"
        )

        with pytest.raises(StorageUploadError, match="Error getting s3 client"):
            self.call_upload_function(
                upload_to_s3_streaming, storage_secrets, sample_data, mock_privacy_request,
                ResponseFormat.json.value, "test-file.json"
            )

    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    @patch("fides.api.service.storage.streaming_s3.stream_attachments_to_s3_zip")
    def test_upload_to_s3_streaming_upload_error(
        self, mock_stream_zip, mock_get_client, mock_privacy_request,
        sample_data, storage_secrets, mock_s3_client
    ):
        """Test upload with streaming error raises StorageUploadError."""
        self.setup_upload_mocks(mock_get_client, mock_s3_client)
        mock_stream_zip.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "PutObject"
        )

        with pytest.raises(StorageUploadError, match="Error uploading to S3"):
            self.call_upload_function(
                upload_to_s3_streaming, storage_secrets, sample_data, mock_privacy_request,
                ResponseFormat.json.value, "test-file.json"
            )

    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    @patch("fides.api.service.storage.streaming_s3.stream_attachments_to_s3_zip")
    @patch("fides.api.service.storage.streaming_s3.create_presigned_url_for_s3")
    def test_upload_to_s3_streaming_presigned_url_error(
        self, mock_create_url, mock_stream_zip, mock_get_client,
        mock_privacy_request, sample_data, storage_secrets, mock_s3_client
    ):
        """Test upload with presigned URL error raises StorageUploadError."""
        self.setup_upload_mocks(mock_get_client, mock_s3_client, mock_stream_zip)
        mock_create_url.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "GetObject"
        )

        with pytest.raises(StorageUploadError, match="Error uploading to S3"):
            self.call_upload_function(
                upload_to_s3_streaming, storage_secrets, sample_data, mock_privacy_request,
                ResponseFormat.json.value, "test-file.json"
            )

    @patch("fides.api.service.storage.streaming_s3.upload_to_s3_streaming")
    @patch("fides.api.service.storage.streaming_s3.get_s3_client")
    def test_upload_to_s3_streaming_advanced_delegates(
        self, mock_get_client, mock_upload, mock_privacy_request, sample_data, storage_secrets
    ):
        """Test that advanced function delegates to main function."""
        mock_get_client.return_value = mock_s3_client
        mock_upload.return_value = ("https://presigned-url.com", ProcessingMetrics())

        url, metrics = self.call_upload_function(
            upload_to_s3_streaming_advanced, storage_secrets, sample_data, mock_privacy_request,
            ResponseFormat.json.value, "test-file.json"
        )

        assert url == "https://presigned-url.com"
        assert isinstance(metrics, ProcessingMetrics)
        mock_upload.assert_called_once()


class TestStreamAttachmentsToS3Zip:
    """Test the stream_attachments_to_s3_zip function."""

    @patch("fides.api.service.storage.streaming_s3.should_split_package")
    @patch("fides.api.service.storage.streaming_s3.split_data_into_packages")
    def test_stream_attachments_to_s3_zip_with_package_splitting(
        self, mock_split_packages, mock_should_split, mock_privacy_request,
        sample_data, mock_s3_client
    ):
        """Test streaming with package splitting."""
        mock_should_split.return_value = True
        mock_split_packages.return_value = [
            {"users": sample_data["users"][:1]},
            {"users": sample_data["users"][1:], "orders": sample_data["orders"]}
        ]

        # Mock the recursive call to avoid infinite recursion
        with patch("fides.api.service.storage.streaming_s3.stream_attachments_to_s3_zip") as mock_recursive:
            mock_recursive.return_value = ProcessingMetrics()

            metrics = stream_attachments_to_s3_zip(
                mock_s3_client, "test-bucket", "test-key", sample_data,
                mock_privacy_request
            )

            assert isinstance(metrics, ProcessingMetrics)
            mock_split_packages.assert_called_once()

    @patch("fides.api.service.storage.streaming_s3.should_split_package")
    def test_stream_attachments_to_s3_zip_without_splitting(
        self, mock_should_split, mock_privacy_request, sample_data, mock_s3_client
    ):
        """Test streaming without package splitting."""
        mock_should_split.return_value = False

        # Mock the internal functions to avoid actual processing
        with patch("fides.api.service.storage.streaming_s3.stream_single_attachment_to_zip_streaming_with_metrics"), \
             patch("fides.api.service.storage.streaming_s3.upload_zip_part") as mock_upload_part:

            mock_upload_part.return_value = {"ETag": "test-etag", "PartNumber": 1}

            metrics = stream_attachments_to_s3_zip(
                mock_s3_client, "test-bucket", "test-key", sample_data,
                mock_privacy_request
            )

            assert isinstance(metrics, ProcessingMetrics)
            assert metrics.total_attachments == 4  # 2 + 1 + 1 from sample_data


class TestDownloadChunkWithRetry:
    """Test the download_chunk_with_retry function."""

    def test_download_chunk_with_retry_success(self, mock_s3_client):
        """Test successful chunk download."""
        mock_s3_client.get_object.return_value = {"Body": BytesIO(b"test content")}

        result = download_chunk_with_retry(
            mock_s3_client, "test-bucket", "test-key", 0, 1024, max_retries=3
        )

        assert result == b"test content"

    def test_download_chunk_with_retry_failure(self, mock_s3_client):
        """Test chunk download with retries and eventual failure."""
        mock_s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            "GetObject"
        )

        with pytest.raises(ClientError):
            download_chunk_with_retry(
                mock_s3_client, "test-bucket", "test-key", 0, 1024, max_retries=3
            )


class TestUploadZipPart:
    """Test the upload_zip_part function."""

    def test_upload_zip_part_success(self, mock_s3_client):
        """Test successful zip part upload."""
        mock_s3_client.upload_part.return_value = {"ETag": "test-etag"}

        result = upload_zip_part(
            mock_s3_client, "test-bucket", "test-upload-id", 1, BytesIO(b"test content")
        )

        assert result["ETag"] == "test-etag"
        assert result["PartNumber"] == 1
        mock_s3_client.upload_part.assert_called_once()

    def test_upload_zip_part_failure(self, mock_s3_client):
        """Test zip part upload failure."""
        mock_s3_client.upload_part.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "UploadPart"
        )

        with pytest.raises(ClientError):
            upload_zip_part(
                mock_s3_client, "test-bucket", "test-upload-id", 1, BytesIO(b"test content")
            )


class TestStreamHTMLToS3Multipart:
    """Test the stream_html_to_s3_multipart function."""

    @patch("fides.api.service.storage.streaming_s3.DsrReportBuilder")
    def test_stream_html_to_s3_multipart_success(
        self, mock_dsr_builder, mock_privacy_request, sample_data, mock_s3_client
    ):
        """Test successful HTML streaming to S3."""
        mock_builder = MagicMock()
        mock_builder.build_html_report.return_value = "<html>Test Report</html>"
        mock_dsr_builder.return_value = mock_builder

        # Mock the multipart upload process
        mock_s3_client.create_multipart_upload.return_value = {"UploadId": "test-upload-id"}
        mock_s3_client.upload_part.return_value = {"ETag": "test-etag"}
        mock_s3_client.complete_multipart_upload.return_value = {"Location": "s3://bucket/test-key"}

        stream_html_to_s3_multipart(
            mock_s3_client, "test-bucket", "test-key", sample_data, mock_privacy_request
        )

        mock_s3_client.create_multipart_upload.assert_called_once()
        mock_s3_client.upload_part.assert_called()
        mock_s3_client.complete_multipart_upload.assert_called_once()

    def test_stream_html_to_s3_multipart_upload_failure(self, mock_privacy_request, sample_data, mock_s3_client):
        """Test HTML streaming with upload failure."""
        mock_s3_client.create_multipart_upload.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "CreateMultipartUpload"
        )

        with pytest.raises(ClientError):
            stream_html_to_s3_multipart(
                mock_s3_client, "test-bucket", "test-key", sample_data, mock_privacy_request
            )


class TestStreamSingleAttachmentToZipStreamingWithMetrics(BaseStreamingTest):
    """Test the stream_single_attachment_to_zip_streaming_with_metrics function."""

    @patch("fides.api.service.storage.streaming_s3.adaptive_chunk_size")
    @patch("fides.api.service.storage.streaming_s3.download_chunk_with_retry")
    def test_stream_single_attachment_to_zip_streaming_with_metrics_success(
        self, mock_download_chunk, mock_adaptive_chunk_size, mock_privacy_request, mock_s3_client,
        create_zip_file, create_metrics
    ):
        """Test successful attachment streaming with metrics."""
        # Setup mocks
        self.setup_mock_chunk_download(mock_download_chunk, mock_adaptive_chunk_size)
        self.setup_mock_s3_head(mock_s3_client, 2048)  # 2KB file

        # Create test objects
        zip_buffer, zip_file = create_zip_file()
        metrics = create_metrics
        attachment = self.create_test_attachment()

        # Call the function
        result = stream_single_attachment_to_zip_streaming_with_metrics(
            mock_s3_client, "test-bucket", attachment, zip_file, "test/path", metrics
        )

        # Verify the result
        assert result['processed_bytes'] == 2048
        assert result['chunks'] == 2  # 2048 bytes / 1024 bytes per chunk
        assert result['chunk_size'] == 1024

        # Verify metrics were reset
        self.verify_metrics_reset(metrics)

        # Verify S3 calls
        mock_s3_client.head_object.assert_called_once_with(Bucket="test-bucket", Key="test-bucket/test-file.txt")
        assert mock_download_chunk.call_count == 2  # Called for each chunk

        # Verify zip file operations
        zip_file.close()
        self.verify_zip_file_contents(zip_buffer, 2)  # Two parts due to buffer threshold

    @patch("fides.api.service.storage.streaming_s3.adaptive_chunk_size")
    @patch("fides.api.service.storage.streaming_s3.download_chunk_with_retry")
    def test_stream_single_attachment_to_zip_streaming_with_metrics_small_file(
        self, mock_download_chunk, mock_adaptive_chunk_size, mock_privacy_request, mock_s3_client,
        create_zip_file, create_metrics
    ):
        """Test attachment streaming for small files that fit in one chunk."""
        # Setup mocks
        self.setup_mock_chunk_download(mock_download_chunk, mock_adaptive_chunk_size, chunk_data=b"small file")
        self.setup_mock_s3_head(mock_s3_client, 512)  # 512 bytes

        # Create test objects
        zip_buffer, zip_file = create_zip_file()
        metrics = create_metrics
        attachment = self.create_test_attachment('test-bucket/small-file.txt', 'small-file.txt')

        # Call the function
        result = stream_single_attachment_to_zip_streaming_with_metrics(
            mock_s3_client, "test-bucket", attachment, zip_file, "test/path", metrics
        )

        # Verify the result
        assert result['processed_bytes'] == 512
        assert result['chunks'] == 1  # Single chunk
        assert result['chunk_size'] == 1024

        # Verify S3 calls
        mock_s3_client.head_object.assert_called_once()
        mock_download_chunk.assert_called_once()  # Only one chunk

        zip_file.close()

    @patch("fides.api.service.storage.streaming_s3.adaptive_chunk_size")
    def test_stream_single_attachment_to_zip_streaming_with_metrics_head_object_failure(
        self, mock_adaptive_chunk_size, mock_privacy_request, mock_s3_client,
        create_zip_file, create_metrics
    ):
        """Test attachment streaming when head_object fails."""
        # Mock S3 head_object failure
        mock_s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            "HeadObject"
        )

        # Create test objects
        zip_buffer, zip_file = create_zip_file()
        metrics = create_metrics
        attachment = self.create_test_attachment('test-bucket/missing-file.txt', 'missing-file.txt')

        # Call the function and expect it to fail
        with pytest.raises(ClientError):
            stream_single_attachment_to_zip_streaming_with_metrics(
                mock_s3_client, "test-bucket", attachment, zip_file, "test/path", metrics
            )

        # Verify metrics were reset even on failure
        self.verify_metrics_reset(metrics)

        zip_file.close()

    @patch("fides.api.service.storage.streaming_s3.adaptive_chunk_size")
    @patch("fides.api.service.storage.streaming_s3.download_chunk_with_retry")
    def test_stream_single_attachment_to_zip_streaming_with_metrics_download_failure(
        self, mock_download_chunk, mock_adaptive_chunk_size, mock_privacy_request, mock_s3_client,
        create_zip_file, create_metrics
    ):
        """Test attachment streaming when chunk download fails."""
        # Setup mocks
        self.setup_mock_chunk_download(mock_download_chunk, mock_adaptive_chunk_size)
        mock_download_chunk.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "GetObject"
        )
        self.setup_mock_s3_head(mock_s3_client, 2048)  # 2KB file

        # Create test objects
        zip_buffer, zip_file = create_zip_file()
        metrics = create_metrics
        attachment = self.create_test_attachment()

        # Call the function and expect it to fail
        with pytest.raises(ClientError):
            stream_single_attachment_to_zip_streaming_with_metrics(
                mock_s3_client, "test-bucket", attachment, zip_file, "test/path", metrics
            )

        # Verify metrics were reset even on failure
        self.verify_metrics_reset(metrics)

        zip_file.close()

    @patch("fides.api.service.storage.streaming_s3.adaptive_chunk_size")
    @patch("fides.api.service.storage.streaming_s3.download_chunk_with_retry")
    def test_stream_single_attachment_to_zip_streaming_with_metrics_progress_callback(
        self, mock_download_chunk, mock_adaptive_chunk_size, mock_privacy_request, mock_s3_client,
        create_zip_file, create_metrics
    ):
        """Test attachment streaming with progress callback."""
        # Setup mocks
        self.setup_mock_chunk_download(mock_download_chunk, mock_adaptive_chunk_size)
        self.setup_mock_s3_head(mock_s3_client, 2048)  # 2KB file

        # Create test objects
        zip_buffer, zip_file = create_zip_file()
        metrics = create_metrics
        attachment = self.create_test_attachment()

        # Track progress callback calls
        progress_calls = []
        def progress_callback(metrics_obj):
            progress_calls.append(metrics_obj.current_attachment_progress)

        # Call the function
        result = stream_single_attachment_to_zip_streaming_with_metrics(
            mock_s3_client, "test-bucket", attachment, zip_file, "test/path", metrics, progress_callback
        )

        # Verify progress callback was called
        assert len(progress_calls) > 0
        # Progress should go from 0 to 100
        assert progress_calls[0] == 50.0  # First chunk: 1/2 * 100
        assert progress_calls[-1] == 100.0  # Last chunk: 2/2 * 100

        zip_file.close()

    @patch("fides.api.service.storage.streaming_s3.adaptive_chunk_size")
    @patch("fides.api.service.storage.streaming_s3.download_chunk_with_retry")
    def test_stream_single_attachment_to_zip_streaming_with_metrics_default_filename(
        self, mock_download_chunk, mock_adaptive_chunk_size, mock_privacy_request, mock_s3_client,
        create_zip_file, create_metrics
    ):
        """Test attachment streaming with default filename when file_name is not provided."""
        # Setup mocks
        self.setup_mock_chunk_download(mock_download_chunk, mock_adaptive_chunk_size)
        self.setup_mock_s3_head(mock_s3_client, 1024)  # 1KB file

        # Create test objects
        zip_buffer, zip_file = create_zip_file()
        metrics = create_metrics

        # Test attachment data without file_name
        attachment = {
            's3_key': 'test-bucket/test-file.txt'
            # No file_name key
        }

        # Call the function
        result = stream_single_attachment_to_zip_streaming_with_metrics(
            mock_s3_client, "test-bucket", attachment, zip_file, "test/path", metrics
        )

        # Verify the result
        assert result['processed_bytes'] == 1024
        assert result['chunks'] == 1

        # Verify metrics were updated with default filename
        assert metrics.current_attachment == "attachment"  # Default value

        zip_file.close()

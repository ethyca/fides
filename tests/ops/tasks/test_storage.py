import ast
import json
import zipfile
from io import BytesIO
from unittest.mock import MagicMock, create_autospec, patch

import pandas as pd
import pytest
from botocore.exceptions import ParamValidationError
from google.cloud.storage import Blob, Bucket, Client

from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    ResponseFormat,
    StorageDetails,
)
from fides.api.tasks.storage import (
    convert_to_encrypted_json,
    upload_to_gcs,
    upload_to_local,
    upload_to_s3,
    write_to_in_memory_buffer,
)
from fides.config import CONFIG


@patch("fides.api.tasks.storage.write_to_in_memory_buffer", autospec=True)
@patch("fides.api.tasks.storage.get_gcs_client", autospec=True)
class TestUploadToGCS:
    def test_upload_to_gcs_success(
        self, mock_get_gcs_client, mock_write_to_in_memory_buffer
    ):
        mock_storage_client = create_autospec(Client)
        mock_bucket = create_autospec(Bucket)
        mock_blob = create_autospec(Blob)
        mock_in_memory_file = MagicMock()

        mock_get_gcs_client.return_value = mock_storage_client
        mock_storage_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_write_to_in_memory_buffer.return_value = mock_in_memory_file
        mock_blob.generate_signed_url.return_value = "http://example.com/signed-url"

        privacy_request = MagicMock(id="test-request-id")

        result = upload_to_gcs(
            storage_secrets={"private_key_id": "test-private-key-id"},
            data={"key": "value"},
            bucket_name="test-bucket",
            file_key="test-file",
            resp_format=ResponseFormat.json.value,
            privacy_request=privacy_request,
            auth_method="test-auth-method",
        )

        mock_get_gcs_client.assert_called_once_with(
            "test-auth-method", {"private_key_id": "test-private-key-id"}
        )
        mock_storage_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.blob.assert_called_once_with("test-file")
        mock_write_to_in_memory_buffer.assert_called_once_with(
            ResponseFormat.json.value, {"key": "value"}, privacy_request
        )
        mock_blob.upload_from_string.assert_called_once_with(
            mock_in_memory_file.getvalue(), content_type="application/json"
        )
        mock_blob.generate_signed_url.assert_called_once_with(
            version="v4",
            expiration=CONFIG.security.subject_request_download_link_ttl_seconds,
            method="GET",
        )
        assert result == "http://example.com/signed-url"

    @patch("fides.api.tasks.storage.logger", autospec=True)
    def test_upload_to_gcs_exception(
        self, mock_logger, mock_get_gcs_client, mock_write_to_in_memory_buffer
    ):
        mock_storage_client = create_autospec(Client)
        mock_bucket = create_autospec(Bucket)
        mock_blob = create_autospec(Blob)
        mock_in_memory_file = MagicMock()

        mock_get_gcs_client.return_value = mock_storage_client
        mock_storage_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_write_to_in_memory_buffer.return_value = mock_in_memory_file
        error = Exception("Upload failed")
        mock_blob.upload_from_string.side_effect = error

        privacy_request = MagicMock(id="test-request-id")

        with pytest.raises(Exception) as excinfo:
            upload_to_gcs(
                storage_secrets={"private_key_id": "test-private-key-id"},
                data={"key": "value"},
                bucket_name="test-bucket",
                file_key="test-file",
                resp_format=ResponseFormat.csv.value,
                privacy_request=privacy_request,
                auth_method="test-auth-method",
            )

        mock_get_gcs_client.assert_called_once_with(
            "test-auth-method", {"private_key_id": "test-private-key-id"}
        )
        mock_storage_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.blob.assert_called_once_with("test-file")
        mock_write_to_in_memory_buffer.assert_called_once_with(
            ResponseFormat.csv.value, {"key": "value"}, privacy_request
        )
        mock_blob.upload_from_string.assert_called_once_with(
            mock_in_memory_file.getvalue(), content_type="application/zip"
        )
        mock_blob.generate_signed_url.assert_not_called()

        # Check that both error messages were logged
        assert mock_logger.error.call_count == 2
        mock_logger.error.assert_any_call("Error uploading to GCS: Upload failed")
        mock_logger.error.assert_any_call(
            "Encountered error while uploading and generating link for Google Cloud Storage object: {}",
            error,
        )
        assert "Upload failed" in str(excinfo.value)


class TestWriteToInMemoryBuffer:
    def test_write_to_in_memory_buffer_json(self):
        data = {"key": "value"}
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.json.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        assert "key" in content
        assert "value" in content

    def test_write_to_in_memory_buffer_csv(self):
        data = {"key": "value"}
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.csv.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        with zipfile.ZipFile(result) as zip_file:
            assert "key.csv" in zip_file.namelist()

    def test_write_to_in_memory_buffer_invalid_format(self):
        data = {"key": "value"}
        privacy_request = MagicMock(id="test-request-id")

        with pytest.raises(NotImplementedError):
            write_to_in_memory_buffer("invalid_format", data, privacy_request)

    @patch("fides.api.tasks.storage.DsrReportBuilder")
    def test_write_to_in_memory_buffer_html(self, mock_dsr_builder):
        """Test HTML format generation using DsrReportBuilder."""
        data = {"key": "value"}
        privacy_request = MagicMock(id="test-request-id")
        mock_report = BytesIO(b"<html>Test Report</html>")
        mock_dsr_builder.return_value.generate.return_value = mock_report

        result = write_to_in_memory_buffer(
            ResponseFormat.html.value, data, privacy_request
        )

        mock_dsr_builder.assert_called_once_with(
            privacy_request=privacy_request,
            dsr_data=data,
        )
        assert result == mock_report

    def test_write_to_in_memory_buffer_with_attachments(self):
        """Test handling of data with attachments."""
        data = {
            "user": {
                "name": "Test User",
                "attachments": [
                    {
                        "file_name": "test.pdf",
                        "content": "base64_encoded_content",
                        "file_size": 1024,
                    }
                ],
            }
        }
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.json.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        json_content = json.loads(content)
        assert "user" in json_content
        assert "attachments" in json_content["user"]
        assert len(json_content["user"]["attachments"]) == 1
        attachment = json_content["user"]["attachments"][0]
        assert "file_name" in attachment
        assert "content" not in attachment  # Content should be removed
        assert "file_size" in attachment

    def test_write_to_in_memory_buffer_top_level_attachments_json(self):
        """Test handling of top-level attachments in JSON format."""
        data = {
            "attachments": [
                {
                    "file_name": "doc1.pdf",
                    "content": "base64_content_1",
                    "file_size": 1024,
                    "content_type": "application/pdf",
                },
                {
                    "file_name": "doc2.pdf",
                    "content": "base64_content_2",
                    "file_size": 2048,
                    "content_type": "application/pdf",
                },
            ],
            "metadata": {"type": "document_package"},
        }
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.json.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        json_content = json.loads(content)
        assert "attachments" in json_content
        assert "metadata" in json_content
        assert len(json_content["attachments"]) == 2
        for attachment in json_content["attachments"]:
            assert "file_name" in attachment
            assert "content" not in attachment
            assert "file_size" in attachment
            assert "content_type" in attachment

    def test_write_to_in_memory_buffer_top_level_attachments_csv(self):
        """Test handling of top-level attachments in CSV format."""
        data = {
            "attachments": [
                {
                    "file_name": "doc1.pdf",
                    "content": "base64_content_1",
                    "file_size": 1024,
                    "content_type": "application/pdf",
                },
                {
                    "file_name": "doc2.pdf",
                    "content": "base64_content_2",
                    "file_size": 2048,
                    "content_type": "application/pdf",
                },
            ],
            "metadata": {"type": "document_package"},
        }
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.csv.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        with zipfile.ZipFile(result) as zip_file:
            # Check for individual attachment CSV files
            assert "attachments/1/data.csv" in zip_file.namelist()
            assert "attachments/2/data.csv" in zip_file.namelist()
            assert "metadata.csv" in zip_file.namelist()

            # Verify attachment data is properly written
            attachment1_data = pd.read_csv(zip_file.open("attachments/1/data.csv"))
            assert "file_name" in attachment1_data.columns
            assert "file_size" in attachment1_data.columns
            assert "content_type" in attachment1_data.columns
            assert (
                "content" not in attachment1_data.columns
            )  # Content should be removed
            assert attachment1_data.iloc[0]["file_name"] == "doc1.pdf"
            assert attachment1_data.iloc[0]["file_size"] == 1024

            attachment2_data = pd.read_csv(zip_file.open("attachments/2/data.csv"))
            assert attachment2_data.iloc[0]["file_name"] == "doc2.pdf"
            assert attachment2_data.iloc[0]["file_size"] == 2048

    def test_write_to_in_memory_buffer_manual_webhook_attachments_json(self):
        """Test handling of attachments in manual webhook data (JSON format)."""
        data = {
            "manual_webhook": [
                {
                    "id": "webhook1",
                    "data": {
                        "name": "Test User",
                        "email": "test@example.com",
                    },
                    "attachments": [
                        {
                            "file_name": "webhook1_doc.pdf",
                            "content": "base64_content_1",
                            "file_size": 1024,
                            "content_type": "application/pdf",
                        }
                    ],
                },
                {
                    "id": "webhook2",
                    "data": {
                        "name": "Another User",
                        "email": "another@example.com",
                    },
                    "attachments": [
                        {
                            "file_name": "webhook2_doc.pdf",
                            "content": "base64_content_2",
                            "file_size": 2048,
                            "content_type": "application/pdf",
                        }
                    ],
                },
            ]
        }
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.json.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        json_content = json.loads(content)
        assert "manual_webhook" in json_content
        assert len(json_content["manual_webhook"]) == 2

        for webhook in json_content["manual_webhook"]:
            assert "id" in webhook
            assert "data" in webhook
            assert "attachments" in webhook
            for attachment in webhook["attachments"]:
                assert "file_name" in attachment
                assert "content" not in attachment
                assert "file_size" in attachment
                assert "content_type" in attachment

    def test_write_to_in_memory_buffer_manual_webhook_attachments_csv(self):
        """Test handling of attachments in manual webhook data (CSV format)."""
        data = {
            "manual_webhook": [
                {
                    "id": "webhook1",
                    "data": {
                        "name": "Test User",
                        "email": "test@example.com",
                    },
                    "attachments": [
                        {
                            "file_name": "webhook1_doc.pdf",
                            "content": "base64_content_1",
                            "file_size": 1024,
                            "content_type": "application/pdf",
                        }
                    ],
                },
                {
                    "id": "webhook2",
                    "data": {
                        "name": "Another User",
                        "email": "another@example.com",
                    },
                    "attachments": [
                        {
                            "file_name": "webhook2_doc.pdf",
                            "content": "base64_content_2",
                            "file_size": 2048,
                            "content_type": "application/pdf",
                        }
                    ],
                },
            ]
        }
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.csv.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        with zipfile.ZipFile(result) as zip_file:
            assert "manual_webhook/1/data.csv" in zip_file.namelist()
            assert "manual_webhook/1/attachments.csv" in zip_file.namelist()
            assert "manual_webhook/2/data.csv" in zip_file.namelist()
            assert "manual_webhook/2/attachments.csv" in zip_file.namelist()

    def test_write_to_in_memory_buffer_nested_data(self):
        """Test handling of deeply nested data structures."""
        data = {
            "user": {
                "profile": {
                    "personal": {
                        "name": "Test User",
                        "address": {
                            "street": "123 Main St",
                            "city": "Test City",
                        },
                    },
                    "preferences": {
                        "theme": "dark",
                        "notifications": True,
                    },
                },
                "orders": [
                    {
                        "id": "order1",
                        "items": ["item1", "item2"],
                    },
                    {
                        "id": "order2",
                        "items": ["item3"],
                    },
                ],
            }
        }
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.json.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        json_content = json.loads(content)
        assert "user" in json_content
        assert "profile" in json_content["user"]
        assert "personal" in json_content["user"]["profile"]
        assert "orders" in json_content["user"]
        assert len(json_content["user"]["orders"]) == 2

    def test_write_to_in_memory_buffer_empty_data(self):
        """Test handling of empty data."""
        data = {}
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.json.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        json_content = json.loads(content)
        assert json_content == {}

    def test_write_to_in_memory_buffer_special_characters(self):
        """Test handling of data with special characters."""
        data = {
            "text": "Special chars: !@#$%^&*()_+{}|:\"<>?[]\\;',./",
            "unicode": "Unicode chars: 你好世界",
            "newlines": "Line 1\nLine 2\r\nLine 3",
        }
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.json.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        json_content = json.loads(content)
        assert json_content["text"] == data["text"]
        assert json_content["unicode"] == data["unicode"]
        assert json_content["newlines"] == data["newlines"]

    def test_write_to_in_memory_buffer_csv_nested_data(self):
        """Test CSV generation with nested data structures."""
        data = {
            "user": {
                "name": "Test User",
                "orders": [
                    {"id": "order1", "total": 100},
                    {"id": "order2", "total": 200},
                ],
            }
        }
        privacy_request = MagicMock(id="test-request-id")

        result = write_to_in_memory_buffer(
            ResponseFormat.csv.value, data, privacy_request
        )

        assert isinstance(result, BytesIO)
        with zipfile.ZipFile(result) as zip_file:
            assert "user.csv" in zip_file.namelist()
            # Verify the orders data is included in the user.csv file
            user_data = pd.read_csv(zip_file.open("user.csv"))
            assert "user.name" in user_data.columns
            assert "user.orders" in user_data.columns
            assert user_data.iloc[0]["user.name"] == "Test User"
            # Use ast.literal_eval() to parse Python literal syntax
            actual_orders = ast.literal_eval(user_data.iloc[0]["user.orders"])
            expected_orders = [
                {"id": "order1", "total": 100},
                {"id": "order2", "total": 200},
            ]
            assert actual_orders == expected_orders


class TestConvertToEncryptedJSON:
    def test_convert_to_encrypted_json(self):
        data = {"key": "value"}
        request_id = "test-request-id"

        result = convert_to_encrypted_json(data, request_id)

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        assert isinstance(content, str)
        assert content != json.dumps(data)  # Should be encrypted


@patch("fides.api.tasks.storage.write_to_in_memory_buffer")
class TestUploadToS3:
    def test_upload_to_s3_success(
        self, mock_write_to_in_memory_buffer, s3_client, monkeypatch, storage_config
    ):
        def mock_get_s3_client(auth_method, storage_secrets, assume_role_arn=None):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
        mock_in_memory_file = BytesIO(b"test data")
        mock_write_to_in_memory_buffer.return_value = mock_in_memory_file

        privacy_request = MagicMock(id="test-request-id")

        result = upload_to_s3(
            storage_secrets={
                "aws_access_key_id": "fake_access_key",
                "aws_secret_access_key": "fake_secret_key",
                "region_name": "us-east-1",
            },
            data={"key": "value"},
            bucket_name=storage_config.details[StorageDetails.BUCKET.value],
            file_key="test-file.txt",
            resp_format=ResponseFormat.json.value,
            privacy_request=privacy_request,
            document=None,
            auth_method=AWSAuthMethod.SECRET_KEYS.value,
        )

        assert result.startswith(
            "https://s3.amazonaws.com/test_bucket/test-file.txt?AWSAccessKeyId"
        )

    def test_upload_to_s3_document_only(
        self, mock_write_to_in_memory_buffer, s3_client, monkeypatch, storage_config
    ):
        """Test uploading a document directly without a privacy request."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
        document = BytesIO(b"test document data")

        result = upload_to_s3(
            storage_secrets={
                "aws_access_key_id": "fake_access_key",
                "aws_secret_access_key": "fake_secret_key",
                "region_name": "us-east-1",
            },
            data={},
            bucket_name=storage_config.details[StorageDetails.BUCKET.value],
            file_key="test-file.txt",
            resp_format=ResponseFormat.json.value,
            privacy_request=None,
            document=document,
            auth_method=AWSAuthMethod.SECRET_KEYS.value,
        )

        mock_write_to_in_memory_buffer.assert_not_called()
        assert result.startswith(
            "https://s3.amazonaws.com/test_bucket/test-file.txt?AWSAccessKeyId"
        )

    def test_upload_to_s3_missing_privacy_request(
        self, mock_write_to_in_memory_buffer, s3_client, monkeypatch
    ):
        """Test that ValueError is raised when both privacy_request and document are None."""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_s3(
                storage_secrets={
                    "aws_access_key_id": "fake_access_key",
                    "aws_secret_access_key": "fake_secret_key",
                    "region_name": "us-east-1",
                },
                data={},
                bucket_name="test-bucket",
                file_key="test-file",
                resp_format=ResponseFormat.json.value,
                privacy_request=None,
                document=None,
                auth_method=AWSAuthMethod.SECRET_KEYS.value,
            )

        mock_write_to_in_memory_buffer.assert_not_called()

    def test_upload_to_s3_param_validation_error(
        self, mock_write_to_in_memory_buffer, s3_client, monkeypatch
    ):
        """Test handling of ParamValidationError during upload."""

        def mock_get_s3_client(auth_method, storage_secrets, assume_role_arn=None):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
        mock_in_memory_file = BytesIO(b"test data")
        mock_write_to_in_memory_buffer.return_value = mock_in_memory_file

        # Create a mock for the upload_fileobj method
        mock_upload = MagicMock()
        error = ParamValidationError(report="Invalid parameter value")
        mock_upload.side_effect = error
        # Replace the real method with our mock
        s3_client.upload_fileobj = mock_upload

        privacy_request = MagicMock(id="test-request-id")

        with pytest.raises(ValueError) as excinfo:
            upload_to_s3(
                storage_secrets={
                    "aws_access_key_id": "fake_access_key",
                    "aws_secret_access_key": "fake_secret_key",
                    "region_name": "us-east-1",
                },
                data={"key": "value"},
                bucket_name="test-bucket",
                file_key="test-file",
                resp_format=ResponseFormat.json.value,
                privacy_request=privacy_request,
                document=None,
                auth_method=AWSAuthMethod.SECRET_KEYS.value,
            )

        assert "The parameters you provided are incorrect" in str(excinfo.value)

    @patch("fides.api.tasks.storage.logger")
    def test_upload_to_s3_upload_error(
        self, mock_logger, mock_write_to_in_memory_buffer, s3_client, monkeypatch
    ):
        """Test handling of general upload errors."""

        def mock_get_s3_client(auth_method, storage_secrets, assume_role_arn=None):
            return s3_client

        monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
        mock_in_memory_file = BytesIO(b"test data")
        mock_write_to_in_memory_buffer.return_value = mock_in_memory_file

        privacy_request = MagicMock(id="test-request-id")

        with pytest.raises(Exception) as excinfo:
            upload_to_s3(
                storage_secrets={
                    "aws_access_key_id": "fake_access_key",
                    "aws_secret_access_key": "fake_secret_key",
                    "region_name": "us-east-1",
                },
                data={"key": "value"},
                bucket_name="non-existent-bucket",
                file_key="test-file",
                resp_format=ResponseFormat.json.value,
                privacy_request=privacy_request,
                document=None,
                auth_method=AWSAuthMethod.SECRET_KEYS.value,
            )

        assert "NoSuchBucket" in str(excinfo.value)
        assert mock_logger.error.call_count == 2
        mock_logger.error.assert_any_call(
            "Encountered error while uploading s3 object: {}", excinfo.value
        )
        mock_logger.error.assert_any_call(
            "Encountered error while uploading and generating link for s3 object: {}",
            excinfo.value,
        )


class TestUploadToLocal:
    @patch("fides.api.tasks.storage.write_to_in_memory_buffer")
    def test_upload_to_local(self, mock_write_to_in_memory_buffer):
        mock_in_memory_file = BytesIO(b"test data")
        mock_write_to_in_memory_buffer.return_value = mock_in_memory_file

        privacy_request = MagicMock(id="test-request-id")

        result = upload_to_local(
            data={"key": "value"},
            file_key="test-file",
            privacy_request=privacy_request,
            resp_format=ResponseFormat.json.value,
        )

        assert result == "your local fides_uploads folder"
        mock_write_to_in_memory_buffer.assert_called_once_with(
            ResponseFormat.json.value, {"key": "value"}, privacy_request
        )

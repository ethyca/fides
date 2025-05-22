import json
import zipfile
from io import BytesIO
from unittest.mock import MagicMock, create_autospec, patch

import pandas as pd
import pytest
from google.cloud.storage import Blob, Bucket, Client

from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.tasks.storage import (
    convert_to_encrypted_json,
    encrypt_access_request_results,
    upload_to_gcs,
    upload_to_local,
    upload_to_s3,
    write_to_in_memory_buffer,
)
from fides.api.util.cache import get_cache
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


class TestEncryptAccessRequestResults:
    @patch("fides.api.tasks.storage.get_cache")
    def test_encrypt_with_key(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        # Use a 16-byte key (16 hex characters)
        mock_cache.get.return_value = "0123456789abcdef"

        data = "test-data"
        request_id = "test-request-id"

        result = encrypt_access_request_results(data, request_id)

        assert result != data  # Data should be encrypted
        mock_cache.get.assert_called_once()

    @patch("fides.api.tasks.storage.get_cache")
    def test_encrypt_without_key(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None

        data = "test-data"
        request_id = "test-request-id"

        result = encrypt_access_request_results(data, request_id)

        assert result == data  # Data should remain unencrypted
        mock_cache.get.assert_called_once()


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


class TestConvertToEncryptedJSON:
    def test_convert_to_encrypted_json(self):
        data = {"key": "value"}
        request_id = "test-request-id"

        result = convert_to_encrypted_json(data, request_id)

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode(CONFIG.security.encoding)
        assert isinstance(content, str)
        assert content != json.dumps(data)  # Should be encrypted


@patch("fides.api.tasks.storage.get_s3_client")
@patch("fides.api.tasks.storage.write_to_in_memory_buffer")
class TestUploadToS3:
    def test_upload_to_s3_success(
        self, mock_write_to_in_memory_buffer, mock_get_s3_client
    ):
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_s3_client.generate_presigned_url.return_value = (
            "http://example.com/signed-url"
        )

        mock_in_memory_file = BytesIO(b"test data")
        mock_write_to_in_memory_buffer.return_value = mock_in_memory_file

        privacy_request = MagicMock(id="test-request-id")

        result = upload_to_s3(
            storage_secrets={"aws_access_key_id": "test-key"},
            data={"key": "value"},
            bucket_name="test-bucket",
            file_key="test-file",
            resp_format=ResponseFormat.json.value,
            privacy_request=privacy_request,
            document=None,
            auth_method="test-auth-method",
        )

        mock_get_s3_client.assert_called_once()
        mock_s3_client.upload_fileobj.assert_called_once()
        mock_s3_client.generate_presigned_url.assert_called_once()
        assert result == "http://example.com/signed-url"


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

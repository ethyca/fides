from unittest.mock import MagicMock, create_autospec, patch

import pytest
from google.cloud.storage import Blob, Bucket, Client

from fides.api.schemas.storage.storage import ResponseFormat
from fides.api.tasks.storage import upload_to_gcs
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
        mock_logger.error.assert_called_once_with(
            "Encountered error while uploading and generating link for Google Cloud Storage object: {}",
            error,
        )
        assert "Upload failed" in str(excinfo.value)

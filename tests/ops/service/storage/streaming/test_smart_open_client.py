"""Tests for SmartOpenStorageClient."""

from io import BytesIO, StringIO
from unittest.mock import Mock, create_autospec, patch

import pytest

from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.service.storage.streaming.base_storage_client import BaseStorageClient
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient
from fides.api.service.storage.streaming.storage_client_factory import (
    StorageClientFactory,
)


class TestSmartOpenStorageClient:
    """Test SmartOpenStorageClient functionality."""

    def test_init_with_s3_storage_type(self):
        """Test initialization with S3 storage type."""
        auth_method = "secret_keys"
        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID: "test_key",
            StorageSecrets.AWS_SECRET_ACCESS_KEY: "test_secret",
            StorageSecrets.REGION_NAME: "us-east-1",
        }

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            # Use create_autospec for the provider client to ensure proper interface compliance
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)

            assert client.storage_type == "s3"
            assert client.storage_secrets == storage_secrets
            assert client._provider_client == mock_provider_client
            mock_create.assert_called_once_with("s3", auth_method, storage_secrets)

    def test_init_with_gcs_storage_type(self):
        """Test initialization with GCS storage type."""
        # GCS is not yet implemented, so we'll use a mock that doesn't require real secrets
        auth_method = None
        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID: "test_key",  # Use S3 secrets for testing
            StorageSecrets.AWS_SECRET_ACCESS_KEY: "test_secret",
        }

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("gcs", auth_method, storage_secrets)

            assert client.storage_type == "gcs"
            assert client.storage_secrets == storage_secrets
            assert client._provider_client == mock_provider_client
            mock_create.assert_called_once_with("gcs", auth_method, storage_secrets)

    def test_init_with_azure_storage_type(self):
        """Test initialization with Azure storage type."""
        auth_method = None
        storage_secrets = {
            "azure_connection_string": "DefaultEndpointsProtocol=https;...",
        }

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("azure", auth_method, storage_secrets)

            assert client.storage_type == "azure"
            assert client.storage_secrets == storage_secrets
            assert client._provider_client == mock_provider_client
            mock_create.assert_called_once_with("azure", auth_method, storage_secrets)

    def test_init_normalizes_storage_type(self):
        """Test that storage type is normalized during initialization."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            # Test with uppercase
            client = SmartOpenStorageClient("S3", auth_method, storage_secrets)
            assert client.storage_type == "s3"

            # Test with mixed case
            client = SmartOpenStorageClient("GcS", auth_method, storage_secrets)
            assert client.storage_type == "gcs"

    def test_init_with_empty_storage_secrets(self):
        """Test initialization with empty storage secrets."""
        auth_method = None
        storage_secrets = {}

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            assert client.storage_secrets == {}
            mock_create.assert_called_once_with("s3", auth_method, storage_secrets)

    def test_init_with_none_storage_secrets(self):
        """Test initialization with None storage secrets."""
        auth_method = None
        storage_secrets = None

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            assert client.storage_secrets is None
            mock_create.assert_called_once_with("s3", auth_method, storage_secrets)

    def test_build_uri(self):
        """Test building URI for storage location."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/path/file.txt"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/path/file.txt"
            )
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            uri = client._build_uri(bucket, key)

            assert uri == "s3://test-bucket/test/path/file.txt"
            mock_provider_client.build_uri.assert_called_once_with(bucket, key)

    def test_build_uri_with_empty_key(self):
        """Test building URI with empty key."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = ""

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = "s3://test-bucket/"
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            uri = client._build_uri(bucket, key)

            assert uri == "s3://test-bucket/"
            mock_provider_client.build_uri.assert_called_once_with(bucket, key)

    def test_get_transport_params(self):
        """Test getting transport parameters for smart-open."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            params = client._get_transport_params()

            assert params == {"param1": "value1"}
            mock_provider_client.get_transport_params.assert_called_once()

    def test_get_transport_params_returns_empty_dict(self):
        """Test getting transport parameters when provider returns empty dict."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.get_transport_params.return_value = {}
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            params = client._get_transport_params()

            assert params == {}
            mock_provider_client.get_transport_params.assert_called_once()

    def test_put_object_with_file_like_object(self):
        """Test put_object with file-like object."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        content_type = "text/plain"
        file_data = BytesIO(b"test file content")

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.put_object(bucket, key, file_data, content_type)

                assert result["status"] == "success"
                assert result["uri"] == "s3://test-bucket/test/file.txt"
                mock_file.write.assert_called_once_with(b"test file content")

    def test_put_object_with_bytes(self):
        """Test put_object with bytes data."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        data = b"test bytes content"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.put_object(bucket, key, data)

                assert result["status"] == "success"
                mock_file.write.assert_called_once_with(b"test bytes content")

    def test_put_object_with_string(self):
        """Test put_object with string data."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        data = "test string content"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.put_object(bucket, key, data)

                assert result["status"] == "success"
                mock_file.write.assert_called_once_with(b"test string content")

    def test_put_object_with_other_object_type(self):
        """Test put_object with object that converts to string."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        data = {"key": "value"}  # Dict that converts to string

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.put_object(bucket, key, data)

                assert result["status"] == "success"
                mock_file.write.assert_called_once_with(b"{'key': 'value'}")

    def test_put_object_without_content_type(self):
        """Test put_object without content type."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        data = b"test content"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.put_object(bucket, key, data)

                assert result["status"] == "success"
                # Verify transport_params doesn't include content_type
                mock_smart_open.assert_called_once_with(
                    "s3://test-bucket/test/file.txt",
                    "wb",
                    transport_params={"param1": "value1"},
                )

    def test_put_object_without_metadata(self):
        """Test put_object without metadata."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        data = b"test content"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.put_object(bucket, key, data)

                assert result["status"] == "success"

    def test_put_object_handles_smart_open_error(self):
        """Test put_object handles smart_open errors gracefully."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        data = b"test content"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_smart_open.side_effect = Exception("smart_open error")

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)

                with pytest.raises(Exception, match="smart_open error"):
                    client.put_object(bucket, key, data)

    def test_get_object_success(self):
        """Test get_object successfully reads object content."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        expected_content = b"file content"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_file.read.return_value = expected_content
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.get_object(bucket, key)

                assert result == expected_content
                mock_file.read.assert_called_once()

    def test_get_object_handles_smart_open_error(self):
        """Test get_object handles smart_open errors gracefully."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_smart_open.side_effect = Exception("smart_open read error")

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)

                with pytest.raises(Exception, match="smart_open read error"):
                    client.get_object(bucket, key)

    def test_stream_upload_with_content_type(self):
        """Test streaming upload with content type."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        content_type = "text/plain"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_stream = Mock()
                mock_smart_open.return_value = mock_stream

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.stream_upload(bucket, key)

                assert result == mock_stream
                mock_provider_client.build_uri.assert_called_once_with(bucket, key)
                mock_provider_client.get_transport_params.assert_called_once()
                mock_smart_open.assert_called_once_with(
                    "s3://test-bucket/test/file.txt",
                    "wb",
                    transport_params={
                        "param1": "value1",
                    },
                )

    def test_stream_upload_without_content_type(self):
        """Test streaming upload without content type."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_stream = Mock()
                mock_smart_open.return_value = mock_stream

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.stream_upload(bucket, key)

                assert result == mock_stream
                mock_smart_open.assert_called_once_with(
                    "s3://test-bucket/test/file.txt",
                    "wb",
                    transport_params={"param1": "value1"},
                )

    def test_stream_upload_without_metadata(self):
        """Test streaming upload without metadata."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_stream = Mock()
                mock_smart_open.return_value = mock_stream

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.stream_upload(bucket, key)

                assert result == mock_stream
                mock_smart_open.assert_called_once_with(
                    "s3://test-bucket/test/file.txt",
                    "wb",
                    transport_params={"param1": "value1"},
                )

    def test_stream_read(self):
        """Test streaming read from storage."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_stream = Mock()
                mock_smart_open.return_value = mock_stream

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.stream_read(bucket, key)

                assert result == mock_stream
                mock_provider_client.build_uri.assert_called_once_with(bucket, key)
                mock_provider_client.get_transport_params.assert_called_once()
                mock_smart_open.assert_called_once_with(
                    "s3://test-bucket/test/file.txt",
                    "rb",
                    transport_params={"param1": "value1"},
                )

    def test_stream_read_with_empty_transport_params(self):
        """Test streaming read with empty transport parameters."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {}
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_stream = Mock()
                mock_smart_open.return_value = mock_stream

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.stream_read(bucket, key)

                assert result == mock_stream
                mock_smart_open.assert_called_once_with(
                    "s3://test-bucket/test/file.txt",
                    "rb",
                    transport_params={},
                )

    def test_create_multipart_upload(self):
        """Test creating multipart upload."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        content_type = "text/plain"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            result = client.create_multipart_upload(bucket, key, content_type)

            # The SmartOpenStorageClient.create_multipart_upload returns a dummy response
            # and doesn't call the provider client
            assert result.upload_id == "smart_open_streaming"
            assert result.metadata["storage_type"] == "s3"
            assert result.metadata["method"] == "streaming"

    def test_create_multipart_upload_without_metadata(self):
        """Test creating multipart upload without metadata."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        content_type = "text/plain"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            result = client.create_multipart_upload(bucket, key, content_type)

            assert result.upload_id == "smart_open_streaming"
            assert result.metadata["storage_type"] == "s3"
            assert result.metadata["method"] == "streaming"

    def test_create_multipart_upload_with_empty_content_type(self):
        """Test creating multipart upload with empty content type."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        content_type = ""

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            result = client.create_multipart_upload(bucket, key, content_type)

            assert result.upload_id == "smart_open_streaming"
            assert result.metadata["storage_type"] == "s3"
            assert result.metadata["method"] == "streaming"

    def test_upload_part(self):
        """Test uploading a part."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        upload_id = "upload_123"
        part_number = 1
        data = b"test data"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)

            # Mock the put_object method to avoid actual upload
            with patch.object(client, "put_object") as mock_put_object:
                result = client.upload_part(bucket, key, upload_id, part_number, data)

                assert result.part_number == part_number
                assert result.etag == "smart_open_part_1"
                assert result.metadata["storage_type"] == "s3"
                assert result.metadata["method"] == "streaming"

    def test_upload_part_with_empty_data(self):
        """Test uploading a part with empty data."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        upload_id = "upload_123"
        part_number = 1
        data = b""

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)

            with patch.object(client, "put_object") as mock_put_object:
                result = client.upload_part(bucket, key, upload_id, part_number, data)

                assert result.part_number == part_number
                assert result.etag == "smart_open_part_1"
                assert result.metadata["storage_type"] == "s3"
                assert result.metadata["method"] == "streaming"

    def test_upload_part_with_large_part_number(self):
        """Test uploading a part with large part number."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        upload_id = "upload_123"
        part_number = 999
        data = b"test data"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)

            with patch.object(client, "put_object") as mock_put_object:
                result = client.upload_part(bucket, key, upload_id, part_number, data)

                assert result.part_number == part_number
                assert result.etag == "smart_open_part_999"
                assert result.metadata["storage_type"] == "s3"
                assert result.metadata["method"] == "streaming"

    def test_generate_presigned_url(self):
        """Test generating presigned URL."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        expiration = 3600

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.generate_presigned_url.return_value = (
                "https://example.com/presigned"
            )
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            result = client.generate_presigned_url(bucket, key, expiration)

            assert result == "https://example.com/presigned"
            mock_provider_client.generate_presigned_url.assert_called_once_with(
                bucket, key, expiration
            )

    def test_generate_presigned_url_without_expiration(self):
        """Test generating presigned URL without expiration."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.generate_presigned_url.return_value = (
                "https://example.com/presigned"
            )
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            result = client.generate_presigned_url(bucket, key)

            assert result == "https://example.com/presigned"
            mock_provider_client.generate_presigned_url.assert_called_once_with(
                bucket, key, None
            )

    def test_generate_presigned_url_with_zero_expiration(self):
        """Test generating presigned URL with zero expiration."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        expiration = 0

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.generate_presigned_url.return_value = (
                "https://example.com/presigned"
            )
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            result = client.generate_presigned_url(bucket, key, expiration)

            assert result == "https://example.com/presigned"
            mock_provider_client.generate_presigned_url.assert_called_once_with(
                bucket, key, 0
            )

    def test_min_part_size_property(self):
        """Test that min_part_size property returns the expected value."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            assert client.min_part_size == 5242880  # 5MB default

    def test_min_part_size_is_class_attribute(self):
        """Test that min_part_size is a class attribute, not instance attribute."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            client1 = SmartOpenStorageClient("s3", auth_method, storage_secrets)
            client2 = SmartOpenStorageClient("gcs", auth_method, storage_secrets)

            # Both instances should have the same min_part_size
            assert client1.min_part_size == client2.min_part_size
            assert SmartOpenStorageClient.min_part_size == 5242880

    def test_storage_type_normalization_edge_cases(self):
        """Test storage type normalization with various edge cases."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_create.return_value = mock_provider_client

            # Test various case combinations
            test_cases = [
                ("S3", "s3"),
                ("GCS", "gcs"),
                ("AZURE", "azure"),
                ("s3", "s3"),
                ("gcs", "gcs"),
                ("azure", "azure"),
                ("S3", "s3"),
                ("GcS", "gcs"),
                ("AzUrE", "azure"),
            ]

            for input_type, expected_type in test_cases:
                client = SmartOpenStorageClient(
                    input_type, auth_method, storage_secrets
                )
                assert client.storage_type == expected_type
                mock_create.assert_called_with(input_type, auth_method, storage_secrets)
                mock_create.reset_mock()

    def test_put_object_handles_unicode_string(self):
        """Test put_object handles unicode strings correctly."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        data = "test unicode content: 🚀🌟✨"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.put_object(bucket, key, data)

                assert result["status"] == "success"
                # Should encode unicode string to UTF-8 bytes
                expected_bytes = "test unicode content: 🚀🌟✨".encode("utf-8")
                mock_file.write.assert_called_once_with(expected_bytes)

    def test_put_object_basic_functionality(self):
        """Test put_object basic functionality."""
        auth_method = "secret_keys"
        storage_secrets = {"test": "secret"}
        bucket = "test-bucket"
        key = "test/file.txt"
        data = b"test content"

        with patch.object(StorageClientFactory, "create_client") as mock_create:
            mock_provider_client = create_autospec(BaseStorageClient)
            mock_provider_client.build_uri.return_value = (
                "s3://test-bucket/test/file.txt"
            )
            mock_provider_client.get_transport_params.return_value = {
                "param1": "value1"
            }
            mock_create.return_value = mock_provider_client

            with patch(
                "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
            ) as mock_smart_open:
                mock_file = Mock()
                mock_file.__enter__ = Mock(return_value=mock_file)
                mock_file.__exit__ = Mock(return_value=None)
                mock_smart_open.return_value = mock_file

                client = SmartOpenStorageClient("s3", auth_method, storage_secrets)
                result = client.put_object(bucket, key, data)

                assert result["status"] == "success"
                mock_smart_open.assert_called_once_with(
                    "s3://test-bucket/test/file.txt",
                    "wb",
                    transport_params={"param1": "value1"},
                )

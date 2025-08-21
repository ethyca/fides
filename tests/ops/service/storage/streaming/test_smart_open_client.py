"""Tests for the SmartOpenStorageClient."""

from unittest.mock import Mock, patch

import pytest

from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient


class TestSmartOpenStorageClient:
    """Test the SmartOpenStorageClient class."""

    def test_init_creates_provider_client(self):
        """Test that initialization creates the appropriate provider client."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        assert client.storage_type == "s3"
        assert client.storage_secrets == secrets
        assert hasattr(client, "_provider_client")

    def test_init_normalizes_storage_type(self):
        """Test that storage type is normalized during initialization."""
        # Test GCP alias
        secrets = {"service_account_info": {"type": "service_account"}}
        client = SmartOpenStorageClient("gcp", secrets)
        assert client.storage_type == "gcs"

        # Test Google alias
        client = SmartOpenStorageClient("google", secrets)
        assert client.storage_type == "gcs"

    def test_build_uri_delegates_to_provider(self):
        """Test that _build_uri delegates to provider client."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri method
        client._provider_client.build_uri = Mock(return_value="mocked://bucket/key")

        result = client._build_uri("bucket", "key")

        assert result == "mocked://bucket/key"
        client._provider_client.build_uri.assert_called_once_with("bucket", "key")

    def test_get_transport_params_delegates_to_provider(self):
        """Test that _get_transport_params delegates to provider client."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's get_transport_params method
        client._provider_client.get_transport_params = Mock(
            return_value={"mocked": "params"}
        )

        result = client._get_transport_params()

        assert result == {"mocked": "params"}
        client._provider_client.get_transport_params.assert_called_once()

    def test_generate_presigned_url_delegates_to_provider(self):
        """Test that generate_presigned_url delegates to provider client."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's generate_presigned_url method
        client._provider_client.generate_presigned_url = Mock(
            return_value="https://mocked-url.com"
        )

        result = client.generate_presigned_url("bucket", "key", 3600)

        assert result == "https://mocked-url.com"
        client._provider_client.generate_presigned_url.assert_called_once_with(
            "bucket", "key", 3600
        )

    def test_put_object_still_works(self):
        """Test that put_object method still works after refactoring."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value.__enter__.return_value = mock_file

            result = client.put_object("bucket", "key", "test content")

            assert result["status"] == "success"
            assert result["uri"] == "s3://bucket/key"
            mock_file.write.assert_called_once_with(b"test content")

    def test_get_object_still_works(self):
        """Test that get_object method still works after refactoring."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_file.read.return_value = b"test content"
            mock_smart_open.return_value.__enter__.return_value = mock_file

            result = client.get_object("bucket", "key")

            assert result == b"test content"
            mock_file.read.assert_called_once()

    def test_stream_upload_still_works(self):
        """Test that stream_upload method still works after refactoring."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value = mock_file

            result = client.stream_upload("bucket", "key")

            assert result == mock_file
            mock_smart_open.assert_called_once_with(
                "s3://bucket/key", "wb", transport_params={}
            )

    def test_stream_read_still_works(self):
        """Test that stream_read method still works after refactoring."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value = mock_file

            result = client.stream_read("bucket", "key")

            assert result == mock_file
            mock_smart_open.assert_called_once_with(
                "s3://bucket/key", "rb", transport_params={}
            )

    def test_put_object_string_body(self):
        """Test put_object with string body."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value.__enter__.return_value = mock_file

            result = client.put_object("bucket", "key", "test string content")

            assert result["status"] == "success"
            assert result["uri"] == "s3://bucket/key"
            mock_file.write.assert_called_once_with(b"test string content")

    def test_put_object_other_type_body(self):
        """Test put_object with other type body (converted to string)."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value.__enter__.return_value = mock_file

            # Test with a number
            result = client.put_object("bucket", "key", 123)

            assert result["status"] == "success"
            assert result["uri"] == "s3://bucket/key"
            mock_file.write.assert_called_once_with(b"123")

    def test_put_object_with_content_type(self):
        """Test put_object with content type."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value.__enter__.return_value = mock_file

            result = client.put_object(
                "bucket", "key", "test content", content_type="text/plain"
            )

            assert result["status"] == "success"
            assert result["uri"] == "s3://bucket/key"
            mock_file.write.assert_called_once_with(b"test content")

    def test_put_object_with_metadata(self):
        """Test put_object with metadata."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value.__enter__.return_value = mock_file

            metadata = {"key1": "value1", "key2": "value2"}
            result = client.put_object(
                "bucket", "key", "test content", metadata=metadata
            )

            assert result["status"] == "success"
            assert result["uri"] == "s3://bucket/key"
            mock_file.write.assert_called_once_with(b"test content")

    def test_put_object_exception_handling(self):
        """Test put_object exception handling."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open to raise an exception
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_smart_open.side_effect = Exception("Upload failed")

            with pytest.raises(Exception, match="Upload failed"):
                client.put_object("bucket", "key", "test content")

    def test_get_object_exception_handling(self):
        """Test get_object exception handling."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open to raise an exception
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_smart_open.side_effect = Exception("Read failed")

            with pytest.raises(Exception, match="Read failed"):
                client.get_object("bucket", "key")

    def test_multipart_upload_methods(self):
        """Test multipart upload methods."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Test create_multipart_upload
        result = client.create_multipart_upload("bucket", "key", "text/plain")
        assert result.upload_id == "smart_open_streaming"
        assert result.metadata["storage_type"] == "s3"
        assert result.metadata["method"] == "streaming"

        # Mock put_object to prevent real AWS calls
        with patch.object(client, "put_object") as mock_put_object:
            mock_put_object.return_value = {
                "status": "success",
                "uri": "s3://bucket/key.part1",
            }

            # Test upload_part - this should not make real AWS calls
            part_result = client.upload_part(
                "bucket", "key", "upload_id", 1, b"part content"
            )
            assert part_result.part_number == 1
            assert part_result.etag == "smart_open_part_1"
            assert part_result.metadata["storage_type"] == "s3"
            assert part_result.metadata["method"] == "streaming"

        # Test complete_multipart_upload
        client.complete_multipart_upload("bucket", "key", "upload_id", [part_result])

        # Test abort_multipart_upload
        client.abort_multipart_upload("bucket", "key", "upload_id")

    def test_stream_upload_with_content_type(self):
        """Test stream_upload with content type."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value = mock_file

            result = client.stream_upload("bucket", "key")

            assert result == mock_file
            mock_smart_open.assert_called_once_with(
                "s3://bucket/key", "wb", transport_params={}
            )

    def test_stream_read_with_content_type(self):
        """Test stream_read with content type."""
        secrets = {"aws_access_key_id": "test_key"}
        client = SmartOpenStorageClient("s3", secrets)

        # Mock the provider client's build_uri and get_transport_params methods
        client._provider_client.build_uri = Mock(return_value="s3://bucket/key")
        client._provider_client.get_transport_params = Mock(return_value={})

        # Mock smart_open.open
        with patch(
            "fides.api.service.storage.streaming.smart_open_client.smart_open.open"
        ) as mock_smart_open:
            mock_file = Mock()
            mock_smart_open.return_value = mock_file

            result = client.stream_read("bucket", "key")

            assert result == mock_file
            mock_smart_open.assert_called_once_with(
                "s3://bucket/key", "rb", transport_params={}
            )

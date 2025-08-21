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

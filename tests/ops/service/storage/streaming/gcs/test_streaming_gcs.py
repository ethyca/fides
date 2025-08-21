"""Tests for GCS streaming storage functionality."""

from io import BytesIO
from unittest.mock import Mock, create_autospec, patch

import pytest

from fides.api.common_exceptions import StorageUploadError
from fides.api.service.storage.streaming.gcs.streaming_gcs import (
    upload_to_gcs_streaming,
)
from fides.api.service.storage.streaming.schemas import StorageUploadConfig
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient
from fides.api.service.storage.streaming.smart_open_streaming_storage import (
    SmartOpenStreamingStorage,
)


@pytest.fixture
def mock_gcs_secrets():
    """Mock GCS storage secrets."""
    return {
        "service_account_info": {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "test-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
        }
    }


@pytest.fixture
def mock_streaming_storage(mock_smart_open_client):
    """Create a SmartOpenStreamingStorage instance with mocked client."""
    return SmartOpenStreamingStorage(mock_smart_open_client)


@pytest.fixture
def mock_privacy_request():
    """Create a mock privacy request."""
    privacy_request = Mock()
    privacy_request.id = "test_request_123"
    privacy_request.policy = Mock()
    privacy_request.policy.get_action_type.return_value = Mock(value="access")
    privacy_request.get_persisted_identity.return_value = Mock(
        labeled_dict=lambda include_default_labels: {
            "email": {"value": "test@example.com"},
            "phone_number": {"value": "+1234567890"},
        }
    )
    privacy_request.requested_at = Mock(strftime=lambda fmt: "01/01/2024 12:00 UTC")
    return privacy_request


class TestGCSStreamingClient:
    """Test GCS-specific functionality of SmartOpenStorageClient."""

    def test_init_gcs(self, mock_gcs_secrets):
        """Test initialization with GCS storage type."""
        client = SmartOpenStorageClient("gcs", mock_gcs_secrets)
        assert client.storage_type == "gcs"
        assert client.storage_secrets == mock_gcs_secrets

    def test_init_gcp_alias(self, mock_gcs_secrets):
        """Test initialization with GCP alias."""
        client = SmartOpenStorageClient("gcp", mock_gcs_secrets)
        assert client.storage_type == "gcs"

    def test_init_google_alias(self, mock_gcs_secrets):
        """Test initialization with Google alias."""
        client = SmartOpenStorageClient("google", mock_gcs_secrets)
        assert client.storage_type == "gcs"

    def test_build_uri_gcs(self, mock_gcs_secrets):
        """Test GCS URI construction."""
        client = SmartOpenStorageClient("gcs", mock_gcs_secrets)
        uri = client._build_uri("test-bucket", "test-key")
        assert uri == "gs://test-bucket/test-key"

    def test_get_transport_params_gcs(self, mock_gcs_secrets):
        """Test GCS transport parameters."""
        client = SmartOpenStorageClient("gcs", mock_gcs_secrets)
        params = client._get_transport_params()
        assert "credentials" in params
        assert params["credentials"] == mock_gcs_secrets["service_account_info"]

    def test_get_transport_params_gcs_service_account_file(self):
        """Test GCS transport parameters with service account file."""
        secrets = {"service_account_file": "/path/to/service-account.json"}
        client = SmartOpenStorageClient("gcs", secrets)
        params = client._get_transport_params()
        assert "credentials" in params
        assert params["credentials"] == "/path/to/service-account.json"


class TestGCSStreamingStorage:
    """Test GCS streaming storage functionality."""

    def test_upload_to_storage_streaming_json(
        self, mock_streaming_storage, mock_privacy_request
    ):
        """Test JSON upload workflow for GCS."""
        data = {"users": [{"id": 1, "name": "User 1"}]}
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.zip",
            resp_format="json",
            max_workers=5,
        )

        # Mock the presigned URL generation
        mock_streaming_storage.storage_client.generate_presigned_url.return_value = (
            "https://storage.googleapis.com/test-bucket/test.zip"
        )

        result = mock_streaming_storage.upload_to_storage_streaming(
            data, config, mock_privacy_request
        )

        # Verify the streaming method was called
        mock_streaming_storage.storage_client.stream_upload.assert_called_once()
        # Now that we have proper presigned URL generation, expect a proper URL
        assert result.startswith("https://storage.googleapis.com/")
        assert "test-bucket" in result
        assert "test.zip" in result

    def test_upload_to_storage_streaming_csv(
        self, mock_streaming_storage, mock_privacy_request
    ):
        """Test CSV upload workflow for GCS."""
        data = {"users": [{"id": 1, "name": "User 1"}]}
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.zip",
            resp_format="csv",
            max_workers=5,
        )

        # Mock the presigned URL generation
        mock_streaming_storage.storage_client.generate_presigned_url.return_value = (
            "https://storage.googleapis.com/test-bucket/test.zip"
        )

        result = mock_streaming_storage.upload_to_storage_streaming(
            data, config, mock_privacy_request
        )

        # Verify the streaming method was called
        mock_streaming_storage.storage_client.stream_upload.assert_called_once()
        # Now that we have proper presigned URL generation, expect a proper URL
        assert result.startswith("https://storage.googleapis.com/")
        assert "test-bucket" in result
        assert "test.zip" in result

    def test_upload_to_storage_streaming_html(
        self, mock_streaming_storage, mock_privacy_request
    ):
        """Test HTML upload workflow for GCS."""
        data = {"users": [{"id": 1, "name": "User 1"}]}
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.zip",
            resp_format="html",
            max_workers=5,
        )

        # Mock the DSR storage function
        with patch(
            "fides.api.service.storage.streaming.smart_open_streaming_storage.stream_html_dsr_report_to_storage_multipart"
        ) as mock_dsr:
            mock_dsr.return_value = "gs://test-bucket/test.zip"

            # Mock the presigned URL generation
            mock_streaming_storage.storage_client.generate_presigned_url.return_value = (
                "https://storage.googleapis.com/test-bucket/test.zip"
            )

            result = mock_streaming_storage.upload_to_storage_streaming(
                data, config, mock_privacy_request
            )

            # Verify the DSR function was called
            mock_dsr.assert_called_once()
            # Now that we have proper presigned URL generation, expect a proper URL
            assert result.startswith("https://storage.googleapis.com/")
            assert "test-bucket" in result
            assert "test.zip" in result

    def test_upload_to_storage_streaming_no_privacy_request(
        self, mock_streaming_storage
    ):
        """Test that upload fails without privacy request."""
        data = {"users": [{"id": 1, "name": "User 1"}]}
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.zip",
            resp_format="json",
            max_workers=5,
        )

        with pytest.raises(ValueError, match="Privacy request must be provided"):
            mock_streaming_storage.upload_to_storage_streaming(
                data, config, privacy_request=None
            )

    def test_upload_to_storage_streaming_unsupported_format(
        self, mock_streaming_storage, mock_privacy_request
    ):
        """Test that upload fails with unsupported format."""
        data = {"users": [{"id": 1, "name": "User 1"}]}
        config = StorageUploadConfig(
            bucket_name="test-bucket",
            file_key="test.zip",
            resp_format="unsupported",
            max_workers=5,
        )

        with pytest.raises(
            StorageUploadError,
            match="Storage upload failed: Unsupported response format: unsupported",
        ):
            mock_streaming_storage.upload_to_storage_streaming(
                data, config, mock_privacy_request
            )


class TestGCSStreamingIntegration:
    """Test integration of GCS streaming components."""

    @patch(
        "fides.api.service.storage.streaming.gcs.streaming_gcs.SmartOpenStorageClient"
    )
    @patch(
        "fides.api.service.storage.streaming.gcs.streaming_gcs.SmartOpenStreamingStorage"
    )
    def test_upload_to_gcs_streaming_success(
        self, mock_streaming_storage_class, mock_client_class, mock_gcs_secrets
    ):
        """Test successful GCS streaming upload."""
        # Mock the client and streaming storage
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_streaming_storage = Mock()
        mock_streaming_storage.upload_to_storage_streaming.return_value = (
            "https://storage.googleapis.com/test-bucket/test.zip"
        )
        mock_streaming_storage_class.return_value = mock_streaming_storage

        # Test data
        data = {"users": [{"id": 1, "name": "User 1"}]}
        bucket_name = "test-bucket"
        file_key = "test.zip"
        resp_format = "json"
        privacy_request = Mock()
        privacy_request.id = "test-request-123"
        auth_method = "automatic"
        max_workers = 5

        # Call the function
        result = upload_to_gcs_streaming(
            mock_gcs_secrets,
            data,
            bucket_name,
            file_key,
            resp_format,
            privacy_request,
            auth_method,
            max_workers,
        )

        # Verify the result
        assert result == "https://storage.googleapis.com/test-bucket/test.zip"

        # Verify the client was created
        mock_client_class.assert_called_once_with("gcs", mock_gcs_secrets)

        # Verify the streaming storage was created
        mock_streaming_storage_class.assert_called_once_with(mock_client)

        # Verify the upload was called
        mock_streaming_storage.upload_to_storage_streaming.assert_called_once()

    def test_upload_to_gcs_streaming_no_privacy_request(self, mock_gcs_secrets):
        """Test that GCS streaming upload fails without privacy request."""
        data = {"users": [{"id": 1, "name": "User 1"}]}
        bucket_name = "test-bucket"
        file_key = "test.zip"
        resp_format = "json"
        auth_method = "automatic"

        with pytest.raises(ValueError, match="Privacy request must be provided"):
            upload_to_gcs_streaming(
                mock_gcs_secrets,
                data,
                bucket_name,
                file_key,
                resp_format,
                None,  # No privacy request
                auth_method,
            )

    @patch(
        "fides.api.service.storage.streaming.gcs.streaming_gcs.SmartOpenStorageClient"
    )
    def test_upload_to_gcs_streaming_client_creation_error(
        self, mock_client_class, mock_gcs_secrets
    ):
        """Test GCS streaming upload when client creation fails."""
        # Mock client creation to fail
        mock_client_class.side_effect = Exception("Failed to create client")

        data = {"users": [{"id": 1, "name": "User 1"}]}
        bucket_name = "test-bucket"
        file_key = "test.zip"
        resp_format = "json"
        privacy_request = Mock()
        privacy_request.id = "test-request-123"
        auth_method = "automatic"

        with pytest.raises(
            StorageUploadError,
            match="Error creating smart-open GCS client: Failed to create client",
        ):
            upload_to_gcs_streaming(
                mock_gcs_secrets,
                data,
                bucket_name,
                file_key,
                resp_format,
                privacy_request,
                auth_method,
            )

    @patch(
        "fides.api.service.storage.streaming.gcs.streaming_gcs.SmartOpenStorageClient"
    )
    @patch(
        "fides.api.service.storage.streaming.gcs.streaming_gcs.SmartOpenStreamingStorage"
    )
    def test_upload_to_gcs_streaming_upload_error(
        self, mock_streaming_storage_class, mock_client_class, mock_gcs_secrets
    ):
        """Test GCS streaming upload when upload fails."""
        # Mock the client and streaming storage
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_streaming_storage = Mock()
        mock_streaming_storage.upload_to_storage_streaming.side_effect = Exception(
            "Upload failed"
        )
        mock_streaming_storage_class.return_value = mock_streaming_storage

        # Test data
        data = {"users": [{"id": 1, "name": "User 1"}]}
        bucket_name = "test-bucket"
        file_key = "test.zip"
        resp_format = "json"
        privacy_request = Mock()
        privacy_request.id = "test-request-123"
        auth_method = "automatic"

        with pytest.raises(
            StorageUploadError,
            match="Unexpected error during smart-open streaming upload to GCS: Upload failed",
        ):
            upload_to_gcs_streaming(
                mock_gcs_secrets,
                data,
                bucket_name,
                file_key,
                resp_format,
                privacy_request,
                auth_method,
            )


class TestGCSSchemas:
    """Test GCS-specific schema handling."""

    def test_storage_upload_config_gcs(self):
        """Test StorageUploadConfig with GCS-specific values."""
        config = StorageUploadConfig(
            bucket_name="gcs-test-bucket",
            file_key="test-data.zip",
            resp_format="json",
            max_workers=10,
        )

        assert config.bucket_name == "gcs-test-bucket"
        assert config.file_key == "test-data.zip"
        assert config.resp_format == "json"
        assert config.max_workers == 10

    def test_storage_upload_config_validation(self):
        """Test StorageUploadConfig validation."""
        # Test with empty bucket name
        with pytest.raises(
            ValueError, match="Storage identifier cannot be empty or whitespace"
        ):
            StorageUploadConfig(
                bucket_name="",
                file_key="test.zip",
                resp_format="json",
                max_workers=5,
            )

        # Test with empty file key
        with pytest.raises(
            ValueError, match="Storage identifier cannot be empty or whitespace"
        ):
            StorageUploadConfig(
                bucket_name="test-bucket",
                file_key="",
                resp_format="json",
                max_workers=5,
            )

        # Test with invalid max_workers
        with pytest.raises(
            ValueError, match="Input should be greater than or equal to 1"
        ):
            StorageUploadConfig(
                bucket_name="test-bucket",
                file_key="test.zip",
                resp_format="json",
                max_workers=0,
            )

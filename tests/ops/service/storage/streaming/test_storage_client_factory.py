from unittest.mock import Mock, create_autospec, patch

import pytest

from fides.api.service.storage.streaming.s3.s3_storage_client import S3StorageClient
from fides.api.service.storage.streaming.storage_client_factory import (
    CloudStorageClientFactory,
    get_storage_client,
)


class TestCloudStorageClientFactory:
    """Test cases for CloudStorageClientFactory class."""

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_s3_storage_client"
    )
    def test_create_storage_client_s3_success(
        self, mock_create_s3_client, mock_s3_storage_client
    ):
        """Test successful S3 storage client creation."""
        # Arrange
        mock_create_s3_client.return_value = mock_s3_storage_client
        storage_type = "s3"
        auth_method = "automatic"
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
        }

        # Act
        result = CloudStorageClientFactory.create_storage_client(
            storage_type, auth_method, storage_secrets
        )

        # Assert
        assert result == mock_s3_storage_client
        mock_create_s3_client.assert_called_once_with(auth_method, storage_secrets)

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_gcs_storage_client"
    )
    def test_create_storage_client_gcs_success(
        self, mock_create_gcs_client, mock_gcs_storage_client
    ):
        """Test successful GCS storage client creation."""
        # Arrange
        mock_create_gcs_client.return_value = mock_gcs_storage_client
        storage_type = "gcs"
        auth_method = "adc"
        storage_secrets = {"project_id": "test-project"}

        # Act
        result = CloudStorageClientFactory.create_storage_client(
            storage_type, auth_method, storage_secrets
        )

        # Assert
        assert result == mock_gcs_storage_client
        mock_create_gcs_client.assert_called_once_with(auth_method, storage_secrets)

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_gcs_storage_client"
    )
    def test_create_storage_client_gcp_alias_success(
        self, mock_create_gcs_client, mock_gcs_storage_client
    ):
        """Test successful GCS storage client creation using 'gcp' alias."""
        # Arrange
        mock_create_gcs_client.return_value = mock_gcs_storage_client
        storage_type = "gcp"
        auth_method = "service_account"
        storage_secrets = {"project_id": "test-project"}

        # Act
        result = CloudStorageClientFactory.create_storage_client(
            storage_type, auth_method, storage_secrets
        )

        # Assert
        assert result == mock_gcs_storage_client
        mock_create_gcs_client.assert_called_once_with(auth_method, storage_secrets)

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_gcs_storage_client"
    )
    def test_create_storage_client_google_alias_success(
        self, mock_create_gcs_client, mock_gcs_storage_client
    ):
        """Test successful GCS storage client creation using 'google' alias."""
        # Arrange
        mock_create_gcs_client.return_value = mock_gcs_storage_client
        storage_type = "google"
        auth_method = "adc"
        storage_secrets = None

        # Act
        result = CloudStorageClientFactory.create_storage_client(
            storage_type, auth_method, storage_secrets
        )

        # Assert
        assert result == mock_gcs_storage_client
        mock_create_gcs_client.assert_called_once_with(auth_method, storage_secrets)

    def test_create_storage_client_s3_missing_secrets(self):
        """Test S3 storage client creation fails when secrets are missing."""
        # Arrange
        storage_type = "s3"
        auth_method = "automatic"
        storage_secrets = None

        # Act & Assert
        with pytest.raises(ValueError, match="Storage secrets are required for S3"):
            CloudStorageClientFactory.create_storage_client(
                storage_type, auth_method, storage_secrets
            )

    def test_create_storage_client_s3_empty_secrets(self):
        """Test S3 storage client creation succeeds with empty secrets dict (not None)."""
        # Arrange
        storage_type = "s3"
        auth_method = "automatic"
        storage_secrets = {}

        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.create_s3_storage_client"
        ) as mock_create_s3:
            mock_s3_client = create_autospec(S3StorageClient)
            mock_create_s3.return_value = mock_s3_client

            # Act
            result = CloudStorageClientFactory.create_storage_client(
                storage_type, auth_method, storage_secrets
            )

            # Assert
            assert result == mock_s3_client
            mock_create_s3.assert_called_once_with(auth_method, storage_secrets)

    def test_create_storage_client_unsupported_type(self):
        """Test storage client creation fails for unsupported storage type."""
        # Arrange
        storage_type = "unsupported"
        auth_method = "automatic"
        storage_secrets = {"key": "value"}

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported storage type: unsupported"):
            CloudStorageClientFactory.create_storage_client(
                storage_type, auth_method, storage_secrets
            )

    def test_create_storage_client_case_insensitive_s3(self, mock_s3_storage_client):
        """Test storage client creation is case insensitive for S3."""
        # Arrange
        storage_type = "S3"
        auth_method = "automatic"
        storage_secrets = {"aws_access_key_id": "test_key"}

        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.create_s3_storage_client"
        ) as mock_create_s3:
            mock_create_s3.return_value = mock_s3_storage_client

            # Act
            result = CloudStorageClientFactory.create_storage_client(
                storage_type, auth_method, storage_secrets
            )

            # Assert
            assert result == mock_s3_storage_client
            mock_create_s3.assert_called_once_with(auth_method, storage_secrets)

    def test_create_storage_client_case_insensitive_gcs(self, mock_gcs_storage_client):
        """Test storage client creation is case insensitive for GCS."""
        # Arrange
        storage_type = "GCS"
        auth_method = "adc"
        storage_secrets = {"project_id": "test-project"}

        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.create_gcs_storage_client"
        ) as mock_create_gcs:
            mock_create_gcs.return_value = mock_gcs_storage_client

            # Act
            result = CloudStorageClientFactory.create_storage_client(
                storage_type, auth_method, storage_secrets
            )

            # Assert
            assert result == mock_gcs_storage_client
            mock_create_gcs.assert_called_once_with(auth_method, storage_secrets)

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_s3_storage_client"
    )
    def test_create_storage_client_from_config_s3(
        self, mock_create_s3_client, mock_s3_storage_client
    ):
        """Test creating S3 storage client from configuration dictionary."""
        # Arrange
        mock_create_s3_client.return_value = mock_s3_storage_client
        storage_config = {
            "type": "s3",
            "auth_method": "automatic",
            "secrets": {
                "aws_access_key_id": "test_key",
                "aws_secret_access_key": "test_secret",
            },
        }

        # Act
        result = CloudStorageClientFactory.create_storage_client_from_config(
            storage_config
        )

        # Assert
        assert result == mock_s3_storage_client
        mock_create_s3_client.assert_called_once_with(
            "automatic", storage_config["secrets"]
        )

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_gcs_storage_client"
    )
    def test_create_storage_client_from_config_gcs(
        self, mock_create_gcs_client, mock_gcs_storage_client
    ):
        """Test creating GCS storage client from configuration dictionary."""
        # Arrange
        mock_create_gcs_client.return_value = mock_gcs_storage_client
        storage_config = {
            "type": "gcs",
            "auth_method": "adc",
            "secrets": {"project_id": "test-project"},
        }

        # Act
        result = CloudStorageClientFactory.create_storage_client_from_config(
            storage_config
        )

        # Assert
        assert result == mock_gcs_storage_client
        mock_create_gcs_client.assert_called_once_with("adc", storage_config["secrets"])

    def test_create_storage_client_from_config_defaults(self, mock_s3_storage_client):
        """Test creating storage client from config with default values."""
        # Arrange
        storage_config = {
            "secrets": {
                "aws_access_key_id": "test_key",
                "aws_secret_access_key": "test_secret",
            }
        }

        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.create_s3_storage_client"
        ) as mock_create_s3:
            mock_create_s3.return_value = mock_s3_storage_client

            # Act
            result = CloudStorageClientFactory.create_storage_client_from_config(
                storage_config
            )

            # Assert
            assert result == mock_s3_storage_client
            # Should default to "s3" type and "automatic" auth_method
            mock_create_s3.assert_called_once_with(
                "automatic", storage_config["secrets"]
            )

    def test_create_storage_client_from_config_no_secrets(
        self, mock_gcs_storage_client
    ):
        """Test creating storage client from config with no secrets."""
        # Arrange
        storage_config = {"type": "gcs", "auth_method": "adc"}

        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.create_gcs_storage_client"
        ) as mock_create_gcs:
            mock_create_gcs.return_value = mock_gcs_storage_client

            # Act
            result = CloudStorageClientFactory.create_storage_client_from_config(
                storage_config
            )

            # Assert
            assert result == mock_gcs_storage_client
            mock_create_gcs.assert_called_once_with("adc", None)

    def test_create_storage_client_from_config_empty_dict(self):
        """Test creating storage client from empty config dictionary raises error for S3."""
        # Arrange
        storage_config = {}

        # Act & Assert
        # Empty config defaults to "s3" type, but S3 requires secrets
        with pytest.raises(ValueError, match="Storage secrets are required for S3"):
            CloudStorageClientFactory.create_storage_client_from_config(storage_config)

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_s3_storage_client"
    )
    def test_create_storage_client_from_config_logs_storage_type(
        self, mock_create_s3_client, mock_s3_storage_client
    ):
        """Test that creating storage client from config logs the storage type."""
        # Arrange
        mock_create_s3_client.return_value = mock_s3_storage_client
        storage_config = {
            "type": "s3",
            "auth_method": "automatic",
            "secrets": {"aws_access_key_id": "test_key"},
        }

        # Act
        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.logger"
        ) as mock_logger:
            CloudStorageClientFactory.create_storage_client_from_config(storage_config)

            # Assert
            mock_logger.info.assert_called_once_with(
                "Creating storage client for type: {}", "s3"
            )


class TestGetStorageClient:
    """Test cases for the get_storage_client convenience function."""

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_s3_storage_client"
    )
    def test_get_storage_client_s3_success(
        self, mock_create_s3_client, mock_s3_storage_client
    ):
        """Test successful S3 storage client creation via convenience function."""
        # Arrange
        mock_create_s3_client.return_value = mock_s3_storage_client
        storage_type = "s3"
        auth_method = "automatic"
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
        }

        # Act
        result = get_storage_client(storage_type, auth_method, storage_secrets)

        # Assert
        assert result == mock_s3_storage_client
        mock_create_s3_client.assert_called_once_with(auth_method, storage_secrets)

    @patch(
        "fides.api.service.storage.streaming.storage_client_factory.create_gcs_storage_client"
    )
    def test_get_storage_client_gcs_success(
        self, mock_create_gcs_client, mock_gcs_storage_client
    ):
        """Test successful GCS storage client creation via convenience function."""
        # Arrange
        mock_create_gcs_client.return_value = mock_gcs_storage_client
        storage_type = "gcs"
        auth_method = "adc"
        storage_secrets = {"project_id": "test-project"}

        # Act
        result = get_storage_client(storage_type, auth_method, storage_secrets)

        # Assert
        assert result == mock_gcs_storage_client
        mock_create_gcs_client.assert_called_once_with(auth_method, storage_secrets)

    def test_get_storage_client_s3_missing_secrets(self):
        """Test convenience function fails when S3 secrets are missing."""
        # Arrange
        storage_type = "s3"
        auth_method = "automatic"
        storage_secrets = None

        # Act & Assert
        with pytest.raises(ValueError, match="Storage secrets are required for S3"):
            get_storage_client(storage_type, auth_method, storage_secrets)

    def test_get_storage_client_unsupported_type(self):
        """Test convenience function fails for unsupported storage type."""
        # Arrange
        storage_type = "unsupported"
        auth_method = "automatic"
        storage_secrets = {"key": "value"}

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported storage type: unsupported"):
            get_storage_client(storage_type, auth_method, storage_secrets)

    def test_get_storage_client_delegates_to_factory(self, mock_s3_storage_client):
        """Test that convenience function properly delegates to factory method."""
        # Arrange
        storage_type = "s3"
        auth_method = "automatic"
        storage_secrets = {"aws_access_key_id": "test_key"}

        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.CloudStorageClientFactory.create_storage_client"
        ) as mock_factory_method:
            mock_factory_method.return_value = mock_s3_storage_client

            # Act
            result = get_storage_client(storage_type, auth_method, storage_secrets)

            # Assert
            assert result == mock_s3_storage_client
            mock_factory_method.assert_called_once_with(
                storage_type, auth_method, storage_secrets
            )


class TestStorageClientFactoryIntegration:
    """Integration tests for storage client factory with existing mock fixtures."""

    def test_s3_client_creation_integration(self, mock_s3_storage_client):
        """Test integration of S3 client creation through the factory using mock fixture."""
        # Arrange
        storage_type = "s3"
        auth_method = "automatic"
        storage_secrets = {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
        }

        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.create_s3_storage_client"
        ) as mock_create_s3:
            mock_create_s3.return_value = mock_s3_storage_client

            # Act
            result = CloudStorageClientFactory.create_storage_client(
                storage_type, auth_method, storage_secrets
            )

            # Assert
            assert result == mock_s3_storage_client
            mock_create_s3.assert_called_once_with(auth_method, storage_secrets)

    def test_gcs_client_creation_integration(self, mock_gcs_storage_client):
        """Test integration of GCS client creation through the factory using mock fixture."""
        # Arrange
        storage_type = "gcs"
        auth_method = "adc"
        storage_secrets = {"project_id": "test-project"}

        with patch(
            "fides.api.service.storage.streaming.storage_client_factory.create_gcs_storage_client"
        ) as mock_create_gcs:
            mock_create_gcs.return_value = mock_gcs_storage_client

            # Act
            result = CloudStorageClientFactory.create_storage_client(
                storage_type, auth_method, storage_secrets
            )

            # Assert
            assert result == mock_gcs_storage_client
            mock_create_gcs.assert_called_once_with(auth_method, storage_secrets)

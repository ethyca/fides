from unittest.mock import MagicMock, create_autospec, patch

import pytest
from google.cloud import storage
from google.oauth2.service_account import Credentials

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import GCSAuthMethod
from fides.api.service.storage.gcs import get_gcs_client


class TestGetGCSClient:
    def test_get_gcs_client_adc(self):
        """Test getting GCS client using ADC authentication."""
        with patch(
            "fides.api.service.storage.gcs.Client", autospec=True
        ) as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            client = get_gcs_client(GCSAuthMethod.ADC.value, None)
            assert isinstance(client, MagicMock)
            mock_client_cls.assert_called_once()

    def test_get_gcs_client_service_account(self):
        """Test getting GCS client using service account authentication."""
        test_secrets = {
            "type": "service_account",
            "project_id": "test-project-123",
            "private_key_id": "test-key-id-456",
            "private_key": (
                "-----BEGIN PRIVATE KEY-----\n"
                "MIItest\n"
                "-----END PRIVATE KEY-----\n"
            ),
            "client_email": "test-service@test-project-123.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": (
                "https://www.googleapis.com/oauth2/v1/certs"
            ),
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-service%40test-project-123.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com",
        }

        mock_credentials = create_autospec(Credentials)
        with patch(
            "fides.api.service.storage.gcs.service_account.Credentials", autospec=True
        ) as mock_creds_cls:
            with patch(
                "fides.api.service.storage.gcs.Client", autospec=True
            ) as mock_client_cls:
                mock_creds_cls.from_service_account_info.return_value = mock_credentials
                mock_client_cls.return_value = MagicMock()

                client = get_gcs_client(
                    GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value, test_secrets
                )

                mock_creds_cls.from_service_account_info.assert_called_once_with(
                    test_secrets
                )
                mock_client_cls.assert_called_once_with(credentials=mock_credentials)
                assert isinstance(client, MagicMock)

    def test_get_gcs_client_service_account_no_secrets(self):
        """Test GCS client with service account auth and missing secrets."""
        with pytest.raises(StorageUploadError) as exc_info:
            get_gcs_client(GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value, None)
        assert "Storage secrets not found for Google Cloud Storage" in str(
            exc_info.value
        )

    def test_get_gcs_client_invalid_auth_method(self):
        """Test getting GCS client with invalid authentication method."""
        invalid_auth = "invalid_auth"
        with pytest.raises(ValueError) as exc_info:
            get_gcs_client(invalid_auth, None)
        expected_msg = "Google Cloud Storage auth method not supported: invalid_auth"
        assert expected_msg in str(exc_info.value)


class TestGetGCSBlob:
    def test_get_gcs_blob_success(self, base_gcs_client_mock):
        """Test successfully getting a GCS blob."""
        # Create a properly specced mock bucket and blob
        mock_bucket = create_autospec(storage.Bucket)
        mock_blob = create_autospec(storage.Blob)
        mock_bucket.blob.return_value = mock_blob

        # Configure the base_gcs_client_mock to return our mock bucket
        base_gcs_client_mock.bucket = MagicMock(return_value=mock_bucket)

        with patch(
            "fides.api.service.storage.gcs.get_gcs_client",
            return_value=base_gcs_client_mock,
        ):
            from fides.api.service.storage.gcs import get_gcs_blob

            result = get_gcs_blob(
                GCSAuthMethod.ADC.value, None, "test-bucket", "test-file.txt"
            )

            # Verify the result is a Blob instance
            assert isinstance(result, storage.Blob)
            # Verify the correct methods were called
            base_gcs_client_mock.bucket.assert_called_once_with("test-bucket")
            mock_bucket.blob.assert_called_once_with("test-file.txt")

    def test_get_gcs_blob_error(self, base_gcs_client_mock):
        """Test error handling when getting a GCS blob."""
        # Configure the mock to raise an exception
        base_gcs_client_mock.bucket = MagicMock(side_effect=Exception("Test error"))

        with patch(
            "fides.api.service.storage.gcs.get_gcs_client",
            return_value=base_gcs_client_mock,
        ):
            from fides.api.service.storage.gcs import get_gcs_blob

            with pytest.raises(Exception) as exc_info:
                get_gcs_blob(
                    GCSAuthMethod.ADC.value, None, "test-bucket", "test-file.txt"
                )
            assert "Test error" in str(exc_info.value)

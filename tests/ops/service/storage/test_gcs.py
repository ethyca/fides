from unittest.mock import MagicMock, patch

import pytest

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import GCSAuthMethod
from fides.api.service.storage.gcs import get_gcs_client


class TestGetGCSClient:
    def test_get_gcs_client_adc(self):
        """Test getting GCS client using ADC authentication."""
        with patch("fides.api.service.storage.gcs.Client") as mock_client:
            mock_client.return_value = MagicMock()
            client = get_gcs_client(GCSAuthMethod.ADC.value, None)
            assert isinstance(client, MagicMock)
            mock_client.assert_called_once()

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
        }

        with patch(
            "fides.api.service.storage.gcs.service_account.Credentials"
        ) as mock_creds:
            with patch("fides.api.service.storage.gcs.Client") as mock_client:
                mock_credentials = MagicMock()
                mock_creds.from_service_account_info.return_value = mock_credentials
                mock_client.return_value = MagicMock()

                client = get_gcs_client(
                    GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value, test_secrets
                )

                mock_creds.from_service_account_info.assert_called_once_with(
                    test_secrets
                )
                mock_client.assert_called_once_with(credentials=mock_credentials)
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

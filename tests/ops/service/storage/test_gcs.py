from io import BytesIO
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from google.cloud import storage
from google.oauth2.service_account import Credentials

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import GCSAuthMethod
from fides.api.service.storage.gcs import generic_upload_to_gcs, get_gcs_client


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


class TestGenericUploadToGCS:
    """Test cases for generic_upload_to_gcs function."""

    @pytest.fixture
    def mock_blob(self):
        """Create a mock GCS blob."""
        blob = create_autospec(storage.Blob)
        blob.size = 1024
        blob.generate_signed_url.return_value = (
            "https://storage.googleapis.com/test-bucket/test-file.txt"
        )
        return blob

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return BytesIO(b"test file content")

    @pytest.fixture
    def storage_secrets(self):
        """Create sample storage secrets."""
        return {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
        }

    def test_generic_upload_to_gcs_success(
        self, mock_blob, sample_document, storage_secrets
    ):
        """Test successful generic upload to GCS."""
        with patch(
            "fides.api.service.storage.gcs.get_gcs_blob",
            return_value=mock_blob,
        ):
            file_size, signed_url = generic_upload_to_gcs(
                storage_secrets=storage_secrets,
                bucket_name="test-bucket",
                file_key="test-file.txt",
                auth_method=GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
                document=sample_document,
            )

            assert file_size == 1024
            assert (
                signed_url == "https://storage.googleapis.com/test-bucket/test-file.txt"
            )

            # Verify the blob methods were called correctly
            mock_blob.upload_from_file.assert_called_once_with(sample_document)
            mock_blob.reload.assert_called_once()
            mock_blob.generate_signed_url.assert_called_once_with(
                version="v4", expiration=3600, method="GET"
            )

    def test_generic_upload_to_gcs_invalid_document_type(self, storage_secrets):
        """Test generic upload with invalid document type."""
        invalid_document = "not a file-like object"

        with pytest.raises(TypeError, match="must be a file-like object"):
            generic_upload_to_gcs(
                storage_secrets=storage_secrets,
                bucket_name="test-bucket",
                file_key="test-file.txt",
                auth_method=GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
                document=invalid_document,
            )

    def test_generic_upload_to_gcs_document_seek_error(self, storage_secrets):
        """Test generic upload with document seek error."""
        mock_document = MagicMock()
        mock_document.seek.side_effect = Exception("Seek failed")

        with pytest.raises(ValueError, match="Failed to reset file pointer"):
            generic_upload_to_gcs(
                storage_secrets=storage_secrets,
                bucket_name="test-bucket",
                file_key="test-file.txt",
                auth_method=GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
                document=mock_document,
            )

    def test_generic_upload_to_gcs_upload_error(
        self, mock_blob, sample_document, storage_secrets
    ):
        """Test generic upload with upload error."""
        mock_blob.upload_from_file.side_effect = Exception("Upload failed")

        with patch(
            "fides.api.service.storage.gcs.get_gcs_blob",
            return_value=mock_blob,
        ):
            with pytest.raises(StorageUploadError, match="Failed to upload file"):
                generic_upload_to_gcs(
                    storage_secrets=storage_secrets,
                    bucket_name="test-bucket",
                    file_key="test-file.txt",
                    auth_method=GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
                    document=sample_document,
                )

    def test_generic_upload_to_gcs_document_reset_position(
        self, mock_blob, storage_secrets
    ):
        """Test that document position is reset before upload."""
        # Create a document that's not at the beginning
        document = BytesIO(b"test content")
        document.seek(5)  # Move to middle of content

        with patch(
            "fides.api.service.storage.gcs.get_gcs_blob",
            return_value=mock_blob,
        ):
            generic_upload_to_gcs(
                storage_secrets=storage_secrets,
                bucket_name="test-bucket",
                file_key="test-file.txt",
                auth_method=GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
                document=document,
            )

            # Verify the document was reset to position 0
            assert document.tell() == 0

    def test_generic_upload_to_gcs_with_empty_document(
        self, mock_blob, storage_secrets
    ):
        """Test generic upload with empty document."""
        empty_document = BytesIO(b"")

        with patch(
            "fides.api.service.storage.gcs.get_gcs_blob",
            return_value=mock_blob,
        ):
            file_size, signed_url = generic_upload_to_gcs(
                storage_secrets=storage_secrets,
                bucket_name="test-bucket",
                file_key="test-file.txt",
                auth_method=GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
                document=empty_document,
            )

            assert file_size == 1024  # Mock returns 1024
            assert (
                signed_url == "https://storage.googleapis.com/test-bucket/test-file.txt"
            )

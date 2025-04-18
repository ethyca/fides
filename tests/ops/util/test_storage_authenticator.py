from unittest import mock
from unittest.mock import create_autospec

import boto3
import pytest
from botocore.exceptions import NoCredentialsError
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
from moto import mock_aws
from sqlalchemy.ext.mutable import MutableDict

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    StorageDetails,
    StorageSecrets,
)
from fides.api.util.aws_util import get_aws_session, get_s3_client


@pytest.fixture
def storage_secrets(storage_config):
    with mock_aws():
        session = boto3.Session(
            aws_access_key_id=storage_config.secrets[
                StorageSecrets.AWS_ACCESS_KEY_ID.value
            ],
            aws_secret_access_key=storage_config.secrets[
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value
            ],
            region_name="us-east-1",
        )
        s3 = session.client("s3")
        s3.create_bucket(Bucket=storage_config.details[StorageDetails.BUCKET.value])
        yield storage_config.secrets


class TestGetS3Session:
    def test_storage_secret_none_raises_error(self):
        with pytest.raises(StorageUploadError):
            get_aws_session(AWSAuthMethod.SECRET_KEYS.value, None)  # type: ignore

    def tests_unsupported_storage_secret_type_error(self):
        with pytest.raises(ValueError):
            get_aws_session(
                "bad", {StorageSecrets.AWS_ACCESS_KEY_ID: "aws_access_key_id"}  # type: ignore
            )

    def tests_automatic_auth_method(self, loguru_caplog):
        # credentials error raised by AWS since runtime doesn't have env credentials set up -
        # but ensure we don't raise an exception from our own code in parsing.
        with pytest.raises(NoCredentialsError):
            get_aws_session(
                AWSAuthMethod.AUTOMATIC.value,  # type: ignore
                None,
            )


@mock_aws
def test_get_s3_client(storage_secrets):
    s3_client = get_s3_client(AWSAuthMethod.SECRET_KEYS.value, storage_secrets)
    assert s3_client is not None
    assert s3_client.list_buckets() is not None


@mock_aws
def test_get_s3_client_with_assume_role(storage_secrets):
    assume_role_arn = "arn:aws:iam::123456789012:role/test-role"
    s3_client = get_s3_client(
        AWSAuthMethod.SECRET_KEYS.value, storage_secrets, assume_role_arn
    )
    assert s3_client is not None
    assert s3_client.list_buckets() is not None


@mock.patch(
    "fides.api.service.storage.storage_authenticator_service.Request", autospec=True
)
@mock.patch(
    "fides.api.service.storage.storage_authenticator_service.service_account.Credentials",
    autospec=True,
)
class TestGCSAuthenticator:
    """Tests for GCS storage authenticator"""

    @pytest.fixture
    def mock_creds_instance(self):
        """Create a mock credentials instance"""
        mock_instance = create_autospec(Credentials)
        return mock_instance

    def test_secrets_are_valid_for_gcs(
        self, mock_credentials, mock_request, mock_creds_instance
    ):
        """Test GCS credentials validation with valid credentials"""
        mock_credentials.from_service_account_info.return_value = mock_creds_instance

        test_secrets = {
            "type": "service_account",
            "project_id": "test-project-123",
            "private_key_id": "test-key-id-456",
            "private_key": (
                "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n"
            ),
            "client_email": "test-service@test-project-123.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": (
                "https://www.googleapis.com/oauth2/v1/certs"
            ),
            "client_x509_cert_url": (
                "https://www.googleapis.com/robot/v1/metadata/x509/"
                "test-service%40test-project-123.iam.gserviceaccount.com"
            ),
            "universe_domain": "googleapis.com",
        }

        assert secrets_are_valid(test_secrets, StorageType.gcs)
        mock_credentials.from_service_account_info.assert_called_once_with(
            test_secrets,
            scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
        )
        mock_creds_instance.refresh.assert_called_once_with(mock_request())

    @mock.patch(
        "fides.api.service.storage.storage_authenticator_service.logger",
        autospec=True,
    )
    def test_secrets_are_invalid_for_gcs(
        self, mock_logger, mock_credentials, mock_request, mock_creds_instance
    ):
        """Test GCS credentials validation with invalid credentials"""
        mock_credentials.from_service_account_info.return_value = mock_creds_instance
        error = GoogleAuthError("Invalid credentials")
        mock_creds_instance.refresh.side_effect = error

        test_secrets = {
            "type": "service_account",
            "project_id": "test-project-123",
            "private_key_id": "invalid-key",
            "private_key": "invalid-key-data",
            "client_email": "test@test.com",
        }

        assert not secrets_are_valid(test_secrets, StorageType.gcs)
        mock_credentials.from_service_account_info.assert_called_once_with(
            test_secrets,
            scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
        )
        mock_creds_instance.refresh.assert_called_once_with(mock_request())
        mock_logger.warning.assert_called_once_with(
            "Google authentication error trying to authenticate GCS secrets: {}",
            error,
        )

    @mock.patch(
        "fides.api.service.storage.storage_authenticator_service.logger",
        autospec=True,
    )
    def test_secrets_validation_unexpected_error(
        self, mock_logger, mock_credentials, mock_request, mock_creds_instance
    ):
        """Test GCS credentials validation with unexpected error"""
        mock_credentials.from_service_account_info.return_value = mock_creds_instance
        error = Exception("Unexpected error")
        mock_creds_instance.refresh.side_effect = error

        test_secrets = {
            "type": "service_account",
            "project_id": "test-project-123",
            "private_key_id": "test-key",
            "private_key": "test-key-data",
            "client_email": "test@test.com",
        }

        assert not secrets_are_valid(test_secrets, StorageType.gcs)
        mock_credentials.from_service_account_info.assert_called_once_with(
            test_secrets,
            scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
        )
        mock_creds_instance.refresh.assert_called_once_with(mock_request())
        mock_logger.warning.assert_called_once_with(
            "Unexpected error authenticating GCS secrets: {}", error
        )

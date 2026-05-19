import json
from typing import Dict, Generator
from unittest import mock
from unittest.mock import MagicMock, create_autospec, patch

import boto3
import pytest
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
from moto import mock_aws
from sqlalchemy.orm import Session

from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    GCSAuthMethod,
    StorageDetails,
    StorageSecrets,
    StorageSecretsS3,
    StorageType,
)
from fides.api.service.storage.storage_authenticator_service import (
    _s3_authenticator,
    secrets_are_valid,
)


@pytest.fixture
def mock_aws_account_id() -> Generator[str, None, None]:
    """Fixture that returns a mock AWS account ID."""
    with mock_aws():
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        yield identity["Account"]


@pytest.fixture
def mock_iam_role(mock_aws_account_id: str) -> Generator[str, None, None]:
    """Fixture that creates a mock IAM role and returns its ARN."""
    with mock_aws():
        iam = boto3.client("iam")
        role_name = "S3FullAccessRole"

        # Create the role that will be assumed
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{mock_aws_account_id}:root"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        # Create the role
        iam.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )

        # Create and attach a policy that allows assuming this role
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Resource": f"arn:aws:iam::{mock_aws_account_id}:role/{role_name}",
                }
            ],
        }

        policy = iam.create_policy(
            PolicyName="AssumeRolePolicy", PolicyDocument=json.dumps(policy_document)
        )

        # Attach the policy to the role
        iam.attach_role_policy(RoleName=role_name, PolicyArn=policy["Policy"]["Arn"])

        role_arn = f"arn:aws:iam::{mock_aws_account_id}:role/{role_name}"
        yield role_arn


@pytest.fixture
def mock_role_credentials(mock_iam_role: str) -> Generator[Dict[str, str], None, None]:
    """Fixture that assumes a role and returns the temporary credentials."""
    with mock_aws():
        sts = boto3.client("sts")
        creds = sts.assume_role(RoleArn=mock_iam_role, RoleSessionName="test-session")[
            "Credentials"
        ]

        yield {
            "access_key_id": creds["AccessKeyId"],
            "secret_access_key": creds["SecretAccessKey"],
        }


@pytest.fixture
def mock_aws_role(
    mock_iam_role: str, mock_role_credentials: Dict[str, str]
) -> Generator[Dict[str, str], None, None]:
    """Combined fixture that provides all role-related information."""
    yield {
        "role_arn": mock_iam_role,
        "access_key_id": mock_role_credentials["access_key_id"],
        "secret_access_key": mock_role_credentials["secret_access_key"],
    }


@pytest.fixture
def s3_storage_config(db: Session) -> Generator[StorageConfig, None, None]:
    """Fixture that creates and yields an S3 storage config."""
    storage_config = StorageConfig.create(
        db=db,
        data={
            "name": "Test S3 Storage",
            "type": StorageType.s3,
            "details": {
                StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
                StorageDetails.NAMING.value: "request_id",
                StorageDetails.BUCKET.value: "test_bucket",
            },
            "key": "test_s3_storage",
            "format": "json",
        },
    )
    yield storage_config
    storage_config.delete(db)


@mock.patch(
    "fides.api.service.storage.storage_authenticator_service.get_aws_session",
    autospec=True,
)
class TestS3Authenticator:
    """Tests for S3 storage authenticator"""

    @pytest.mark.parametrize(
        "has_role",
        [True, False],
    )
    def test_storage_config_can_assume_role(
        self,
        mock_get_aws_session: MagicMock,
        db: Session,
        mock_aws_role: Dict[str, str],
        s3_storage_config: StorageConfig,
        has_role: bool,
    ) -> None:
        """
        Test that a storage config can handle both cases:
        1. With assume_role_arn - verifies role assumption occurs
        2. Without assume_role_arn - verifies direct access works
        """
        # Set the secrets with the role ARN and credentials
        secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: mock_aws_role["access_key_id"],
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: mock_aws_role[
                "secret_access_key"
            ],
        }
        if has_role:
            secrets["assume_role_arn"] = mock_aws_role["role_arn"]
            s3_storage_config.details[StorageDetails.AUTH_METHOD.value] = (
                AWSAuthMethod.AUTOMATIC.value
            )

        s3_storage_config.set_secrets(
            db=db,
            storage_secrets=secrets,
        )

        # Verify that the secrets are valid
        assert secrets_are_valid(
            secrets=StorageSecretsS3(
                aws_access_key_id=mock_aws_role["access_key_id"],
                aws_secret_access_key=mock_aws_role["secret_access_key"],
                assume_role_arn=mock_aws_role["role_arn"] if has_role else None,
            ),
            storage_config=s3_storage_config,
        )

        # Verify the AWS session was created with the correct parameters
        if has_role:
            # When role assumption is enabled, verify the session was created with the role ARN
            mock_get_aws_session.assert_called_once_with(
                AWSAuthMethod.AUTOMATIC.value,
                {
                    "aws_access_key_id": mock_aws_role["access_key_id"],
                    "aws_secret_access_key": mock_aws_role["secret_access_key"],
                    "assume_role_arn": mock_aws_role["role_arn"],
                    "region_name": None,
                },
            )
        else:
            # When role assumption is disabled, verify direct access with secret keys
            mock_get_aws_session.assert_called_once_with(
                AWSAuthMethod.SECRET_KEYS.value,
                {
                    "aws_access_key_id": mock_aws_role["access_key_id"],
                    "aws_secret_access_key": mock_aws_role["secret_access_key"],
                    "assume_role_arn": None,
                    "region_name": None,
                },
            )

    @pytest.mark.parametrize(
        "has_role",
        [True, False],
    )
    def test_s3_authenticator_calls(
        self,
        mock_get_aws_session: MagicMock,
        mock_aws_role: Dict[str, str],
        s3_storage_config: StorageConfig,
        has_role: bool,
    ) -> None:
        """
        Test that _s3_authenticator is called with the correct parameters for both cases:
        1. With assume_role_arn
        2. Without assume_role_arn
        """
        # Create secrets object
        secrets = StorageSecretsS3(
            aws_access_key_id=mock_aws_role["access_key_id"],
            aws_secret_access_key=mock_aws_role["secret_access_key"],
            assume_role_arn=mock_aws_role["role_arn"] if has_role else None,
        )

        # Call _s3_authenticator directly
        _s3_authenticator(s3_storage_config, secrets)

        # Verify get_aws_session was called with correct parameters
        expected_secrets = {
            "aws_access_key_id": mock_aws_role["access_key_id"],
            "aws_secret_access_key": mock_aws_role["secret_access_key"],
            "region_name": None,
        }
        if has_role:
            expected_secrets["assume_role_arn"] = mock_aws_role["role_arn"]
            s3_storage_config.details[StorageDetails.AUTH_METHOD.value] = (
                AWSAuthMethod.AUTOMATIC.value
            )
        else:
            expected_secrets["assume_role_arn"] = None

        mock_get_aws_session.assert_called_once_with(
            AWSAuthMethod.SECRET_KEYS.value,
            expected_secrets,
        )


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
    def gcs_storage_config(self, db: Session) -> Generator[StorageConfig, None, None]:
        """Fixture that creates and yields a GCS storage config."""
        storage_config = StorageConfig.create(
            db=db,
            data={
                "name": "Test GCS Storage",
                "type": StorageType.gcs,
                "details": {
                    StorageDetails.NAMING.value: "request_id",
                    StorageDetails.AUTH_METHOD.value: GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value,
                    StorageDetails.BUCKET.value: "prj-sandbox-55855-test-bucket",
                    StorageDetails.MAX_RETRIES.value: 0,
                },
                "format": "json",
            },
        )
        yield storage_config
        storage_config.delete(db)

    @pytest.fixture
    def mock_creds_instance(self):
        """Create a mock credentials instance"""
        mock_instance = create_autospec(Credentials)
        return mock_instance

    def test_secrets_are_valid_for_gcs(
        self, mock_credentials, mock_request, mock_creds_instance, gcs_storage_config
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

        assert secrets_are_valid(test_secrets, gcs_storage_config)
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
        self,
        mock_logger,
        mock_credentials,
        mock_request,
        mock_creds_instance,
        gcs_storage_config,
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

        assert not secrets_are_valid(test_secrets, gcs_storage_config)
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
        self,
        mock_logger,
        mock_credentials,
        mock_request,
        mock_creds_instance,
        gcs_storage_config,
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

        assert not secrets_are_valid(test_secrets, gcs_storage_config)
        mock_credentials.from_service_account_info.assert_called_once_with(
            test_secrets,
            scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
        )
        mock_creds_instance.refresh.assert_called_once_with(mock_request())
        mock_logger.warning.assert_called_once_with(
            "Unexpected error authenticating GCS secrets: {}", error
        )

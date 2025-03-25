import boto3
import pytest
from botocore.exceptions import NoCredentialsError
from moto import mock_aws

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    StorageDetails,
    StorageSecrets,
    StorageSecretsS3,
    StorageType,
)
from fides.api.service.storage.storage_authenticator_service import secrets_are_valid
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

    def test_secrets_are_valid_bad_storage_type(self):
        with pytest.raises(ValueError):
            secrets_are_valid(
                StorageSecretsS3(
                    aws_access_key_id="aws_access_key_id",
                    aws_secret_access_key="aws_secret_access_key",
                ),
                "fake_storage_type",
            )

    def test_secrets_are_valid(self):
        # just test we don't error out
        assert not secrets_are_valid(
            StorageSecretsS3(
                aws_access_key_id="aws_access_key_id",
                aws_secret_access_key="aws_secret_access_key",
            ),
            "s3",
        )  # we expect this to fail because they're not real secret values

        # just test we don't error out
        assert not secrets_are_valid(
            StorageSecretsS3(
                aws_access_key_id="aws_access_key_id",
                aws_secret_access_key="aws_secret_access_key",
            ),
            StorageType.s3,
        )  # we expect this to fail because they're not real secret values


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

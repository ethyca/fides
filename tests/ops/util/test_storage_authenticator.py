import pytest
from botocore.exceptions import NoCredentialsError

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    StorageSecrets,
    StorageSecretsS3,
    StorageType,
)
from fides.api.service.storage.storage_authenticator_service import secrets_are_valid
from fides.api.util.aws_util import get_aws_session


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

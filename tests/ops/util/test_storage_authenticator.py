import pytest

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import (
    S3AuthMethod,
    StorageSecrets,
    StorageSecretsS3,
    StorageType,
)
from fides.api.service.storage.storage_authenticator_service import secrets_are_valid
from fides.api.util.storage_authenticator import get_s3_session


class TestGetS3Session:
    def test_storage_secret_none_raises_error(self):
        with pytest.raises(StorageUploadError):
            get_s3_session(S3AuthMethod.SECRET_KEYS.value, None)  # type: ignore

    def tests_unsupported_storage_secret_type_error(self):
        with pytest.raises(ValueError):
            get_s3_session(
                "bad", {StorageSecrets.AWS_ACCESS_KEY_ID: "aws_access_key_id"}  # type: ignore
            )

    def tests_automatic_auth_method(self, loguru_caplog):
        get_s3_session(
            S3AuthMethod.AUTOMATIC.value,  # type: ignore
            {StorageSecrets.AWS_ACCESS_KEY_ID: "aws_access_key_id"},
        )

        assert "created automatic session" in loguru_caplog.text

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

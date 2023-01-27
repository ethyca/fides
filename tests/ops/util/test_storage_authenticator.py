import pytest

from fides.api.ops.common_exceptions import StorageUploadError
from fides.api.ops.schemas.storage.storage import S3AuthMethod, StorageSecrets
from fides.api.ops.util.storage_authenticator import get_s3_session


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

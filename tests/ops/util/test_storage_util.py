import pytest

from fides.api.schemas.storage.storage import StorageSecretsS3, StorageType
from fides.api.util.storage_util import get_schema_for_secrets


class TestStorageUtil:
    def test_get_schema_for_secrets_invalid_storage_type(self):
        with pytest.raises(ValueError):
            get_schema_for_secrets(
                "invalid_storage_type",
                StorageSecretsS3(
                    aws_access_key_id="aws_access_key_id",
                    aws_secret_access_key="aws_secret_access_key",
                ),
            )

        with pytest.raises(ValueError):
            get_schema_for_secrets(
                StorageType.local,
                StorageSecretsS3(
                    aws_access_key_id="aws_access_key_id",
                    aws_secret_access_key="aws_secret_access_key",
                ),
            )

        with pytest.raises(ValueError) as e:
            get_schema_for_secrets(
                StorageType.s3,
                {
                    "aws_access_key_id": "aws_access_key_id",
                    "aws_secret_access_key": "aws_secret_access_key",
                    "fake_key": "aws_secret_access_key",
                },
            )
        assert "Extra inputs are not permitted" in str(e)

    def test_get_schema_for_secrets(self):
        secrets = get_schema_for_secrets(
            "s3",
            StorageSecretsS3(
                aws_access_key_id="aws_access_key_id",
                aws_secret_access_key="aws_secret_access_key",
            ),
        )
        assert secrets.aws_access_key_id == "aws_access_key_id"
        assert secrets.aws_secret_access_key == "aws_secret_access_key"

        secrets = get_schema_for_secrets(
            StorageType.s3,
            StorageSecretsS3(
                aws_access_key_id="aws_access_key_id",
                aws_secret_access_key="aws_secret_access_key",
            ),
        )
        assert secrets.aws_access_key_id == "aws_access_key_id"
        assert secrets.aws_secret_access_key == "aws_secret_access_key"

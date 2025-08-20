from typing import Any, Union

from fides.api.schemas.storage.storage import StorageSecrets, StorageSecretsS3

# AWS S3 multipart upload requirements
AWS_MIN_PART_SIZE = 5 * 1024 * 1024  # 5MB minimum per part (except last)
ZIP_BUFFER_THRESHOLD = 5 * 1024 * 1024  # 5MB threshold for zip buffer uploads
CHUNK_SIZE_THRESHOLD = 5 * 1024 * 1024  # 5MB threshold for chunk-based uploads
LARGE_FILE_THRESHOLD = 25 * 1024 * 1024  # 25MB threshold for large file handling


def update_storage_secrets(
    storage_secrets: Union[StorageSecretsS3, dict[StorageSecrets, Any]]
) -> dict[StorageSecrets, Any]:
    """
    Updates the storage secrets to the expected format.
    """
    if isinstance(storage_secrets, StorageSecretsS3):
        # Convert StorageSecretsS3 to dict[StorageSecrets, Any]
        secrets_dict = {
            StorageSecrets.AWS_ACCESS_KEY_ID: storage_secrets.aws_access_key_id,
            StorageSecrets.AWS_SECRET_ACCESS_KEY: storage_secrets.aws_secret_access_key,
            StorageSecrets.REGION_NAME: storage_secrets.region_name,
            StorageSecrets.AWS_ASSUME_ROLE: storage_secrets.assume_role_arn,
        }
        # Filter out None values
        return {k: v for k, v in secrets_dict.items() if v is not None}

    return storage_secrets

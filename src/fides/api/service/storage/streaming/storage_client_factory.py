from __future__ import annotations

from typing import Any, Optional, Union

from loguru import logger

from fides.api.schemas.storage.storage import (
    StorageSecrets,
    StorageSecretsGCS,
    StorageSecretsS3,
)
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.gcs.gcs_storage_client import (
    create_gcs_storage_client,
)
from fides.api.service.storage.streaming.s3.s3_storage_client import (
    create_s3_storage_client,
)


class CloudStorageClientFactory:
    """Factory for creating cloud storage clients based on storage type and configuration"""

    @staticmethod
    def create_storage_client(
        storage_type: str,
        auth_method: str,
        storage_secrets: Optional[
            Union[StorageSecretsS3, dict[StorageSecrets, Any]]
        ] = None,
    ) -> CloudStorageClient:
        """Create a storage client based on the storage type"""

        if storage_type.lower() == "s3":
            if storage_secrets is None:
                raise ValueError("Storage secrets are required for S3")
            # Convert StorageSecretsS3 to dict[StorageSecrets, Any] for backward compatibility
            if isinstance(storage_secrets, StorageSecretsS3):
                secrets_dict = {
                    StorageSecrets.AWS_ACCESS_KEY_ID: storage_secrets.aws_access_key_id,
                    StorageSecrets.AWS_SECRET_ACCESS_KEY: storage_secrets.aws_secret_access_key,
                    StorageSecrets.REGION_NAME: storage_secrets.region_name,
                    StorageSecrets.AWS_ASSUME_ROLE: storage_secrets.assume_role_arn,
                }
                # Filter out None values
                secrets_dict = {k: v for k, v in secrets_dict.items() if v is not None}
            else:
                secrets_dict = storage_secrets
            return create_s3_storage_client(auth_method, secrets_dict)

        if storage_type.lower() in ["gcs", "gcp", "google"]:
            # GCS streaming is now implemented with full CloudStorageClient interface
            # Convert storage_secrets to the format expected by create_gcs_storage_client
            if isinstance(storage_secrets, StorageSecretsS3):
                # Convert StorageSecretsS3 to the format expected by GCS
                # This is a temporary fix - ideally we'd have proper GCS secrets handling
                gcs_secrets = None  # GCS will use default credentials
            else:
                gcs_secrets = storage_secrets
            return create_gcs_storage_client(auth_method, gcs_secrets)

        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

    @staticmethod
    def create_storage_client_from_config(
        storage_config: dict[str, Any]
    ) -> CloudStorageClient:
        """Create a storage client from a configuration dictionary"""

        storage_type = storage_config.get("type", "s3")
        auth_method = storage_config.get("auth_method", "automatic")
        storage_secrets = storage_config.get("secrets")

        logger.info("Creating storage client for type: {}", storage_type)

        return CloudStorageClientFactory.create_storage_client(
            storage_type=storage_type,
            auth_method=auth_method,
            storage_secrets=storage_secrets,
        )


# Convenience function for backward compatibility
def get_storage_client(
    storage_type: str,
    auth_method: str,
    storage_secrets: Optional[
        Union[StorageSecretsS3, dict[StorageSecrets, Any]]
    ] = None,
) -> CloudStorageClient:
    """Convenience function to create a storage client"""
    return CloudStorageClientFactory.create_storage_client(
        storage_type, auth_method, storage_secrets
    )

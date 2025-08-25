"""S3-specific storage client implementation."""

from __future__ import annotations

from typing import Any, Optional

from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.schemas.storage.storage import AWSAuthMethod, StorageSecrets
from fides.api.service.storage.s3 import create_presigned_url_for_s3
from fides.api.service.storage.streaming.base_storage_client import BaseStorageClient
from fides.api.util.aws_util import get_s3_client


class S3StorageClient(BaseStorageClient):
    """S3-specific storage client implementation.

    Handles S3-specific URI construction, transport parameters, and presigned URL
    generation for the smart-open storage client.
    """

    def __init__(self, storage_secrets: dict[StorageSecrets, Any]):
        """Initialize the storage client with secrets.

        Args:
            storage_secrets: Provider-specific storage credentials and configuration using StorageSecrets enum keys
        """
        super().__init__(storage_secrets)
        self.storage_secrets: dict[StorageSecrets, Any] = storage_secrets

    def build_uri(self, bucket: str, key: str) -> str:
        """Build the S3 URI for the storage location.

        Args:
            bucket: S3 bucket name
            key: Object key/path

        Returns:
            S3 URI string for smart-open
        """
        # Handle custom endpoint (e.g., MinIO) - endpoint_url is not in StorageSecrets enum
        # For now, we'll use standard S3 URI since we only have enum keys
        return f"s3://{bucket}/{key}"

    def get_transport_params(self) -> dict[str, Any]:
        """Get S3-specific transport parameters for smart-open.

        Returns:
            Dictionary of S3 transport parameters for smart-open
        """
        params = {}

        if StorageSecrets.AWS_ACCESS_KEY_ID in self.storage_secrets:
            params["access_key"] = self.storage_secrets[
                StorageSecrets.AWS_ACCESS_KEY_ID
            ]
        if StorageSecrets.AWS_SECRET_ACCESS_KEY in self.storage_secrets:
            params["secret_key"] = self.storage_secrets[
                StorageSecrets.AWS_SECRET_ACCESS_KEY
            ]
        if StorageSecrets.REGION_NAME in self.storage_secrets:
            params["region"] = self.storage_secrets[StorageSecrets.REGION_NAME]
        if StorageSecrets.AWS_ASSUME_ROLE in self.storage_secrets:
            params["assume_role_arn"] = self.storage_secrets[
                StorageSecrets.AWS_ASSUME_ROLE
            ]

        return params

    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate an S3 presigned URL for the object.

        Args:
            bucket: S3 bucket name
            key: Object key/path
            ttl_seconds: Time to live in seconds

        Returns:
            S3 presigned URL for the object

        Raises:
            Exception: If presigned URL generation fails
        """
        try:
            # Storage secrets are already in the right format for get_s3_client
            # get_s3_client expects dict[StorageSecrets, Any] with enum keys
            s3_secrets = self.storage_secrets

            # Determine auth method based on available credentials
            # If AWS credentials are present, use SECRET_KEYS, otherwise use AUTOMATIC
            if (
                StorageSecrets.AWS_ACCESS_KEY_ID in self.storage_secrets
                and StorageSecrets.AWS_SECRET_ACCESS_KEY in self.storage_secrets
                and self.storage_secrets[StorageSecrets.AWS_ACCESS_KEY_ID]
                and self.storage_secrets[StorageSecrets.AWS_SECRET_ACCESS_KEY]
            ):
                auth_method = AWSAuthMethod.SECRET_KEYS.value
            else:
                auth_method = AWSAuthMethod.AUTOMATIC.value

            # Extract assume_role_arn if present for role assumption
            assume_role_arn = None
            if StorageSecrets.AWS_ASSUME_ROLE in self.storage_secrets:
                assume_role_arn = self.storage_secrets[StorageSecrets.AWS_ASSUME_ROLE]

            s3_client = get_s3_client(auth_method, s3_secrets, assume_role_arn)
            return create_presigned_url_for_s3(s3_client, bucket, key, ttl_seconds)
        except Exception as e:
            logger.error(f"Failed to generate S3 presigned URL: {e}")
            raise

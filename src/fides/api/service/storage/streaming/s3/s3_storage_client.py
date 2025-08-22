"""S3-specific storage client implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional

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

    def build_uri(self, bucket: str, key: str) -> str:
        """Build the S3 URI for the storage location.

        Args:
            bucket: S3 bucket name
            key: Object key/path

        Returns:
            S3 URI string for smart-open
        """
        # Handle custom endpoint (e.g., MinIO)
        if "endpoint_url" in self.storage_secrets:
            endpoint = self.storage_secrets["endpoint_url"].rstrip("/")
            return f"{endpoint}/{bucket}/{key}"

        # Standard AWS S3
        return f"s3://{bucket}/{key}"

    def get_transport_params(self) -> dict[str, Any]:
        """Get S3-specific transport parameters for smart-open.

        Returns:
            Dictionary of S3 transport parameters for smart-open
        """
        params = {}

        if "aws_access_key_id" in self.storage_secrets:
            params["access_key"] = self.storage_secrets["aws_access_key_id"]
        if "aws_secret_access_key" in self.storage_secrets:
            params["secret_key"] = self.storage_secrets["aws_secret_access_key"]
        if "region_name" in self.storage_secrets:
            params["region"] = self.storage_secrets["region_name"]
        if "endpoint_url" in self.storage_secrets:
            params["endpoint_url"] = self.storage_secrets["endpoint_url"]

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
            # Convert storage secrets to the format expected by get_s3_client
            # get_s3_client expects dict[str, Any] where keys are the enum values (strings)
            s3_secrets: Dict[str, Any] = {}

            # Map the string keys from storage_secrets to the format expected by get_s3_client
            # The keys should be the enum values (strings), not the enum objects
            if "aws_access_key_id" in self.storage_secrets:
                s3_secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value] = (
                    self.storage_secrets["aws_access_key_id"]
                )
            if "aws_secret_access_key" in self.storage_secrets:
                s3_secrets[StorageSecrets.AWS_SECRET_ACCESS_KEY.value] = (
                    self.storage_secrets["aws_secret_access_key"]
                )
            if "region_name" in self.storage_secrets:
                s3_secrets[StorageSecrets.REGION_NAME.value] = self.storage_secrets[
                    "region_name"
                ]
            if "assume_role_arn" in self.storage_secrets:
                s3_secrets[StorageSecrets.AWS_ASSUME_ROLE.value] = self.storage_secrets[
                    "assume_role_arn"
                ]

            logger.debug("Converted storage secrets for S3 client: {}", s3_secrets)

            # Use a default auth method if not specified
            auth_method = self.storage_secrets.get(
                "auth_method", AWSAuthMethod.SECRET_KEYS.value
            )

            s3_client = get_s3_client(auth_method, s3_secrets)
            return create_presigned_url_for_s3(s3_client, bucket, key, ttl_seconds)
        except Exception as e:
            logger.error(f"Failed to generate S3 presigned URL: {e}")
            raise

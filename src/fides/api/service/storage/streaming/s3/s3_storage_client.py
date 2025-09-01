"""S3-specific storage client implementation."""

from __future__ import annotations

from typing import Any, Optional

from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.schemas.storage.storage import AWSAuthMethod
from fides.api.service.storage.s3 import create_presigned_url_for_s3
from fides.api.service.storage.streaming.base_storage_client import BaseStorageClient
from fides.api.util.aws_util import get_s3_client


class S3StorageClient(BaseStorageClient):
    """S3-specific storage client implementation.

    Handles S3-specific URI construction, transport parameters, and presigned URL
    generation for the smart-open storage client.
    """

    def __init__(self, auth_method: str, storage_secrets: dict[str, Any]):
        """Initialize the storage client with secrets.

        Args:
            storage_secrets: Provider-specific storage credentials and configuration using string keys
                           (e.g., "aws_access_key_id", "region_name") from format_secrets()
        """
        super().__init__(storage_secrets)
        self.storage_secrets: dict[str, Any] = storage_secrets
        self.auth_method = auth_method

    def build_uri(self, bucket: str, key: str) -> str:
        """Build S3 URI for the given bucket and key.

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
        Type annotation: get_s3_client returns a boto3 S3 client object, not a Session
        This is what smart-open expects for the "client" transport parameter

        Returns:
            Dictionary of S3 transport parameters for smart-open
        """
        params: dict[str, Any] = {}

        # Create S3 client for smart-open
        try:
            # Determine auth method based on available credentials
            if self.auth_method == AWSAuthMethod.AUTOMATIC.value:

                # For automatic authentication, check if region is available
                if not self.storage_secrets.get("region_name", None):
                    logger.warning(
                        "No region specified in storage secrets for automatic authentication"
                        "This may cause credential issues - consider setting a default region"
                    )

            # Extract assume_role_arn if present
            assume_role_arn = None
            if (
                "assume_role_arn" in self.storage_secrets
                and self.storage_secrets["assume_role_arn"]
            ):
                assume_role_arn = self.storage_secrets["assume_role_arn"]
                logger.debug(f"Using assume role ARN: {assume_role_arn}")

            # Create S3 client using existing utility
            # get_s3_client returns a boto3 S3 client, not a Session
            s3_client: Any = None
            try:
                s3_client = get_s3_client(
                    self.auth_method, self.storage_secrets, assume_role_arn  # type: ignore
                )
                logger.debug("Successfully created S3 client")
            except Exception as e:
                # For automatic authentication, try to provide more helpful error messages
                if self.auth_method == AWSAuthMethod.AUTOMATIC.value:
                    logger.error(
                        f"Failed to create S3 client with automatic authentication: {e}. "
                        "This usually means AWS credentials are not available in the environment"
                        "Please ensure AWS credentials are configured via environment variables, IAM roles, or AWS profiles"
                    )
                    raise ValueError(
                        f"Automatic AWS authentication failed: {e}. Please check your AWS credential configuration."
                    )
                raise

            params["client"] = s3_client

        except Exception as e:
            logger.error(f"Failed to create S3 client for smart-open: {e}")
            raise

        # Include credentials at top level for compatibility
        # Note: When using an S3 client, these credential parameters are not needed
        # and will be ignored by smart-open, causing warnings
        # Only include them if no S3 client is provided (fallback scenario)
        if not params.get("client"):
            for key, transport_key in [
                ("aws_access_key_id", "access_key"),
                ("aws_secret_access_key", "secret_key"),
                ("region_name", "region"),
                ("assume_role_arn", "assume_role_arn"),
            ]:
                if key in self.storage_secrets and self.storage_secrets[key]:
                    params[transport_key] = self.storage_secrets[key]

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
            # Extract assume_role_arn if present for role assumption
            assume_role_arn = None
            if "assume_role_arn" in self.storage_secrets:
                assume_role_arn = self.storage_secrets["assume_role_arn"]

            # get_s3_client returns a boto3 S3 client, not a Session
            s3_client: Any = get_s3_client(
                self.auth_method, self.storage_secrets, assume_role_arn  # type: ignore
            )
            return create_presigned_url_for_s3(s3_client, bucket, key, ttl_seconds)
        except Exception as e:
            logger.error(f"Failed to generate S3 presigned URL: {e}")
            raise

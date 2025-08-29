"""S3-specific storage client implementation."""

from __future__ import annotations

from typing import Any, Optional

from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.schemas.storage.storage import AWSAuthMethod
from fides.api.service.storage.s3 import create_presigned_url_for_s3
from fides.api.service.storage.streaming.base_storage_client import BaseStorageClient
from fides.api.util.aws_util import get_s3_client

# Type annotation: get_s3_client returns a boto3 S3 client object, not a Session
# This is what smart-open expects for the "client" transport parameter


class S3StorageClient(BaseStorageClient):
    """S3-specific storage client implementation.

    Handles S3-specific URI construction, transport parameters, and presigned URL
    generation for the smart-open storage client.
    """

    def __init__(self, storage_secrets: dict[str, Any]):
        """Initialize the storage client with secrets.

        Args:
            storage_secrets: Provider-specific storage credentials and configuration using string keys
                           (e.g., "aws_access_key_id", "region_name") from format_secrets()
        """
        super().__init__(storage_secrets)
        self.storage_secrets: dict[str, Any] = storage_secrets

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

        Returns:
            Dictionary of S3 transport parameters for smart-open
        """
        params: dict[str, Any] = {}

        # Create S3 client for smart-open
        try:
            # Determine auth method based on available credentials
            if (
                "aws_access_key_id" in self.storage_secrets
                and "aws_secret_access_key" in self.storage_secrets
                and self.storage_secrets["aws_access_key_id"]
                and self.storage_secrets["aws_secret_access_key"]
            ):
                auth_method = AWSAuthMethod.SECRET_KEYS.value
                logger.debug("Using SECRET_KEYS authentication method")
            else:
                auth_method = AWSAuthMethod.AUTOMATIC.value
                logger.debug(
                    "Using AUTOMATIC authentication method - relying on AWS credential chain"
                )

                # For automatic authentication, check if region is available
                if (
                    "region_name" in self.storage_secrets
                    and self.storage_secrets["region_name"]
                ):
                    logger.debug(
                        f"Region specified in storage secrets: {self.storage_secrets['region_name']}"
                    )
                else:
                    logger.warning(
                        "No region specified in storage secrets for automatic authentication"
                    )
                    logger.warning(
                        "This may cause credential issues - consider setting a default region"
                    )

            # Extract assume_role_arn if present
            assume_role_arn = None
            if "assume_role_arn" in self.storage_secrets:
                assume_role_arn = self.storage_secrets["assume_role_arn"]
                logger.debug(f"Using assume role ARN: {assume_role_arn}")

            # Create S3 client using existing utility
            # get_s3_client returns a boto3 S3 client, not a Session
            s3_client: Any = None
            try:
                logger.debug(f"Creating S3 client with auth_method={auth_method}")
                s3_client = get_s3_client(
                    auth_method, self.storage_secrets, assume_role_arn  # type: ignore
                )
                logger.debug("Successfully created S3 client")
            except Exception as e:
                # For automatic authentication, try to provide more helpful error messages
                if auth_method == AWSAuthMethod.AUTOMATIC.value:
                    logger.error(
                        f"Failed to create S3 client with automatic authentication: {e}"
                    )
                    logger.error(
                        "This usually means AWS credentials are not available in the environment"
                    )
                    logger.error(
                        "Please ensure AWS credentials are configured via environment variables, IAM roles, or AWS profiles"
                    )
                    raise ValueError(
                        f"Automatic AWS authentication failed: {e}. Please check your AWS credential configuration."
                    )
                else:
                    raise

            params["client"] = s3_client

        except Exception as e:
            logger.error(f"Failed to create S3 client for smart-open: {e}")
            raise

        # Include credentials at top level for compatibility
        if (
            "aws_access_key_id" in self.storage_secrets
            and self.storage_secrets["aws_access_key_id"]
        ):
            params["access_key"] = self.storage_secrets["aws_access_key_id"]
        if (
            "aws_secret_access_key" in self.storage_secrets
            and self.storage_secrets["aws_secret_access_key"]
        ):
            params["secret_key"] = self.storage_secrets["aws_secret_access_key"]
        if (
            "region_name" in self.storage_secrets
            and self.storage_secrets["region_name"]
        ):
            params["region"] = self.storage_secrets["region_name"]
        if (
            "assume_role_arn" in self.storage_secrets
            and self.storage_secrets["assume_role_arn"]
        ):
            params["assume_role_arn"] = self.storage_secrets["assume_role_arn"]

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

            # Determine auth method based on available credentials
            # If AWS credentials are present, use SECRET_KEYS, otherwise use AUTOMATIC
            if (
                "aws_access_key_id" in self.storage_secrets
                and "aws_secret_access_key" in self.storage_secrets
                and self.storage_secrets["aws_access_key_id"]
                and self.storage_secrets["aws_secret_access_key"]
            ):
                auth_method = AWSAuthMethod.SECRET_KEYS.value
            else:
                auth_method = AWSAuthMethod.AUTOMATIC.value

            # Extract assume_role_arn if present for role assumption
            assume_role_arn = None
            if "assume_role_arn" in self.storage_secrets:
                assume_role_arn = self.storage_secrets["assume_role_arn"]

            # get_s3_client returns a boto3 S3 client, not a Session
            s3_client: Any = get_s3_client(
                auth_method, self.storage_secrets, assume_role_arn  # type: ignore
            )
            return create_presigned_url_for_s3(s3_client, bucket, key, ttl_seconds)
        except Exception as e:
            logger.error(f"Failed to generate S3 presigned URL: {e}")
            raise

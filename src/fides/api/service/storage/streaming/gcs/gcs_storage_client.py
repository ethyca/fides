"""GCS-specific storage client implementation."""

from __future__ import annotations

from typing import Any, Optional

from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.schemas.storage.storage import GCSAuthMethod
from fides.api.service.storage.gcs import get_gcs_blob
from fides.api.service.storage.streaming.base_storage_client import BaseStorageClient
from fides.config import CONFIG


class GCSStorageClient(BaseStorageClient):
    """GCS-specific storage client implementation.

    Handles GCS-specific URI construction, transport parameters, and signed URL
    generation for the smart-open storage client.
    """

    def build_uri(self, bucket: str, key: str) -> str:
        """Build the GCS URI for the storage location.

        Args:
            bucket: GCS bucket name
            key: Object key/path

        Returns:
            GCS URI string for smart-open
        """
        return f"gs://{bucket}/{key}"

    def get_transport_params(self) -> dict[str, Any]:
        """Get GCS-specific transport parameters for smart-open.

        Returns:
            Dictionary of GCS transport parameters for smart-open
        """
        params = {}

        if "service_account_info" in self.storage_secrets:
            params["credentials"] = self.storage_secrets["service_account_info"]
        elif "service_account_file" in self.storage_secrets:
            params["credentials"] = self.storage_secrets["service_account_file"]

        return params

    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a GCS signed URL for the object.

        Args:
            bucket: GCS bucket name
            key: Object key/path
            ttl_seconds: Time to live in seconds

        Returns:
            GCS signed URL for the object

        Raises:
            Exception: If signed URL generation fails
        """
        try:
            # Convert storage secrets to the format expected by get_gcs_blob
            gcs_secrets = {}
            if "private_key_id" in self.storage_secrets:
                gcs_secrets["private_key_id"] = self.storage_secrets["private_key_id"]
            if "private_key" in self.storage_secrets:
                gcs_secrets["private_key"] = self.storage_secrets["private_key"]
            if "client_email" in self.storage_secrets:
                gcs_secrets["client_email"] = self.storage_secrets["client_email"]
            if "client_id" in self.storage_secrets:
                gcs_secrets["client_id"] = self.storage_secrets["client_id"]
            if "type" in self.storage_secrets:
                gcs_secrets["type"] = self.storage_secrets["type"]

            # Use a default auth method if not specified
            auth_method = self.storage_secrets.get(
                "auth_method", GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value
            )

            blob = get_gcs_blob(auth_method, gcs_secrets, bucket, key)

            # Ensure we have the blob metadata
            blob.reload()

            # Generate signed URL with TTL
            expiration = (
                ttl_seconds
                if ttl_seconds
                else CONFIG.security.subject_request_download_link_ttl_seconds
            )
            return blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET",
            )
        except Exception as e:
            logger.error(f"Failed to generate GCS signed URL: {e}")
            raise

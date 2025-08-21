"""Azure-specific storage client implementation."""

from __future__ import annotations

from typing import Any, Optional

from fideslang.validation import AnyHttpUrlString

from fides.api.service.storage.streaming.base_storage_client import BaseStorageClient


class AzureStorageClient(BaseStorageClient):
    """Azure-specific storage client implementation.

    Handles Azure-specific URI construction, transport parameters, and signed URL
    generation for the smart-open storage client.
    """

    def build_uri(self, bucket: str, key: str) -> str:
        """Build the Azure URI for the storage location.

        Args:
            bucket: Azure container name
            key: Object key/path

        Returns:
            Azure URI string for smart-open

        Raises:
            ValueError: If account_name is not provided in storage secrets
        """
        raise NotImplementedError("Azure storage is not yet implemented")

    def get_transport_params(self) -> dict[str, Any]:
        """Get Azure-specific transport parameters for smart-open.

        Returns:
            Dictionary of Azure transport parameters for smart-open
        """
        raise NotImplementedError("Azure storage is not yet implemented")

    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate an Azure signed URL for the object.

        Args:
            bucket: Azure container name
            key: Object key/path
            ttl_seconds: Time to live in seconds (not yet implemented)

        Returns:
            Azure signed URL for the object

        Raises:
            NotImplementedError: Azure presigned URL generation not yet implemented
        """
        # Azure storage not yet implemented
        raise NotImplementedError(
            f"Presigned URL generation not yet implemented for Azure storage. "
            f"Container: {bucket}, Key: {key}"
        )

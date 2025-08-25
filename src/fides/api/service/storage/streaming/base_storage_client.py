"""Base abstract class for cloud storage clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from fideslang.validation import AnyHttpUrlString


class BaseStorageClient(ABC):
    """Abstract base class for cloud storage clients.

    This class defines the interface that all provider-specific storage clients
    must implement. It provides a common contract for URI building, transport
    parameters, and presigned URL generation.
    """

    def __init__(self, storage_secrets: Any):
        """Initialize the storage client with secrets.

        Args:
            storage_secrets: Provider-specific storage credentials and configuration.
                           Derived classes will specify the exact type they expect.
        """
        self.storage_secrets = storage_secrets

    @abstractmethod
    def build_uri(self, bucket: str, key: str) -> str:
        """Build the URI for the storage location.

        Args:
            bucket: Storage bucket/container name
            key: Object key/path

        Returns:
            URI string for smart-open
        """

    @abstractmethod
    def get_transport_params(self) -> dict[str, Any]:
        """Get transport parameters for smart-open.

        Returns:
            Dictionary of transport parameters for smart-open
        """

    @abstractmethod
    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a presigned URL for the object.

        Args:
            bucket: Storage bucket/container name
            key: Object key/path
            ttl_seconds: Time to live in seconds

        Returns:
            Presigned URL for the object
        """

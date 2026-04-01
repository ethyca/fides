"""Key provider abstraction for envelope encryption."""

from abc import ABC, abstractmethod


class KeyProviderError(Exception):
    """Raised when a key provider operation fails."""


class KeyProvider(ABC):
    """Abstract base class for envelope encryption key providers."""

    @abstractmethod
    def get_dek(self) -> str:
        """Retrieve and unwrap the Data Encryption Key."""
        ...

    @abstractmethod
    def encrypt_dek(self, dek: str) -> str:
        """Encrypt a DEK for storage.

        Returns the encrypted DEK as a base64-encoded string.
        """
        ...

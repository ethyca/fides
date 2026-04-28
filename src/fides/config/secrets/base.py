"""Base classes for the secret provider abstraction."""

from abc import ABC, abstractmethod
from typing import Dict, KeysView


class SecretProviderError(Exception):
    """Raised when a secret provider operation fails."""


class SecretValue:
    """Wrapper around a secret dict that prevents accidental credential leakage.

    Supports subscript access (``secret["username"]``) but overrides string
    coercion so credentials never appear in logs, tracebacks, or debug output.
    """

    def __init__(self, data: Dict[str, str]) -> None:
        self._data = data

    def __getitem__(self, key: str) -> str:
        return self._data[key]

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SecretValue):
            return self._data == other._data
        return NotImplemented

    def __repr__(self) -> str:
        return "<redacted>"

    def __str__(self) -> str:
        return "<redacted>"

    def keys(self) -> KeysView[str]:
        return self._data.keys()


class SecretProvider(ABC):
    """Abstract base class for secret providers."""

    @abstractmethod
    def get_secret(self, secret_id: str) -> SecretValue:
        """Return the current value of a named secret."""

    @abstractmethod
    def invalidate(self, secret_id: str) -> None:
        """Mark a cached secret as stale, forcing the next fetch to refresh."""

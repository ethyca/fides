"""Base classes for the secret provider abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class SecretProviderError(Exception):
    """Raised when a secret provider operation fails."""


class SecretValue:
    """Wrapper around a secret dict that prevents accidental credential leakage.

    Supports subscript access (``secret["username"]``) but overrides string
    coercion so credentials never appear in logs, tracebacks, or debug output.

    Uses ``__slots__`` to prevent ``vars()`` / ``__dict__`` access, which
    blocks error reporters (Sentry, Datadog APM) from capturing the secret
    data when serializing local variables on exception frames.
    """

    __slots__ = ("_data",)

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def __reduce__(self) -> None:  # type: ignore[override]
        raise TypeError("SecretValue cannot be pickled")

    def __getstate__(self) -> None:
        raise TypeError("SecretValue cannot be serialized")

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SecretValue):
            return self._data == other._data
        return NotImplemented

    __hash__ = None  # type: ignore[assignment]  # unhashable by design

    def __iter__(self) -> None:
        raise TypeError(
            "SecretValue cannot be iterated — use 'key in sv' to check fields"
        )

    def __repr__(self) -> str:
        return "<redacted>"

    def __str__(self) -> str:
        return "<redacted>"


class SecretProvider(ABC):
    """Abstract base class for secret providers."""

    @abstractmethod
    def get_secret(self, secret_id: str) -> SecretValue:
        """Return the current value of a named secret."""

    @abstractmethod
    def invalidate(self, secret_id: str) -> None:
        """Mark a cached secret as stale, forcing the next fetch to refresh."""

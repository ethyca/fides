"""Static secret provider — returns fixed values from config."""

from typing import Any, Dict

from loguru import logger as log

from fides.config.secrets.base import SecretProvider, SecretProviderError, SecretValue


class StaticSecretProvider(SecretProvider):
    """Returns pre-configured secret values. Used for static credentials
    (environment variables / TOML config) where rotation is not needed.
    """

    def __init__(self, secrets: Dict[str, Dict[str, Any]]) -> None:
        self._secrets = secrets

    def get_secret(self, secret_id: str) -> SecretValue:
        try:
            return SecretValue(self._secrets[secret_id])
        except KeyError:
            raise SecretProviderError(f"Unknown secret_id: {secret_id!r}") from None

    def invalidate(self, secret_id: str) -> None:
        log.debug(
            "invalidate() called on StaticSecretProvider for {!r} (no-op)",
            secret_id,
        )

"""Static secret provider — caches credentials from config at construction time."""

from typing import Dict

from loguru import logger as log

from fides.config import CONFIG
from fides.config.secrets.base import SecretProvider, SecretProviderError, SecretValue

DATABASE_CREDENTIALS_KEY = "_db_credentials"
DATABASE_READONLY_CREDENTIALS_KEY = "_db_readonly_credentials"


class StaticSecretProvider(SecretProvider):
    """Returns credentials read from config at construction time.

    Used for static credentials (environment variables / TOML config)
    where rotation is not needed.  Reads ``CONFIG.database`` once and
    caches the values as ``SecretValue`` objects under well-known keys.
    """

    def __init__(self) -> None:
        db = CONFIG.database
        self._secrets: Dict[str, SecretValue] = {
            DATABASE_CREDENTIALS_KEY: SecretValue(
                {"username": db.user, "password": db.raw_password}
            ),
        }
        if db.readonly_server:
            self._secrets[DATABASE_READONLY_CREDENTIALS_KEY] = SecretValue(
                {
                    "username": db.readonly_user,
                    "password": db.raw_readonly_password,
                }
            )

    def get_secret(self, secret_id: str) -> SecretValue:
        try:
            return self._secrets[secret_id]
        except KeyError:
            raise SecretProviderError(f"Unknown secret_id: {secret_id!r}") from None

    def invalidate(self, secret_id: str) -> None:
        log.debug(
            "invalidate() called on StaticSecretProvider for {!r} (no-op)",
            secret_id,
        )

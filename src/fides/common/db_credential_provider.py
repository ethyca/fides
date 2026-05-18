"""Database credential resolution with retry-on-auth-failure and exception sanitization.

DBCredentialProvider sits between SQLAlchemy engine creators and the SecretProvider
abstraction.  It resolves credentials (from static config or a secret store), wraps
connection attempts with a single retry on authentication failure during credential
rotation, and sanitizes all connection exceptions to prevent credential leakage.

Driver-agnostic: does not import psycopg2 or asyncpg.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional, TypeVar
from urllib.parse import quote, quote_plus, urlencode

from loguru import logger as log
from psycopg2 import (  # type: ignore[import-untyped]
    OperationalError as Psycopg2OperationalError,
)

from fides.config import CONFIG
from fides.config.secrets import StaticSecretProvider, get_secret_provider
from fides.config.secrets.static_provider import (
    DATABASE_CREDENTIALS_KEY,
    DATABASE_READONLY_CREDENTIALS_KEY,
)

__all__ = ["DBCredentialProvider", "SanitizedConnectionError"]

T = TypeVar("T")

_AUTH_SQLSTATES = frozenset({"28P01", "28000"})
_AUTH_RETRY_DELAY = 1.5  # seconds — propagation window for AWS rotation


class SanitizedConnectionError(Exception):
    """Connection error with credentials stripped. Safe to log and report."""

    __slots__ = ("sqlstate",)

    def __init__(self, message: str, sqlstate: Optional[str] = None) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate


class DBCredentialProvider:
    """Resolves database credentials and wraps connection attempts
    with retry-on-auth-failure and exception sanitization.
    """

    def __init__(self) -> None:
        self._provider = get_secret_provider()

    # ------------------------------------------------------------------
    # Credential resolution
    # ------------------------------------------------------------------

    @property
    def is_dynamic(self) -> bool:
        """True when using a non-static provider (credentials can rotate)."""
        return not isinstance(self._provider, StaticSecretProvider)

    def _get_secret_id(self, readonly: bool) -> str:
        """Resolve which secret ID to use.

        For dynamic providers: uses configured secret IDs with readonly -> primary fallback.
        For static provider: uses the well-known default keys.
        """
        if self.is_dynamic:
            credential_secret_name = CONFIG.database.credential_secret_name
            if credential_secret_name is None:
                raise ValueError(
                    "secrets.provider is not 'static' but "
                    "database.credential_secret_name is not set."
                )
            if readonly:
                return (
                    CONFIG.database.readonly_credential_secret_name
                    or credential_secret_name
                )
            return credential_secret_name
        else:
            if readonly and CONFIG.database.readonly_server:
                return DATABASE_READONLY_CREDENTIALS_KEY
            return DATABASE_CREDENTIALS_KEY

    def get_credentials(self, readonly: bool = False) -> Dict[str, Any]:
        """Return ``{host, port, user, password, dbname}`` for a database connection."""
        db = CONFIG.database

        # Host, port, dbname always from config
        creds = {
            "host": db.server,
            "port": int(db.port),
            "dbname": db.test_db if CONFIG.test_mode else db.db,
        }
        if readonly and db.readonly_server:
            creds["host"] = db.readonly_server
            creds["port"] = int(db.readonly_port or db.port)
            creds["dbname"] = db.readonly_db or db.db

        # Get credentials (user/password) from the provider
        secret = self._provider.get_secret(self._get_secret_id(readonly))
        creds["user"] = secret["username"]
        creds["password"] = secret["password"]

        return creds

    def get_database_url(
        self, driver: str = "postgresql+psycopg2", readonly: bool = False
    ) -> str:
        """Build a SQLAlchemy database URL with credentials from the provider.

        Includes connection params (SSL, keepalives, etc.) from CONFIG.database.params
        as query parameters, matching the old sync_database_uri behavior.
        """
        creds = self.get_credentials(readonly=readonly)
        user = quote_plus(creds["user"])
        password = quote_plus(creds["password"])
        url = f"{driver}://{user}:{password}@{creds['host']}:{creds['port']}/{creds['dbname']}"

        params = CONFIG.database.params
        if params:
            url += "?" + urlencode(params, quote_via=quote, safe="/")
        return url

    # ------------------------------------------------------------------
    # Connection with retry
    # ------------------------------------------------------------------

    def connect_with_retry(
        self,
        connect_fn: Callable[..., T],
        connect_kwargs: Dict[str, Any],
        readonly: bool = False,
    ) -> T:
        """Attempt a connection; on auth failure with dynamic credentials, retry once.

        Args:
            connect_fn: Driver connect callable (e.g. ``psycopg2.connect``).
            connect_kwargs: Non-credential connection kwargs (keepalives, SSL).
                Credentials are merged in from ``get_credentials()``.
            readonly: Whether to use readonly credentials.

        Returns:
            The raw connection object.

        Raises:
            SanitizedConnectionError: On any connection failure, with
                connection parameters stripped from the exception message.
        """
        creds = self.get_credentials(readonly=readonly)
        kwargs = {**connect_kwargs, **creds}

        try:
            return connect_fn(**kwargs)
        except Exception as exc:
            if self.is_dynamic and self._is_auth_error(exc):
                return self._retry_with_fresh_credentials(
                    connect_fn, connect_kwargs, readonly, exc
                )
            raise self._sanitize_exception(exc) from None

    def _retry_with_fresh_credentials(
        self,
        connect_fn: Callable[..., T],
        connect_kwargs: Dict[str, Any],
        readonly: bool,
        original_exc: Exception,
    ) -> T:
        """Invalidate the cached secret, wait for propagation, retry once."""
        secret_id = self._get_secret_id(readonly)

        log.warning(
            "Connection failure ({}: SQLSTATE {}), invalidating secret {!r} and retrying",
            type(original_exc).__name__,
            self._extract_sqlstate(original_exc),
            secret_id,
        )
        self._provider.invalidate(secret_id)

        # Safe in both sync and async paths: async engine creators run inside
        # SQLAlchemy's greenlet bridge, so time.sleep blocks the greenlet, not
        # the event loop (same mechanism as await_only(asyncpg.connect(...))).
        time.sleep(_AUTH_RETRY_DELAY)

        fresh_creds = self.get_credentials(readonly=readonly)
        kwargs = {**connect_kwargs, **fresh_creds}

        try:
            return connect_fn(**kwargs)
        except Exception as exc:
            log.error(
                "Retry also failed (SQLSTATE {}), credentials may be wrong",
                self._extract_sqlstate(exc),
            )
            raise self._sanitize_exception(exc) from None

    # ------------------------------------------------------------------
    # Error detection and sanitization
    # ------------------------------------------------------------------

    @staticmethod
    def _is_auth_error(exc: Exception) -> bool:
        """Detect connection failures that may indicate credential rotation.

        Checks SQLSTATE codes first (asyncpg always provides these).
        Falls back to message matching for psycopg2, which does not
        populate pgcode on connection-time errors.  The fallback string
        comes from PostgreSQL's auth handshake, which is always English
        (sent before any locale is configured).

        Also matches any psycopg2 OperationalError as a broad fallback,
        because RDS Proxy and other managed PostgreSQL services may return
        non-standard error messages on auth failure that don't match the
        specific patterns above. The cost of retrying
        on a non-auth OperationalError is one extra Secrets Manager call
        and a 1.5s delay, which is acceptable given the alternative is
        15 minutes of 500s.
        """
        if DBCredentialProvider._extract_sqlstate(exc) in _AUTH_SQLSTATES:
            return True
        if "password authentication failed" in str(exc).lower():
            return True
        return isinstance(exc, Psycopg2OperationalError)

    @staticmethod
    def _extract_sqlstate(exc: Exception) -> Optional[str]:
        """Extract SQLSTATE from a driver exception for logging."""
        return getattr(exc, "pgcode", None) or getattr(exc, "sqlstate", None)

    @staticmethod
    def _sanitize_exception(exc: Exception) -> SanitizedConnectionError:
        """Replace a driver exception with a sanitized version.

        Constructs a new exception containing only the exception type name
        and SQLSTATE code.  Raised with ``from None`` by callers to break
        the exception chain and prevent credential leakage through error
        reporters that serialize ``__cause__``.
        """
        sqlstate = DBCredentialProvider._extract_sqlstate(exc)
        exc_type = type(exc).__name__
        if sqlstate:
            msg = f"Database connection failed: {exc_type} (SQLSTATE {sqlstate})"
        else:
            msg = f"Database connection failed: {exc_type}"
        return SanitizedConnectionError(msg, sqlstate=sqlstate)

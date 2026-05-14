"""
SQLAlchemy engine ``creator`` callables for dynamic credential resolution.

The ``creator`` pattern passes a callable to ``create_engine`` /
``create_async_engine`` instead of a connection URI.  SQLAlchemy calls the
creator every time the pool needs a new connection, so credentials are
resolved at **connection time** rather than engine construction time.

Credential resolution, auth-failure retry, and exception sanitization are
handled by ``DBCredentialProvider``.

Because creators run on every new pool connection, they must stay
lightweight — avoid expensive I/O, network calls, or heavy computation.
Credential lookups should return cached values in the common case.
"""

from __future__ import annotations

import ssl
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

import asyncpg  # type: ignore[import-untyped]
import psycopg2  # type: ignore[import-untyped]
from sqlalchemy.dialects.postgresql.asyncpg import (
    AsyncAdapt_asyncpg_connection,
    AsyncAdapt_asyncpg_dbapi,
)
from sqlalchemy.util.concurrency import await_only  # type: ignore[import-untyped]

from fides.common.db_credential_provider import DBCredentialProvider
from fides.config import CONFIG

# Dialect-only URLs for the creator pattern — no credentials, just driver selection.
SYNC_DIALECT_URL = "postgresql+psycopg2://"
ASYNC_DIALECT_URL = "postgresql+asyncpg://"

# Shared dbapi instance for async creators — reused across connections.
_asyncpg_dbapi = AsyncAdapt_asyncpg_dbapi(asyncpg)

# Module-level provider — all engines share one instance (and one secret cache).
db_cred_provider = DBCredentialProvider()


# ---------------------------------------------------------------------------
# Sync creators (psycopg2)
# ---------------------------------------------------------------------------


def make_sync_creator(
    connect_args: Optional[Dict[str, Any]] = None,
    readonly: bool = False,
) -> Callable[[], Any]:
    """Return a creator callable for psycopg2 engines.

    The factory captures per-engine config (keepalives, SSL) in the closure.
    Credentials are resolved via ``DBCredentialProvider`` on every call,
    with automatic retry on auth failure for dynamic credentials.

    When using ``creator``, SQLAlchemy ignores ``connect_args`` passed to
    ``create_engine``, so all connection parameters must be baked in here.
    """
    extra_kwargs = dict(connect_args) if connect_args else {}

    def creator() -> Any:
        return db_cred_provider.connect_with_retry(
            connect_fn=psycopg2.connect,
            connect_kwargs=extra_kwargs,
            readonly=readonly,
        )

    return creator


# ---------------------------------------------------------------------------
# Async creators (asyncpg)
# ---------------------------------------------------------------------------


def make_async_creator(
    readonly: bool = False,
) -> Callable[[], Any]:
    """Return a creator callable for asyncpg engines (SA 1.4.27).

    The factory builds the SSL context and asyncpg-compatible params from
    CONFIG, capturing them in the closure.  Credentials are resolved via
    ``DBCredentialProvider`` on every call.

    The creator replaces ``dialect.connect()`` in SQLAlchemy's pool.  For
    async engines the pool runs inside a greenlet bridge, so ``await_only``
    is valid.  Must return ``AsyncAdapt_asyncpg_connection`` (SA's sync
    wrapper) since the pool operates in sync mode through greenlets.

    TODO: Replace with ``async_creator`` API after SQLAlchemy 2.0 upgrade.
    """
    db_params = (
        (CONFIG.database.readonly_params or CONFIG.database.params)
        if readonly
        else CONFIG.database.params
    )
    ssl_context = _build_ssl_context(db_params)
    async_params = _convert_asyncpg_params(db_params)

    # When we have a full SSLContext (from sslrootcert), it takes priority
    # over the raw ssl string (from sslmode). Otherwise kw.update(async_params)
    # would overwrite the SSLContext with e.g. "require", losing cert verification.
    if ssl_context:
        async_params.pop("ssl", None)

    extra_kwargs: Dict[str, Any] = {}
    if ssl_context:
        extra_kwargs["ssl"] = ssl_context
    if async_params:
        extra_kwargs.update(async_params)

    def _connect_asyncpg(**kwargs: Any) -> AsyncAdapt_asyncpg_connection:
        kw = {
            "host": kwargs.pop("host"),
            "port": kwargs.pop("port"),
            "user": kwargs.pop("user"),
            "password": kwargs.pop("password"),
            "database": kwargs.pop("dbname"),
        }
        kw.update(kwargs)
        raw_conn = await_only(asyncpg.connect(**kw))
        return AsyncAdapt_asyncpg_connection(_asyncpg_dbapi, raw_conn)

    def creator() -> Any:
        return db_cred_provider.connect_with_retry(
            connect_fn=_connect_asyncpg,
            connect_kwargs=extra_kwargs,
            readonly=readonly,
        )

    return creator


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_ssl_context(params: Dict[str, Any]) -> Optional[ssl.SSLContext]:
    """Build an ``ssl.SSLContext`` from DB params if ``sslrootcert`` is set."""
    sslrootcert = params.get("sslrootcert")
    if not sslrootcert:
        return None
    ctx = ssl.create_default_context(cafile=sslrootcert)
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def _convert_asyncpg_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert DB params dict for asyncpg compatibility.

    asyncpg uses ``ssl`` instead of ``sslmode`` and does not accept
    ``sslrootcert`` as a connection parameter (it's handled via
    ``ssl.SSLContext`` passed separately).

    See: https://github.com/MagicStack/asyncpg/issues/737
    ref: https://github.com/sqlalchemy/sqlalchemy/discussions/5975
    """
    converted = deepcopy(params)
    if "sslmode" in converted:
        converted["ssl"] = converted.pop("sslmode")
    converted.pop("sslrootcert", None)
    return converted

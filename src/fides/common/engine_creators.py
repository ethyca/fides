"""
SQLAlchemy engine ``creator`` callables for dynamic credential resolution.

The ``creator`` pattern passes a callable to ``create_engine`` /
``create_async_engine`` instead of a connection URI.  SQLAlchemy calls the
creator every time the pool needs a new connection, so credentials are
resolved at **connection time** rather than engine construction time.

Today the credential helpers read from static config (``CONFIG.database``).
A future secret-provider integration will swap them to call
``provider.get_secret()`` — the rest of the engine code stays the same.

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

from fides.config import CONFIG

# Shared dbapi instance for async creators — reused across connections.
_asyncpg_dbapi = AsyncAdapt_asyncpg_dbapi(asyncpg)


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------


def get_db_credentials() -> Dict[str, Any]:
    """Return DB credentials from static config."""
    db_settings = CONFIG.database
    dbname = db_settings.test_db if CONFIG.test_mode else db_settings.db
    return {
        "host": db_settings.server,
        "port": int(db_settings.port),
        "user": db_settings.user,
        "password": db_settings.raw_password,
        "dbname": dbname,
    }


def get_readonly_db_credentials() -> Optional[Dict[str, Any]]:
    """Return readonly DB credentials, or ``None`` if not configured.

    Falls back to primary fields where readonly-specific values are absent.
    """
    db_settings = CONFIG.database
    if not db_settings.readonly_server:
        return None
    return {
        "host": db_settings.readonly_server,
        "port": int(db_settings.readonly_port or db_settings.port),
        "user": db_settings.readonly_user or db_settings.user,
        "password": db_settings.raw_readonly_password or db_settings.raw_password,
        "dbname": db_settings.readonly_db or db_settings.db,
    }


# ---------------------------------------------------------------------------
# Sync creators (psycopg2)
# ---------------------------------------------------------------------------


def make_sync_creator(
    connect_args: Optional[Dict[str, Any]] = None,
    readonly: bool = False,
) -> Callable[[], Any]:
    """Return a creator callable for psycopg2 engines.

    The factory captures per-engine config (keepalives, SSL) in the closure.
    Credentials are resolved from CONFIG on every call — the seam for future
    dynamic credential rotation.

    When using ``creator``, SQLAlchemy ignores ``connect_args`` passed to
    ``create_engine``, so all connection parameters must be baked in here.
    """

    def creator() -> Any:
        if readonly:
            kw = get_readonly_db_credentials() or get_db_credentials()
        else:
            kw = get_db_credentials()
        if connect_args:
            kw.update(connect_args)
        return psycopg2.connect(**kw)

    return creator


# ---------------------------------------------------------------------------
# Async creators (asyncpg)
# ---------------------------------------------------------------------------


def make_async_creator(
    readonly: bool = False,
) -> Callable[[], Any]:
    """Return a creator callable for asyncpg engines (SA 1.4.27).

    The factory builds the SSL context and asyncpg-compatible params from
    CONFIG, capturing them in the closure.  Credentials are resolved from
    CONFIG on every call.

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

    def creator() -> Any:
        if readonly:
            creds = get_readonly_db_credentials() or get_db_credentials()
        else:
            creds = get_db_credentials()
        kw: Dict[str, Any] = {
            "host": creds["host"],
            "port": creds["port"],
            "user": creds["user"],
            "password": creds["password"],
            "database": creds["dbname"],
        }
        if ssl_context:
            kw["ssl"] = ssl_context
        if async_params:
            kw.update(async_params)
        raw_conn = await_only(asyncpg.connect(**kw))
        return AsyncAdapt_asyncpg_connection(_asyncpg_dbapi, raw_conn)

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

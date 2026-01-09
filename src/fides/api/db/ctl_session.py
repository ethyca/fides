import ssl
from typing import Any, AsyncGenerator, Callable, Dict
from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from asyncio import current_task
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine
)

from fides.api.db.session import ExtendedSession
from fides.api.db.util import custom_json_deserializer, custom_json_serializer
from fides.config import CONFIG

# Import tracing utilities - safe to import even if OpenTelemetry is not installed
try:
    from fides.telemetry.tracing import instrument_sqlalchemy
except ImportError:
    instrument_sqlalchemy = None  # type: ignore

# Associated with a workaround in fides.core.config.database_settings
# ref: https://github.com/sqlalchemy/sqlalchemy/discussions/5975
connect_args: Dict[str, Any] = {}
if CONFIG.database.params.get("sslrootcert"):
    ssl_ctx = ssl.create_default_context(cafile=CONFIG.database.params["sslrootcert"])
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    connect_args["ssl"] = ssl_ctx

if CONFIG.database.api_engine_disable_pool:
    print("POOL DISABLED FOR ASYNC ENGINE")
    # Parameters are hidden for security
    from sqlalchemy.pool import NullPool
    async_engine = create_async_engine(
        CONFIG.database.async_database_uri,
        connect_args=connect_args,
        echo=False,
        hide_parameters=not CONFIG.dev_mode,
        logging_name="AsyncEngine",
        json_serializer=custom_json_serializer,
        json_deserializer=custom_json_deserializer,
        poolclass=NullPool
    )
else:
    # Parameters are hidden for security
    async_engine = create_async_engine(
        CONFIG.database.async_database_uri,
        connect_args=connect_args,
        echo=False,
        hide_parameters=not CONFIG.dev_mode,
        logging_name="AsyncEngine",
        json_serializer=custom_json_serializer,
        json_deserializer=custom_json_deserializer,
        pool_size=CONFIG.database.api_async_engine_pool_size,
        max_overflow=CONFIG.database.api_async_engine_max_overflow,
        pool_pre_ping=CONFIG.database.api_async_engine_pool_pre_ping,
    )

    # pool_size=CONFIG.database.api_async_engine_pool_size
    # print(f"Warming up ASYNC connection pool with {pool_size} connections...")
    # connections = []
    # try:
    #     # Check out connections
    #     for _ in range(pool_size):
    #         conn = async_engine.connect()
    #         connections.append(conn)
    #         # Optional: run a simple, lightweight query to ensure the connection is truly live
    #         conn.execute(text("SELECT 1"))
    #         import time
    #         print("Sleeping 10s to allow async connections to complete")
    #         time.sleep(10)
    #     print(f"Pool warmed up. Releasing connections...")
    # except Exception as e:
    #     print(f"An error occurred during warming: {e}")
    # finally:
    #     # Release all connections back to the pool
    #     for conn in connections:
    #         conn.close()
    #     print("Connections released back to the pool.")




local_async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Read-only async engine and session
# Only created if read-only database URI is configured
readonly_async_engine: Any = None
readonly_async_session: Callable[[], AsyncSession]

# Initialize readonly_async_session (will be overridden if readonly DB is configured)
local_readonly_async_session = local_async_session

if CONFIG.database.async_readonly_database_uri:
    # Build connect_args for readonly (similar to primary)
    readonly_connect_args: Dict[str, Any] = {}
    readonly_params = CONFIG.database.readonly_params or {}

    if readonly_params.get("sslrootcert"):
        ssl_ctx = ssl.create_default_context(cafile=readonly_params["sslrootcert"])
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        readonly_connect_args["ssl"] = ssl_ctx

    readonly_async_engine = create_async_engine(
        CONFIG.database.async_readonly_database_uri,
        connect_args=readonly_connect_args,
        echo=False,
        hide_parameters=not CONFIG.dev_mode,
        logging_name="ReadOnlyAsyncEngine",
        json_serializer=custom_json_serializer,
        json_deserializer=custom_json_deserializer,
        pool_size=CONFIG.database.api_async_engine_pool_size,
        max_overflow=CONFIG.database.api_async_engine_max_overflow,
        pool_pre_ping=CONFIG.database.api_async_engine_pool_pre_ping,
    )
    readonly_async_session = sessionmaker(
        readonly_async_engine, class_=AsyncSession, expire_on_commit=False
    )

# TODO: this engine and session are only used in test modules,
# and they do not respect engine settings like pool_size, max_overflow, etc.
# these should be removed, and we should standardize on what's provided in `session.py`
sync_engine = create_engine(
    CONFIG.database.sync_database_uri,
    echo=False,
    hide_parameters=not CONFIG.dev_mode,
    logging_name="SyncEngine",
    json_serializer=custom_json_serializer,
    json_deserializer=custom_json_deserializer,
)
sync_session = sessionmaker(
    sync_engine,
    class_=ExtendedSession,
    expire_on_commit=False,
    autocommit=False,
)

# Instrument the sync engine with OpenTelemetry tracing if available and enabled
if instrument_sqlalchemy:
    instrument_sqlalchemy(sync_engine, CONFIG, {"engine": "sync_engine"})

    instrument_sqlalchemy(async_engine, CONFIG, {"engine": "async_engine"})

from sqlalchemy.orm import scoped_session

scoped_async_session = async_scoped_session(local_async_session, scopefunc=current_task)
scoped_readonly_async_session = async_scoped_session(local_readonly_async_session, scopefunc=current_task)

import threading

POOL_WARMED = False
POOL_LOCK = threading.Lock()

async def warm_pool():
    pool_size=CONFIG.database.api_async_engine_pool_size
    print(f"Warming up ASYNC connection pool with {pool_size} connections...")
    connections = []
    try:
        # Check out connections
        for _ in range(pool_size):
            conn = await async_engine.connect()
            connections.append(conn)
        print(f"Pool warmed up. Releasing connections...")
    except Exception as e:
        print(f"An error occurred during warming: {e}")
    finally:
        # Release all connections back to the pool
        for conn in connections:
            await conn.close()
        print("Connections released back to the pool.")

@asynccontextmanager
async def async_session() -> AsyncSession:
    with POOL_LOCK:
        global POOL_WARMED
        if not POOL_WARMED:
            await warm_pool()
            POOL_WARMED = True

    """Provide a session context manager."""
    session = scoped_async_session()
    print(async_engine.pool.status())
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        # Crucially, remove the session from the registry when the request/task is done
        await session.close()
        scoped_async_session.remove()

@asynccontextmanager
async def readonly_async_session() -> AsyncSession:
    session = scoped_readonly_async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        # Crucially, remove the session from the registry when the request/task is done
        await session.close()
        scoped_readonly_async_session.remove()


async def get_async_db() -> AsyncGenerator:
    """Return an async session generator for dependency injection into API endpoints"""
    async with async_session() as session:
        yield session

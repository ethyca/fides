import ssl
from asyncio import Lock
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Dict

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import sessionmaker

from fides.api.db.session import ExtendedSession
from fides.api.db.util import custom_json_deserializer, custom_json_serializer
from fides.config import CONFIG

# asyncio lock and flag for warming up the async pool
ASYNC_READONLY_POOL_LOCK = Lock()
ASYNC_READONLY_POOL_WARMED = False

# Associated with a workaround in fides.core.config.database_settings
# ref: https://github.com/sqlalchemy/sqlalchemy/discussions/5975
connect_args: Dict[str, Any] = {}
if CONFIG.database.params.get("sslrootcert"):
    ssl_ctx = ssl.create_default_context(cafile=CONFIG.database.params["sslrootcert"])
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    connect_args["ssl"] = ssl_ctx

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
async_session_factory = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Read-only async engine and session factory
# Only created if read-only database URI is configured (otherwise defaults to the async session factory)
readonly_async_engine: Any = None
readonly_async_session_factory: Callable[[], AsyncSession] = async_session_factory

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
        pool_size=CONFIG.database.async_readonly_database_pool_size,
        max_overflow=CONFIG.database.async_readonly_database_max_overflow,
        pool_pre_ping=CONFIG.database.async_readonly_database_pre_ping,
        # Don't rollback before returning a connection to the pool - this improves performance dramatically;
        # can be turned off via config but the default is to not reset on return
        pool_reset_on_return=(
            None
            if CONFIG.database.async_readonly_database_pool_skip_rollback
            else "rollback"
        ),
        # Autocommit transactions (this should effectively be a no-op because it's a readonly database)
        isolation_level=(
            "AUTOCOMMIT" if CONFIG.database.async_readonly_database_autocommit else None
        ),
    )
    readonly_async_session_factory = sessionmaker(
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


# This will delay the first connection until the pool is warmed up
# TODO: Defer marking the service as healthy until this finishes if it's enabled
@asynccontextmanager
async def prewarmed_async_readonly_session() -> AsyncGenerator[Any, Any]:
    async with ASYNC_READONLY_POOL_LOCK:
        global ASYNC_READONLY_POOL_WARMED
        if not ASYNC_READONLY_POOL_WARMED:
            await warm_async_pool(
                "readonly-async-pool",
                CONFIG.database.async_readonly_database_pool_size,
                readonly_async_engine,
            )
            ASYNC_READONLY_POOL_WARMED = True

        session = readonly_async_session_factory()

    try:
        yield session
        # If we aren't using autocommit, commit the transaction
        # TODO: Do we even want to do this? It's harmless on read-only queries but somewhat meaningless
        if not CONFIG.database.async_readonly_database_autocommit:
            await session.commit()
    except Exception:
        # If something went wrong, rollback the transaction for safety
        if not CONFIG.database.async_readonly_database_pool_skip_rollback:
            await session.rollback()
        raise
    finally:
        await session.close()


# If warm-up is disabled, use non-warmed session factory
@asynccontextmanager
async def non_warmed_async_readonly_session() -> AsyncGenerator[Any, Any]:
    session = readonly_async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# If the prewarm flag is enabled, use the prewarmed session factory, otherwise use the non-warmed one
readonly_async_session: Callable[[], _AsyncGeneratorContextManager[Any]] = (
    prewarmed_async_readonly_session
    if CONFIG.database.async_readonly_database_prewarm
    else non_warmed_async_readonly_session
)

# This is here for consistency with the readonly pattern and for a future behavior change
async_session: Callable[[], AsyncSession] = async_session_factory


# engine is actually an AsyncEngine but apparently the async proxy doesn't properly export connect
# as async so the type checking complains below in await engine.connect()
async def warm_async_pool(pool_id: str, pool_size: int, engine: AsyncEngine) -> None:
    logger.info(f"Warming up {pool_id} connection pool with {pool_size} connections...")
    connections = []
    try:
        # Check out connections
        for _ in range(pool_size):
            # This is actually async, even though the type checker may not think so
            conn = await engine.connect()
            connections.append(conn)
        logger.info(f"Pool {pool_id} warmed up. Releasing connections...")
    except Exception as e:
        logger.error(f"An error occurred during warming of {pool_id}: {e}")
    finally:
        # Release all connections back to the pool
        for conn in connections:
            await conn.close()
        logger.info(f"Connections released back to the pool for {pool_id}.")


async def get_async_db() -> AsyncGenerator:
    """Return an async session generator for dependency injection into API endpoints"""
    async with async_session() as session:
        yield session

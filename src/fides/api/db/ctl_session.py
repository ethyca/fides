import ssl
from typing import Any, AsyncGenerator, Dict

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fides.api.db.session import ExtendedSession
from fides.api.db.util import custom_json_deserializer, custom_json_serializer
from fides.config import CONFIG

# Associated with a workaround in fides.core.config.database_settings
# ref: https://github.com/sqlalchemy/sqlalchemy/discussions/5975
connect_args: Dict[str, Any] = {}
if CONFIG.database.params.get("sslrootcert"):
    ssl_ctx = ssl.create_default_context(cafile=CONFIG.database.params["sslrootcert"])
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    connect_args["ssl"] = ssl_ctx

if CONFIG.database.api_async_engine_keepalives_idle:
    connect_args["keepalives_idle"] = CONFIG.database.api_async_engine_keepalives_idle
if CONFIG.database.api_async_engine_keepalives_interval:
    connect_args["keepalives_interval"] = (
        CONFIG.database.api_async_engine_keepalives_interval
    )
if CONFIG.database.api_async_engine_keepalives_count:
    connect_args["keepalives_count"] = CONFIG.database.api_async_engine_keepalives_count

# Parameters are hidden for security
async_engine = create_async_engine(
    CONFIG.database.async_database_uri,
    connect_args=connect_args,
    echo=False,
    hide_parameters=not CONFIG.dev_mode,
    logging_name="AsyncEngine",
    json_serializer=custom_json_serializer,
    json_deserializer=custom_json_deserializer,
    pool_pre_ping=CONFIG.database.api_async_engine_pool_pre_ping,
)
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

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


async def get_async_db() -> AsyncGenerator:
    """Return an async session generator for dependency injection into API endpoints"""
    async with async_session() as session:
        yield session

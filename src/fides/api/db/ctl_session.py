import ssl
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fides.api.db.session import ExtendedSession
from fides.api.db.util import custom_json_deserializer, custom_json_serializer
from fides.config import CONFIG

# Associated with a workaround in fides.core.config.database_settings
# ref: https://github.com/sqlalchemy/sqlalchemy/discussions/5975
connect_args = {}
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
)
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

readonly_async_engine = (
    create_async_engine(
        CONFIG.database.readonly_async_database_uri,
        connect_args=connect_args,
        echo=False,
        hide_parameters=not CONFIG.dev_mode,
        logging_name="AsyncEngine",
        json_serializer=custom_json_serializer,
        json_deserializer=custom_json_deserializer,
    )
    if CONFIG.database.readonly_async_database_uri
    else None
)
readonly_async_session = (
    sessionmaker(readonly_async_engine, class_=AsyncSession, expire_on_commit=False)
    if CONFIG.database.readonly_async_database_uri
    else None
)

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


async def get_readonly_async_db() -> AsyncGenerator:
    """Return an async session generator for dependency injection into API endpoints"""
    if readonly_async_session:
        async with readonly_async_session() as session:
            yield session

    yield get_async_db()

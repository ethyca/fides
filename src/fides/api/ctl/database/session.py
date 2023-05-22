from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fides.api.db.session import ExtendedSession
from fides.core.config import CONFIG

# Parameters are hidden for security
engine = create_async_engine(
    CONFIG.database.async_database_uri,
    echo=False,
    hide_parameters=not CONFIG.dev_mode,
    logging_name="AsyncEngine",
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = create_engine(
    CONFIG.database.sync_database_uri,
    echo=False,
    hide_parameters=not CONFIG.dev_mode,
    logging_name="SyncEngine",
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

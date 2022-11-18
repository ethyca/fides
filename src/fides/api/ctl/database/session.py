from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fides.ctl.core.config import get_config

config = get_config()

_async_engine = None


async def get_async_db() -> AsyncGenerator:
    """Return an async session generator for dependency injection into API endpoints"""
    async_session = get_async_sessionmaker()
    async with async_session() as session:
        yield session


async def get_async_session() -> AsyncSession:
    """Gets an async session on the shared engine to use for API functionality"""
    return get_async_sessionmaker()()


def get_async_sessionmaker() -> sessionmaker:
    """Creates an async sessionmaker"""
    global _async_engine  # pylint: disable=W0603
    if not _async_engine:
        _async_engine = create_async_engine(
            config.database.async_database_uri,
            echo=False,
        )
    return sessionmaker(_async_engine, class_=AsyncSession, expire_on_commit=False)

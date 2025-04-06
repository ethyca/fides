from contextlib import contextmanager
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from fides.api.common_exceptions import RedisNotConfigured
from fides.api.db.session import get_db_engine, get_db_session
from fides.api.util.cache import get_cache as get_redis_connection
from fides.config import CONFIG, FidesConfig
from fides.config import get_config as get_app_config
from fides.config.config_proxy import ConfigProxy

_engine = None


def get_config() -> FidesConfig:
    """Returns the config for use in dependency injection."""
    return get_app_config()


def get_db() -> Generator:
    """Return our database session"""
    try:
        db = get_api_session()
        yield db
    finally:
        db.close()


@contextmanager
def get_autoclose_db_session() -> Generator[Session, None, None]:
    """
    Return a database session as a context manager that automatically closes when the context exits.

    Unlike get_api_session which is managed by FastAPI's dependency injection,
    this context manager explicitly closes the session when exiting the context.
    Use this when you need manual control over the session lifecycle outside of API endpoints.
    """
    try:
        db = get_api_session()
        yield db
    finally:
        db.close()


def get_api_session() -> Session:
    """Gets the shared database session to use for API functionality"""
    global _engine  # pylint: disable=W0603
    if not _engine:
        _engine = get_db_engine(
            config=CONFIG,
            pool_size=CONFIG.database.api_engine_pool_size,
            max_overflow=CONFIG.database.api_engine_max_overflow,
            keepalives_idle=CONFIG.database.api_engine_keepalives_idle,
            keepalives_interval=CONFIG.database.api_engine_keepalives_interval,
            keepalives_count=CONFIG.database.api_engine_keepalives_count,
        )
    SessionLocal = get_db_session(CONFIG, engine=_engine)
    db = SessionLocal()
    return db


def get_config_proxy(db: Session = Depends(get_db)) -> ConfigProxy:
    return ConfigProxy(db)


def get_cache() -> Generator:
    """Return a connection to our Redis cache"""
    if not CONFIG.redis.enabled:
        raise RedisNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a Redis cache."
        )
    yield get_redis_connection()

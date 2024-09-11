from contextlib import contextmanager
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FunctionalityNotConfigured
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
def get_db_contextmanager() -> Generator[Session, None, None]:
    """Return our database session as a context manager"""
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
        )
    SessionLocal = get_db_session(CONFIG, engine=_engine)
    db = SessionLocal()
    return db


def get_config_proxy(db: Session = Depends(get_db)) -> ConfigProxy:
    return ConfigProxy(db)


def get_cache() -> Generator:
    """Return a connection to our redis cache"""
    if not CONFIG.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )
    yield get_redis_connection()

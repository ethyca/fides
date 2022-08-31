from typing import Generator

from fideslib.db.session import get_db_engine, get_db_session
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import FunctionalityNotConfigured
from fides.ctl.core.config import FidesConfig, get_config as get_app_config
from fides.api.ops.util.cache import get_cache as get_redis_connection

_engine = None
CONFIG = get_app_config()


def get_config() -> FidesConfig:
    """Returns the config for use in dependency injection."""
    return get_app_config()


def get_db() -> Generator:
    """Return our database session"""
    if not CONFIG.database.enabled:
        raise FunctionalityNotConfigured(
            "Application database required, but it is currently disabled! Please update your application configuration to enable integration with an application database."
        )

    try:
        db = _get_session()
        yield db
    finally:
        db.close()


def get_db_for_health_check() -> Generator:
    """Gets a database session regardless of whether the application db is disabled, for a health check."""
    try:
        db = _get_session()
        yield db
    finally:
        db.close()


def _get_session() -> Session:
    """Gets a database session"""
    global _engine  # pylint: disable=W0603
    if not _engine:
        _engine = get_db_engine(config=CONFIG)
    SessionLocal = get_db_session(CONFIG, engine=_engine)
    db = SessionLocal()
    return db


def get_cache() -> Generator:
    """Return a connection to our redis cache"""
    if not CONFIG.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )
    yield get_redis_connection()

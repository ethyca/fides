from typing import Generator

from fidesops.common_exceptions import FunctionalityNotConfigured
from fidesops.core.config import config
from fidesops.db.session import get_db_session
from fidesops.util.cache import get_cache as get_redis_connection


def get_db() -> Generator:
    """Return our database session"""
    if not config.database.ENABLED:
        raise FunctionalityNotConfigured(
            "Application database required, but it is currently disabled! Please update your application configuration to enable integration with an application database."
        )
    try:
        SessionLocal = get_db_session()
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_cache() -> Generator:
    """Return a connection to our redis cache"""
    if not config.redis.ENABLED:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )
    yield get_redis_connection()

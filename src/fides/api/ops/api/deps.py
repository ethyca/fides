from typing import Generator

from fideslib.db.session import get_db_engine, get_db_session
from sqlalchemy.orm import Session

<<<<<<< HEAD:src/fides/api/ops/api/deps.py
from fides.api.ops.common_exceptions import FunctionalityNotConfigured
from fides.api.ops.core.config import config
from fides.api.ops.util.cache import get_cache as get_redis_connection
=======
from fidesops.ops.common_exceptions import FunctionalityNotConfigured
from fidesops.ops.core.config import FidesopsConfig, config
from fidesops.ops.util.cache import get_cache as get_redis_connection
>>>>>>> fidesops/main:src/fidesops/ops/api/deps.py

_engine = None


def get_config() -> FidesopsConfig:
    """Returns the config for use in dependency injection."""
    return config


def get_db() -> Generator:
    """Return our database session"""
    if not config.database.enabled:
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
        _engine = get_db_engine(config=config)
    SessionLocal = get_db_session(config, engine=_engine)
    db = SessionLocal()
    return db


def get_cache() -> Generator:
    """Return a connection to our redis cache"""
    if not config.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )
    yield get_redis_connection()

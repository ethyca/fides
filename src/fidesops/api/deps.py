from typing import Generator

from fidesops.db.session import get_db_session
from fidesops.util.cache import get_cache as get_redis_connection


def get_db() -> Generator:
    """Return our database session"""
    try:
        SessionLocal = get_db_session()
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_cache() -> Generator:
    """Return a connection to our redis cache"""
    yield get_redis_connection()

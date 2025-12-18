from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from fides.api.common_exceptions import MissingConfig
from fides.api.db.util import custom_json_deserializer, custom_json_serializer
from fides.config import FidesConfig


def get_db_engine(
    *,
    config: FidesConfig | None = None,
    database_uri: str | URL | None = None,
    pool_size: int = 50,
    max_overflow: int = 50,
    keepalives_idle: int | None = None,
    keepalives_interval: int | None = None,
    keepalives_count: int | None = None,
    pool_pre_ping: bool = True,
    disable_pooling: bool = False,
) -> Engine:
    """Return a database engine.

    If the TESTING environment var is set the database engine returned will be
    connected to the test DB.
    """
    if not config and not database_uri:
        raise ValueError("Either a config or database_uri is required")

    if not database_uri and config:
        # Don't override any database_uri explicitly passed in
        if config.test_mode:
            database_uri = config.database.sqlalchemy_test_database_uri
        else:
            database_uri = config.database.sqlalchemy_database_uri

    engine_args: Dict[str, Any] = {
        "json_serializer": custom_json_serializer,
        "json_deserializer": custom_json_deserializer,
    }

    # keepalives settings
    connect_args = {}
    if keepalives_idle:
        connect_args["keepalives_idle"] = keepalives_idle
    if keepalives_interval:
        connect_args["keepalives_interval"] = keepalives_interval
    if keepalives_count:
        connect_args["keepalives_count"] = keepalives_count

    if connect_args:
        connect_args["keepalives"] = 1
        engine_args["connect_args"] = connect_args

    if disable_pooling:
        engine_args["poolclass"] = NullPool
    else:
        engine_args["pool_pre_ping"] = pool_pre_ping
        engine_args["pool_size"] = pool_size
        engine_args["max_overflow"] = max_overflow

    return create_engine(database_uri, **engine_args)


def get_db_session(
    config: FidesConfig,
    autocommit: bool = False,
    autoflush: bool = False,
    engine: Engine | None = None,
) -> sessionmaker:
    """Return a database SessionLocal."""
    if not config.database.sqlalchemy_database_uri:
        raise MissingConfig("No database uri available in the config")

    return sessionmaker(
        autocommit=autocommit,
        autoflush=autoflush,
        bind=engine or get_db_engine(config=config),
        class_=ExtendedSession,
    )


class ExtendedSession(Session):
    """This class wraps the SQLAlchemy Session to provide some error handling on
    commits."""

    def commit(self) -> None:
        """Provide the option to automatically rollback failed transactions."""
        try:
            return super().commit()
        except Exception as exc:
            logger.error("Exception: {}", exc)
            # Rollback the current transaction after each failed commit
            self.rollback()
            raise


def get_engine_pool_stats(engine: Optional[Engine]) -> Optional[Dict[str, Any]]:
    """
    Extract connection pool statistics from a SQLAlchemy engine.

    Args:
        engine: SQLAlchemy Engine object to inspect

    Returns:
        Dictionary containing pool statistics:
        - pool_size: configured pool_size (max permanent connections)
        - max_overflow: configured max_overflow (max temporary connections)
        - num_checked_out: connections currently in use
        - num_in_pool: connections currently available in the pool
        - overflow_count: overflow connections currently in use (beyond pool_size)
        - total_connections: total connections that exist (in_pool + checked_out)
        Returns None if engine is None or doesn't have a pool.
    """
    if engine is None:
        return None

    try:
        pool = engine.pool
        # NullPool doesn't have meaningful stats
        if isinstance(pool, NullPool):
            return {"type": "NullPool", "pooling_disabled": True}

        # Access pool statistics through public and internal attributes
        # These are available on QueuePool (the default pool implementation)
        checked_out = pool.checkedout()

        # Get the actual number of connections in the pool (available for checkout)
        # This is tracked in _pool which is a queue
        num_in_pool = 0
        if hasattr(pool, "_pool"):
            num_in_pool = pool._pool.qsize()

        # Calculate overflow: connections created beyond pool_size
        # This is tracked in _overflow which can be negative during initialization
        overflow_count = 0
        if hasattr(pool, "_overflow"):
            overflow_count = max(0, pool._overflow)

        # Total connections = in pool + checked out
        total_connections = num_in_pool + checked_out

        stats = {
            "pool_size": pool.size(),
            "max_overflow": pool._max_overflow if hasattr(pool, "_max_overflow") else 0,
            "num_checked_out": checked_out,
            "num_in_pool": num_in_pool,
            "overflow_count": overflow_count,
            "total_connections": total_connections,
        }

        return stats
    except Exception as exc:
        logger.debug("Failed to get pool stats: {}", exc)
        return None

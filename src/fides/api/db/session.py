from __future__ import annotations

from typing import Any, Dict

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from fides.api.common_exceptions import MissingConfig
from fides.api.db.util import custom_json_deserializer, custom_json_serializer
from fides.config import FidesConfig

# Import tracing utilities - safe to import even if OpenTelemetry is not installed
try:
    from fides.telemetry.tracing import instrument_sqlalchemy
except ImportError:
    instrument_sqlalchemy = None  # type: ignore


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

    engine = create_engine(database_uri, **engine_args)

    # Instrument SQLAlchemy engine with OpenTelemetry tracing if available and enabled
    if instrument_sqlalchemy and config:
        logger.info("Instrumenting SQLAlchemy engine with OpenTelemetry tracing")
        instrument_sqlalchemy(engine, config)

    # """
    # Checks out and immediately closes connections to warm the pool.
    # """
    # print(f"Warming up connection pool with {pool_size} connections...")
    # connections = []
    # try:
    #     # Check out connections
    #     for _ in range(pool_size):
    #         conn = engine.connect()
    #         connections.append(conn)
    #         # Optional: run a simple, lightweight query to ensure the connection is truly live
    #         # conn.execute(text("SELECT 1"))
    #     print(f"Pool warmed up. Releasing connections...")
    # except Exception as e:
    #     print(f"An error occurred during warming: {e}")
    # finally:
    #     # Release all connections back to the pool
    #     for conn in connections:
    #         conn.close()
    #     print("Connections released back to the pool.")

    return engine


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

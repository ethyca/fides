from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from fides.api.common_exceptions import MissingConfig
from fides.api.db.util import custom_json_deserializer, custom_json_serializer
from fides.common.engine_creators import SYNC_DIALECT_URL, make_sync_creator
from fides.config import FidesConfig


def get_db_engine(
    *,
    config: FidesConfig | None = None,
    database_uri: str | URL | None = None,
    creator: Callable[[], Any] | None = None,
    pool_size: int = 50,
    max_overflow: int = 50,
    keepalives_idle: int | None = None,
    keepalives_interval: int | None = None,
    keepalives_count: int | None = None,
    pool_pre_ping: bool = True,
    pool_recycle: Optional[int] = None,
    disable_pooling: bool = False,
) -> Engine:
    """Return a database engine.

    When *creator* is provided, it is called by the pool to open each new
    connection — credentials and connect_args are handled inside the creator.
    A dialect-only URL is used for engine construction.

    When *database_uri* or *config* is provided, the engine uses a fixed
    connection URI (existing behavior).

    If the TESTING environment var is set the database engine returned will be
    connected to the test DB.
    """
    engine_args: Dict[str, Any] = {
        "json_serializer": custom_json_serializer,
        "json_deserializer": custom_json_deserializer,
    }

    if creator:
        # Creator handles credentials and connect_args internally,
        # so creator needs to set keepalives settings.
        if database_uri or config:
            raise ValueError(
                "database_uri/config cannot be used with creator — "
                "the creator handles connection construction"
            )
        if keepalives_idle or keepalives_interval or keepalives_count:
            raise ValueError(
                "keepalives_idle/interval/count cannot be used with creator — "
                "pass them as connect_args to the creator instead"
            )
        engine_args["creator"] = creator
        database_uri = SYNC_DIALECT_URL
    else:
        # URI-based path.
        if not config and not database_uri:
            raise ValueError("Either a config, database_uri, or creator is required")

        if not database_uri and config:
            if config.test_mode:
                database_uri = config.database.sqlalchemy_test_database_uri
            else:
                database_uri = config.database.sqlalchemy_database_uri

        # keepalives settings (only for URI path; creator handles its own)
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
        if pool_recycle is not None:
            engine_args["pool_recycle"] = pool_recycle

    return create_engine(database_uri, **engine_args)


def get_db_session(
    config: FidesConfig,  # TODO: remove — no longer used, all callers pass CONFIG
    autocommit: bool = False,
    autoflush: bool = False,
    engine: Engine | None = None,
) -> sessionmaker:
    """Return a database SessionLocal."""
    if engine is None:
        engine = get_db_engine(creator=make_sync_creator())

    return sessionmaker(
        autocommit=autocommit,
        autoflush=autoflush,
        bind=engine,
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

from __future__ import annotations

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import Session, sessionmaker

from fides.api.common_exceptions import MissingConfig
from fides.api.db.util import custom_json_deserializer, custom_json_serializer
from fides.config import FidesConfig


def get_db_engine(
    *,
    config: FidesConfig | None = None,
    database_uri: str | URL | None = None,
    pool_size: int = 50,
    max_overflow: int = 50,
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
    return create_engine(
        database_uri,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        json_serializer=custom_json_serializer,
        json_deserializer=custom_json_deserializer,
    )


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

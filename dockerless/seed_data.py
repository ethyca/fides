#!/usr/bin/env python
"""Seed the local Fides database with default resources."""

from __future__ import annotations

from contextlib import contextmanager

from fides.api.db.database import configure_db, seed_db
from fides.api.db.session import get_db_session
from fides.config import get_config


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    config = get_config()
    configure_db(config.database.sqlalchemy_database_uri)
    SessionLocal = get_db_session(config=config)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    with session_scope() as session:
        seed_db(session)


if __name__ == "__main__":
    main()

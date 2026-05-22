"""Shared fixtures for tests/service/ — provides a lightweight `db` fixture
that connects to the running fidesplus-db Postgres instance and rolls back
each test so tests remain isolated.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_DB_URL = "postgresql://postgres:fides@fidesplus-db:5432/fides"


@pytest.fixture()
def db():
    """Yield a SQLAlchemy Session, rolling back after each test."""
    engine = create_engine(_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()

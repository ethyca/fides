"""Fixtures for the event framework tests.

Provides:
- ``session`` — a lightweight in-memory SQLAlchemy session used to drive
  ``after_commit`` / ``after_rollback`` events. Doesn't need any tables.
- ``ping_received`` — a per-test reset of the ping capture list.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Importing _ping here ensures the ping subscriber is registered before any
# test in this directory runs.
from . import _ping  # noqa: F401


@pytest.fixture
def session() -> Session:
    """A real SQLAlchemy session backed by in-memory SQLite.

    No tables are created — the event framework only needs the session's
    transaction lifecycle hooks (``after_commit`` / ``after_rollback``).
    """
    engine = create_engine("sqlite:///:memory:")
    factory = sessionmaker(bind=engine)
    s = factory()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def ping_received() -> list:
    """Yield the ping capture list, clearing it before and after each test."""
    _ping._PING_RECEIVED.clear()
    yield _ping._PING_RECEIVED
    _ping._PING_RECEIVED.clear()

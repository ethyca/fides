"""
Standardized Database Fixtures
==============================

This module provides a unified set of fixtures for database testing.
It standardizes how database connections are created, reset, and loaded with data,
ensuring consistent behavior across all tests.
"""

import pytest
import requests
from fideslang import DEFAULT_TAXONOMY
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.db.base_class import Base
from fides.api.db.ctl_session import sync_engine, sync_session
from fides.api.db.session import get_db_engine, get_db_session
from fides.api.models.sql_models import DataCategory, DataUse
from fides.api.tasks.scheduled.scheduler import async_scheduler, scheduler
from fides.config import CONFIG

# Core database management functions


def create_citext_extension(engine):
    """Create the CITEXT extension if it doesn't exist."""
    # Use a raw connection with autocommit
    # This avoids transaction issues with CREATE EXTENSION
    with engine.connect() as conn:
        # We run this for local testing. In CI, citext is included and this fails
        # as an "already exists" error
        try:
            conn.execute("CREATE EXTENSION IF NOT EXISTS citext")
            # Explicitly commit the statement
            try:
                conn.commit()
            except AttributeError:
                # Some SQLAlchemy connections don't have commit,
                # for older versions where commit is implicit or for newer engines
                pass
        except Exception:
            # Extension already exists or cannot be created (likely CI)
            # No need to rollback here - just continue
            pass


def _get_db_engine(config):
    """Create a database engine with the proper configuration."""
    engine = get_db_engine(
        database_uri=config.database.sqlalchemy_test_database_uri,
    )
    create_citext_extension(engine)
    return engine


def _ensure_schedulers_running():
    """Ensure that scheduler services are running."""
    if not scheduler.running:
        scheduler.start()
    if not async_scheduler.running:
        async_scheduler.start()


def _reset_database(db):
    """Reset the database by clearing all tables in the correct order."""
    # Skip these tables when clearing
    SKIP_TABLES = ["ctl_data_categories", "migrations_history"]

    def delete_data(tables):
        redo = []
        for table in tables:
            if table.name in SKIP_TABLES:
                continue
            try:
                db.execute(table.delete())
            except IntegrityError:
                redo.append(table)
            finally:
                db.commit()
        if redo:
            delete_data(redo)

    db.commit()  # make sure all transactions are closed
    delete_data(Base.metadata.sorted_tables)


def _load_default_taxonomy(db):
    """Load default taxonomy data into the database."""
    # Load data categories
    categories = []
    for obj in DEFAULT_TAXONOMY.data_category:
        try:
            if DataCategory.get_by(db, field="name", value=obj.name) is None:
                categories.append(DataCategory.from_fideslang_obj(obj).save(db))
        except IntegrityError:
            pass

    # Load data uses
    for data_use in DEFAULT_TAXONOMY.data_use:
        try:
            if DataUse.get_by(db, field="name", value=data_use.name) is None:
                DataUse.create(db=db, data=data_use.model_dump(mode="json"))
        except IntegrityError:
            pass

    # Could add more taxonomy elements here

    db.commit()
    return categories


# Standard database fixtures


@pytest.fixture(scope="session")
def fideslang_data_categories():
    """
    Fixture that provides access to the default taxonomy data categories.
    This is kept for backward compatibility with existing tests.
    """
    return DEFAULT_TAXONOMY.data_category


@pytest.fixture(scope="session")
def db(api_client, config):
    """
    Standard session-scoped database fixture.
    This provides one database session for the entire test suite.
    """
    assert config.test_mode
    assert requests.post != api_client.post
    engine = _get_db_engine(config)
    _ensure_schedulers_running()

    SessionLocal = get_db_session(config, engine=engine)
    session = SessionLocal()

    # Load default taxonomy data
    _load_default_taxonomy(session)

    yield session

    session.close()
    engine.dispose()


@pytest.fixture(autouse=True, scope="function")
def reset_db_after_test(db):
    """
    Reset the database after each test.
    This fixture automatically runs after every test.
    """
    # Allow the test to run
    yield

    # Reset the database
    _reset_database(db)

    # Reload basic data needed for all tests
    _load_default_taxonomy(db)


@pytest.fixture(scope="session")
async def async_session(test_client):
    """
    Session-scoped async database fixture.
    This provides one async session for async tests.
    """
    assert CONFIG.test_mode
    assert requests.post == test_client.post

    create_citext_extension(sync_engine)
    _ensure_schedulers_running()

    async_engine = create_async_engine(
        CONFIG.database.async_database_uri,
        echo=False,
    )

    session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        yield session
        session.close()
        async_engine.dispose()


@pytest.fixture(scope="function")
async def async_session_temp(test_client):
    """
    Function-scoped async database fixture.
    This provides a fresh async session for each test.
    """
    assert CONFIG.test_mode

    create_citext_extension(sync_engine)

    async_engine = create_async_engine(
        CONFIG.database.async_database_uri,
        echo=False,
    )

    session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        yield session
        session.close()
        async_engine.dispose()


@pytest.fixture(scope="session")
def ctl_db():
    """
    CTL-specific database fixture.
    This is kept for backward compatibility but uses the same reset approach.
    """
    create_citext_extension(sync_engine)
    session = sync_session()

    # Load default taxonomy data
    _load_default_taxonomy(session)

    yield session

    session.close()

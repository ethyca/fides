import logging
from typing import Generator

import pytest
from sqlalchemy import func, select, table

from fidesops.db.session import get_db_session, get_db_engine

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def postgres_example_db() -> Generator:
    """Return a connection to the PostgreSQL example DB"""
    example_postgres_uri = (
        "postgresql://postgres:postgres@postgres_example/postgres_example"
    )
    engine = get_db_engine(database_uri=example_postgres_uri)
    logger.debug(f"Connecting to PostgreSQL example database at: {engine.url}")
    SessionLocal = get_db_session(engine=engine)
    the_session = SessionLocal()
    # Setup above...
    yield the_session
    # Teardown below...
    the_session.close()
    engine.dispose()


@pytest.mark.integration
def test_postgres_example_data(postgres_example_db):
    """Confirm that the example database is populated with simulated data"""
    expected_counts = {
        "product": 3,
        "address": 3,
        "customer": 2,
        "employee": 2,
        "payment_card": 2,
        "orders": 4,
        "order_item": 5,
        "visit": 2,
        "login": 7,
        "service_request": 4,
        "report": 4,
    }

    for table_name, expected_count in expected_counts.items():
        # NOTE: we could use text() here, but we want to avoid SQL string
        # templating as much as possible. instead, use the table() helper to
        # dynamically generate the FROM clause for each table_name
        count_sql = select(func.count()).select_from(table(table_name))
        assert postgres_example_db.execute(count_sql).scalar() == expected_count

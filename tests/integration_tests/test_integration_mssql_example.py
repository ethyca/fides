import logging
from typing import Generator

import pytest
from sqlalchemy import func, select, table

from fidesops.db.session import get_db_session, get_db_engine

logger = logging.getLogger(__name__)

MSSQL_URL_TEMPLATE = "mssql+pyodbc://sa:Mssql_pw1@mssql_example:1433/{}?driver=ODBC+Driver+17+for+SQL+Server"
MSSQL_URL = MSSQL_URL_TEMPLATE.format("mssql_example")


@pytest.mark.integration_mssql
@pytest.mark.integration
def test_mssql_example_data(mssql_integration_db):
    """Confirm that the example database is populated with simulated data"""
    expected_counts = {
        "product": 3,
        "address": 4,
        "customer": 3,
        "employee": 2,
        "payment_card": 3,
        "orders": 5,
        "order_item": 6,
        "visit": 2,
        "login": 8,
        "service_request": 4,
        "report": 4,
        "type_link_test": 2,
    }

    for table_name, expected_count in expected_counts.items():
        # NOTE: we could use text() here, but we want to avoid SQL string
        # templating as much as possible. instead, use the table() helper to
        # dynamically generate the FROM clause for each table_name
        count_sql = select(func.count()).select_from(table(table_name))
        assert mssql_integration_db.execute(count_sql).scalar() == expected_count

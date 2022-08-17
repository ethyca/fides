import logging

import pytest
from sqlalchemy import func, select, table

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.integration_mysql
def test_mysql_example_data(mysql_integration_db):
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
        assert mysql_integration_db.execute(count_sql).scalar() == expected_count

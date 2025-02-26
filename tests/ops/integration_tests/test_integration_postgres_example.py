import pytest
from sqlalchemy import func, select, table


@pytest.mark.integration_postgres
@pytest.mark.integration
def test_postgres_example_data(postgres_integration_db):
    """Confirm that the example database is populated with simulated data"""
    expected_counts = {
        "product": 6,
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
        "dynamic_email_address_config": 5,
    }

    for table_name, expected_count in expected_counts.items():
        # NOTE: we could use text() here, but we want to avoid SQL string
        # templating as much as possible. instead, use the table() helper to
        # dynamically generate the FROM clause for each table_name
        count_sql = select(func.count()).select_from(table(table_name))
        actual_count = postgres_integration_db.execute(count_sql).scalar()
        assert actual_count == expected_count

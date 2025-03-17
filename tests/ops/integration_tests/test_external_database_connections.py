import os
from typing import Generator

import pytest
from sqlalchemy import func, inspect, select, table
from toml import load as load_toml

from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.schemas.connection_configuration import RedshiftSchema, SnowflakeSchema
from fides.api.service.connectors import (
    RedshiftConnector,
    SnowflakeConnector,
    get_connector,
)

integration_config = load_toml("tests/ops/integration_test_config.toml")


@pytest.fixture(scope="session")
def redshift_test_engine() -> Generator:
    """Return a connection to an Amazon Redshift Cluster"""

    connection_config = ConnectionConfig(
        name="My Redshift Config",
        key="test_redshift_key",
        connection_type=ConnectionType.redshift,
    )

    # Pulling from integration config file or GitHub secrets
    host = integration_config.get("redshift", {}).get("host") or os.environ.get(
        "REDSHIFT_TEST_HOST"
    )
    port = integration_config.get("redshift", {}).get("port") or os.environ.get(
        "REDSHIFT_TEST_PORT"
    )
    user = integration_config.get("redshift", {}).get("user") or os.environ.get(
        "REDSHIFT_TEST_USER"
    )
    password = integration_config.get("redshift", {}).get("password") or os.environ.get(
        "REDSHIFT_TEST_PASSWORD"
    )
    database = integration_config.get("redshift", {}).get("database") or os.environ.get(
        "REDSHIFT_TEST_DATABASE"
    )
    db_schema = integration_config.get("redshift", {}).get(
        "db_schema"
    ) or os.environ.get("REDSHIFT_TEST_DB_SCHEMA")

    schema = RedshiftSchema(
        host=host,
        port=int(port) if port and port.isdigit() else None,
        user=user,
        password=password,
        database=database,
        db_schema=db_schema,
    )
    connection_config.secrets = schema.model_dump(mode="json")

    connector: RedshiftConnector = get_connector(connection_config)
    engine = connector.client()
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def snowflake_test_engine() -> Generator:
    """Return a connection to a Snowflake database"""
    # Pulling from integration config file or GitHub secrets
    account_identifier = integration_config.get("snowflake", {}).get(
        "account_identifier"
    ) or os.environ.get("SNOWFLAKE_TEST_ACCOUNT_IDENTIFIER")
    user_login_name = integration_config.get("snowflake", {}).get(
        "user_login_name"
    ) or os.environ.get("SNOWFLAKE_TEST_USER_LOGIN_NAME")
    password = integration_config.get("snowflake", {}).get(
        "password"
    ) or os.environ.get("SNOWFLAKE_TEST_PASSWORD")
    warehouse_name = integration_config.get("snowflake", {}).get(
        "warehouse_name"
    ) or os.environ.get("SNOWFLAKE_TEST_WAREHOUSE_NAME")
    database_name = integration_config.get("snowflake", {}).get(
        "database_name"
    ) or os.environ.get("SNOWFLAKE_TEST_DATABASE_NAME")
    schema_name = integration_config.get("snowflake", {}).get(
        "schema_name"
    ) or os.environ.get("SNOWFLAKE_TEST_SCHEMA_NAME")

    schema = SnowflakeSchema(
        account_identifier=account_identifier,
        user_login_name=user_login_name,
        password=password,
        warehouse_name=warehouse_name,
        database_name=database_name,
        schema_name=schema_name,
    )

    connection_config = ConnectionConfig(
        name="My Snowflake Config",
        key="test_snowflake_key",
        connection_type=ConnectionType.snowflake,
        secrets=schema.model_dump(mode="json"),
    )
    connector: SnowflakeConnector = get_connector(connection_config)
    engine = connector.client()
    yield engine
    engine.dispose()


@pytest.mark.integration_external
@pytest.mark.integration_redshift
def test_redshift_sslmode_default(redshift_test_engine):
    """Confirm that sslmode is set to verify-full for non SSH connections"""
    _, kwargs = redshift_test_engine.dialect.create_connect_args(
        redshift_test_engine.url
    )
    assert kwargs["sslmode"] == "verify-full"


@pytest.mark.integration_external
@pytest.mark.integration_redshift
def test_redshift_example_data(redshift_test_engine):
    """Confirm that we can connect to the redshift test db and get table names"""
    inspector = inspect(redshift_test_engine)
    assert sorted(inspector.get_table_names(schema="test")) == sorted(
        [
            "report",
            "service_request",
            "login",
            "visit",
            "order_item",
            "order",
            "payment_card",
            "employee",
            "customer",
            "address",
            "product",
        ]
    )


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_snowflake_example_data(snowflake_test_engine):
    """Confirm that we can connect to the snowflake test db and get table names"""
    inspector = inspect(snowflake_test_engine)
    assert sorted(inspector.get_table_names(schema="test")) == sorted(
        [
            "cc",
            "report",
            "address",
            "customer",
            "employee",
            "login",
            "order",
            "order_item",
            "payment_card",
            "product",
            "report",
            "service_request",
            "visit",
        ]
    )


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
def test_bigquery_example_data(bigquery_test_engine):
    """Confirm that we can connect to the bigquery test db and get table names"""
    inspector = inspect(bigquery_test_engine)

    # we may have added more tables to the test db, so we just check that
    # _at least_ the expected tables below are present
    assert {
        "address",
        "customer",
        "customer_profile",
        "employee",
        "login",
        "order_item",
        "orders",
        "payment_card",
        "product",
        "report",
        "service_request",
        "visit",
        "visit_partitioned",
    }.issubset(set(inspector.get_table_names(schema="fidesopstest")))


@pytest.mark.integration_external
@pytest.mark.integration_google_cloud_sql_mysql
def test_google_cloud_sql_mysql_example_data(google_cloud_sql_mysql_integration_db):
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
        assert (
            google_cloud_sql_mysql_integration_db.execute(count_sql).scalar()
            == expected_count
        )


@pytest.mark.integration_external
@pytest.mark.integration_google_cloud_sql_postgres
def test_google_cloud_sql_postgres_example_data(
    google_cloud_sql_postgres_integration_db,
):
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
        assert (
            google_cloud_sql_postgres_integration_db.execute(count_sql).scalar()
            == expected_count
        )

import os

import logging
import pytest
from sqlalchemy import inspect
from typing import Generator

from fidesops.core.config import load_toml
from fidesops.models.connectionconfig import ConnectionConfig, ConnectionType
from fidesops.schemas.connection_configuration import RedshiftSchema, SnowflakeSchema
from fidesops.service.connectors import (
    get_connector,
    RedshiftConnector,
    SnowflakeConnector,
)

logger = logging.getLogger(__name__)

integration_config = load_toml("fidesops-integration.toml")


@pytest.fixture(scope="session")
def redshift_test_engine() -> Generator:
    """Return a connection to an Amazon Redshift Cluster"""

    connection_config = ConnectionConfig(
        name="My Redshift Config",
        key="test_redshift_key",
        connection_type=ConnectionType.redshift,
    )

    # Pulling from integration config file or GitHub secrets
    uri = integration_config.get("redshift", {}).get("external_uri") or os.environ.get(
        "REDSHIFT_TEST_URI"
    )
    db_schema = integration_config.get("redshift", {}).get(
        "db_schema"
    ) or os.environ.get("REDSHIFT_TEST_DB_SCHEMA")
    if uri and db_schema:
        schema = RedshiftSchema(url=uri, db_schema=db_schema)
        connection_config.secrets = schema.dict()

    connector: RedshiftConnector = get_connector(connection_config)
    engine = connector.client()
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def snowflake_test_engine() -> Generator:
    """Return a connection to a Snowflake database"""
    # Pulling from integration config file or GitHub secrets
    uri = integration_config.get("snowflake", {}).get("external_uri") or os.environ.get(
        "SNOWFLAKE_TEST_URI"
    )
    schema = SnowflakeSchema(url=uri)
    connection_config = ConnectionConfig(
        name="My Snowflake Config",
        key="test_snowflake_key",
        connection_type=ConnectionType.snowflake,
        secrets=schema.dict(),
    )
    connector: SnowflakeConnector = get_connector(connection_config)
    engine = connector.client()
    yield engine
    engine.dispose()


@pytest.mark.integration_external
@pytest.mark.integration_redshift
def test_redshift_example_data(redshift_test_engine):
    """Confirm that we can connect to the redshift test db and get table names"""
    inspector = inspect(redshift_test_engine)
    assert inspector.get_table_names(schema="test") == [
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


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_snowflake_example_data(snowflake_test_engine):
    """Confirm that we can connect to the snowflake test db and get table names"""
    inspector = inspect(snowflake_test_engine)
    assert inspector.get_table_names(schema="test") == [
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


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
def test_bigquery_example_data(bigquery_test_engine):
    """Confirm that we can connect to the bigquery test db and get table names"""
    inspector = inspect(bigquery_test_engine)
    assert inspector.get_table_names(schema="fidesopstest") == [
        "address",
        "customer",
        "employee",
        "login",
        "order_item",
        "orders",
        "payment_card",
        "product",
        "report",
        "service_request",
        "visit",
    ]

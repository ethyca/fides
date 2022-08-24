import ast
import logging
import os
from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.schemas.connection_configuration import BigQuerySchema
from fidesops.ops.service.connectors import BigQueryConnector, get_connector

from .application_fixtures import integration_config

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def bigquery_connection_config_without_secrets(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_bigquery_config",
            "connection_type": ConnectionType.bigquery,
            "access": AccessLevel.write,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def bigquery_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_bigquery_config",
            "connection_type": ConnectionType.bigquery,
            "access": AccessLevel.write,
        },
    )
    # Pulling from integration config file or GitHub secrets
    keyfile_creds = integration_config.get("bigquery", {}).get(
        "keyfile_creds"
    ) or ast.literal_eval(os.environ.get("BIGQUERY_KEYFILE_CREDS"))
    dataset = integration_config.get("bigquery", {}).get("dataset") or os.environ.get(
        "BIGQUERY_DATASET"
    )
    if keyfile_creds:
        schema = BigQuerySchema(keyfile_creds=keyfile_creds, dataset=dataset)
        connection_config.secrets = schema.dict()
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def bigquery_example_test_dataset_config(
    bigquery_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    bigquery_dataset = example_datasets[7]
    fides_key = bigquery_dataset["fides_key"]
    bigquery_connection_config.name = fides_key
    bigquery_connection_config.key = fides_key
    bigquery_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": bigquery_connection_config.id,
            "fides_key": fides_key,
            "dataset": bigquery_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def bigquery_resources(
    bigquery_example_test_dataset_config,
):
    bigquery_connection_config = bigquery_example_test_dataset_config.connection_config
    connector = BigQueryConnector(bigquery_connection_config)
    bigquery_client = connector.client()
    with bigquery_client.connect() as connection:
        uuid = str(uuid4())
        customer_email = f"customer-{uuid}@example.com"
        customer_name = f"{uuid}"

        stmt = "select max(id) from customer;"
        res = connection.execute(stmt)
        customer_id = res.all()[0][0] + 1

        stmt = "select max(id) from address;"
        res = connection.execute(stmt)
        address_id = res.all()[0][0] + 1

        city = "Test City"
        state = "TX"
        stmt = f"""
        insert into address (id, house, street, city, state, zip)
        values ({address_id}, '{111}', 'Test Street', '{city}', '{state}', '55555');
        """
        connection.execute(stmt)

        stmt = f"""
            insert into customer (id, email, name, address_id)
            values ({customer_id}, '{customer_email}', '{customer_name}', {address_id});
        """
        connection.execute(stmt)

        yield {
            "email": customer_email,
            "name": customer_name,
            "id": customer_id,
            "client": bigquery_client,
            "address_id": address_id,
            "city": city,
            "state": state,
            "connector": connector,
        }
        # Remove test data and close BigQuery connection in teardown
        stmt = f"delete from customer where email = '{customer_email}';"
        connection.execute(stmt)

        stmt = f"delete from address where id = {address_id};"
        connection.execute(stmt)


@pytest.fixture(scope="session")
def bigquery_test_engine() -> Generator:
    """Return a connection to a Google BigQuery Warehouse"""

    connection_config = ConnectionConfig(
        name="My BigQuery Config",
        key="test_bigquery_key",
        connection_type=ConnectionType.bigquery,
    )

    # Pulling from integration config file or GitHub secrets
    keyfile_creds = integration_config.get("bigquery", {}).get(
        "keyfile_creds"
    ) or ast.literal_eval(os.environ.get("BIGQUERY_KEYFILE_CREDS"))
    dataset = integration_config.get("bigquery", {}).get("dataset") or os.environ.get(
        "BIGQUERY_DATASET"
    )
    if keyfile_creds:
        schema = BigQuerySchema(keyfile_creds=keyfile_creds, dataset=dataset)
        connection_config.secrets = schema.dict()

    connector: BigQueryConnector = get_connector(connection_config)
    engine = connector.client()
    yield engine
    engine.dispose()


def seed_bigquery_integration_db(bigquery_integration_engine) -> None:
    """
    Currently unused.
    This helper function has already been run once, and data has been populated in the test BigQuery dataset.
    We may need this later for integration erasure tests, or in case tables are accidentally removed.
    """
    logger.info("Seeding bigquery db")
    statements = [
        """
        DROP TABLE IF EXISTS fidesopstest.report;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.service_request;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.login;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.visit;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.order_item;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.orders;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.payment_card;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.employee;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.customer;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.address;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.product;

        """,
        """
        CREATE TABLE fidesopstest.product (
            id INT,
            name STRING,
            price DECIMAL(10,2)
        );
        """,
        """
        CREATE TABLE fidesopstest.address (
            id BIGINT,
            house STRING,
            street STRING,
            city STRING,
            state STRING,
            zip STRING
        );
        """,
        """
        CREATE TABLE fidesopstest.customer (
            id INT,
            email STRING,
            name  STRING,
            created TIMESTAMP,
            address_id BIGINT
        );
        """,
        """
        CREATE TABLE fidesopstest.employee (
            id INT,
            email STRING,
            name STRING,
            address_id BIGINT
        );
        """,
        """
        CREATE TABLE fidesopstest.payment_card (
            id STRING,
            name STRING,
            ccn BIGINT,
            code SMALLINT,
            preferred BOOLEAN,
            customer_id INT,
            billing_address_id BIGINT
        );
        """,
        """
        CREATE TABLE fidesopstest.orders (
            id STRING,
            customer_id INT,
            shipping_address_id BIGINT,
            payment_card_id STRING
        );
        """,
        """
        CREATE TABLE fidesopstest.order_item (
            order_id STRING,
            item_no SMALLINT,
            product_id INT,
            quantity SMALLINT
        );
        """,
        """
        CREATE TABLE fidesopstest.visit (
            email STRING,
            last_visit TIMESTAMP
        );
        """,
        """
        CREATE TABLE fidesopstest.login (
            id INT,
            customer_id INT,
            time TIMESTAMP
        );
        """,
        """
        CREATE TABLE fidesopstest.service_request (
            id STRING,
            email STRING,
            alt_email STRING,
            opened DATE,
            closed DATE,
            employee_id INT
        );
        """,
        """
        CREATE TABLE fidesopstest.report (
            id INT,
            email STRING,
            name STRING,
            year INT,
            month INT,
            total_visits INT
        );
        """,
        """
        INSERT INTO fidesopstest.product VALUES
        (1, 'Example Product 1', 10.00),
        (2, 'Example Product 2', 20.00),
        (3, 'Example Product 3', 50.00);
        """,
        """
        INSERT INTO fidesopstest.address VALUES
        (1, '123', 'Example Street', 'Exampletown', 'NY', '12345'),
        (2, '4', 'Example Lane', 'Exampletown', 'NY', '12321'),
        (3, '555', 'Example Ave', 'Example City', 'NY', '12000');
        """,
        """
        INSERT INTO fidesopstest.customer VALUES
        (1, 'customer-1@example.com', 'John Customer', '2020-04-01 11:47:42', 1),
        (2, 'customer-2@example.com', 'Jill Customer', '2020-04-01 11:47:42', 2);
        """,
        """
        INSERT INTO fidesopstest.employee VALUES
        (1, 'employee-1@example.com', 'Jack Employee', 3),
        (2, 'employee-2@example.com', 'Jane Employee', 3);
        """,
        """
        INSERT INTO fidesopstest.payment_card VALUES
        ('pay_aaa-aaa', 'Example Card 1', 123456789, 321, true, 1, 1),
        ('pay_bbb-bbb', 'Example Card 2', 987654321, 123, false, 2, 1);
        """,
        """
        INSERT INTO fidesopstest.orders VALUES
        ('ord_aaa-aaa', 1, 2, 'pay_aaa-aaa'),
        ('ord_bbb-bbb', 2, 1, 'pay_bbb-bbb'),
        ('ord_ccc-ccc', 1, 1, 'pay_aaa-aaa'),
        ('ord_ddd-ddd', 1, 1, 'pay_bbb-bbb');
        """,
        """
        INSERT INTO fidesopstest.order_item VALUES
        ('ord_aaa-aaa', 1, 1, 1),
        ('ord_bbb-bbb', 1, 1, 1),
        ('ord_ccc-ccc', 1, 1, 1),
        ('ord_ccc-ccc', 2, 2, 1),
        ('ord_ddd-ddd', 1, 1, 1);
        """,
        """
        INSERT INTO fidesopstest.visit VALUES
        ('customer-1@example.com', '2021-01-06 01:00:00'),
        ('customer-2@example.com', '2021-01-06 01:00:00');
        """,
        """
        INSERT INTO fidesopstest.login VALUES
        (1, 1, '2021-01-01 01:00:00'),
        (2, 1, '2021-01-02 01:00:00'),
        (5, 1, '2021-01-05 01:00:00'),
        (6, 1, '2021-01-06 01:00:00'),
        (7, 2, '2021-01-06 01:00:00');
        """,
        """
        INSERT INTO fidesopstest.service_request VALUES
        ('ser_aaa-aaa', 'customer-1@example.com', 'customer-1-alt@example.com', '2021-01-01', '2021-01-03', 1),
        ('ser_bbb-bbb', 'customer-2@example.com', null, '2021-01-04', null, 1),
        ('ser_ccc-ccc', 'customer-3@example.com', null, '2021-01-05', '2020-01-07', 1),
        ('ser_ddd-ddd', 'customer-3@example.com', null, '2021-05-05', '2020-05-08', 2);
        """,
        """
        INSERT INTO fidesopstest.report VALUES
        (1, 'admin-account@example.com', 'Monthly Report', 2021, 8, 100),
        (2, 'admin-account@example.com', 'Monthly Report', 2021, 9, 100),
        (3, 'admin-account@example.com', 'Monthly Report', 2021, 10, 100),
        (4, 'admin-account@example.com', 'Monthly Report', 2021, 11, 100);
        """,
    ]
    with bigquery_integration_engine.connect() as connection:
        [connection.execute(stmt) for stmt in statements]
    logger.info("Finished seeding bigquery db")
    return

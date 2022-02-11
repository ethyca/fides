import logging
from collections import Generator
from typing import List, Dict
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fidesops.db.session import get_db_session, get_db_engine
from fidesops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionType,
    AccessLevel,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.service.connectors import MariaDBConnector
from .application_fixtures import integration_secrets

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def connection_config_mariadb(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_maria_db_1",
            "connection_type": ConnectionType.mariadb,
            "access": AccessLevel.write,
            "secrets": integration_secrets["mariadb_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="session")
def mariadb_example_db() -> Generator:
    """Return a connection to the MariaDB example DB"""
    example_mariadb_uri = (
        "mariadb+pymysql://mariadb_user:mariadb_pw@mariadb_example/mariadb_example"
    )
    engine = get_db_engine(database_uri=example_mariadb_uri)
    logger.debug(f"Connecting to MariaDB example database at: {engine.url}")
    SessionLocal = get_db_session(engine=engine)
    the_session = SessionLocal()
    # Setup above...
    yield the_session
    # Teardown below...
    the_session.close()
    engine.dispose()


@pytest.fixture
def mariadb_example_test_dataset_config(
    connection_config_mariadb: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    mariadb_dataset = example_datasets[6]
    fides_key = mariadb_dataset["fides_key"]
    connection_config_mariadb.name = fides_key
    connection_config_mariadb.key = fides_key
    connection_config_mariadb.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_mariadb.id,
            "fides_key": fides_key,
            "dataset": mariadb_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def mariadb_integration_session(connection_config_mariadb):
    example_mariadb_uri = MariaDBConnector(connection_config_mariadb).build_uri()
    engine = get_db_engine(database_uri=example_mariadb_uri)
    SessionLocal = get_db_session(
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
    yield SessionLocal()


def truncate_all_tables(db_session):
    tables = [
        "report",
        "service_request",
        "login",
        "visit",
        "order_item",
        "orders",
        "payment_card",
        "employee",
        "customer",
        "address",
        "product",
    ]
    [db_session.execute(f"TRUNCATE TABLE {table};") for table in tables]


@pytest.fixture(scope="function")
def mariadb_integration_db(mariadb_integration_session):
    truncate_all_tables(mariadb_integration_session)
    statements = [
        """
        INSERT INTO product VALUES
        (1, 'Example Product 1', 10.00),
        (2, 'Example Product 2', 20.00),
        (3, 'Example Product 3', 50.00);
        """,
        """
        INSERT INTO address VALUES
        (1, '123', 'Example Street', 'Exampletown', 'NY', '12345'),
        (2, '4', 'Example Lane', 'Exampletown', 'NY', '12321'),
        (3, '555', 'Example Ave', 'Example City', 'NY', '12000');
        """,
        """
        INSERT INTO customer VALUES
        (1, 'customer-1@example.com', 'John Customer', '2020-04-01 11:47:42', 1),
        (2, 'customer-2@example.com', 'Jill Customer', '2020-04-01 11:47:42', 2);
        """,
        """
        INSERT INTO employee VALUES
        (1, 'employee-1@example.com', 'Jack Employee', 3),
        (2, 'employee-2@example.com', 'Jane Employee', 3);
        """,
        """
        INSERT INTO payment_card VALUES
        ('pay_aaa-aaa', 'Example Card 1', 123456789, 321, true, 1, 1),
        ('pay_bbb-bbb', 'Example Card 2', 987654321, 123, false, 2, 1);
        """,
        """
        INSERT INTO orders VALUES
        ('ord_aaa-aaa', 1, 2, 'pay_aaa-aaa'),
        ('ord_bbb-bbb', 2, 1, 'pay_bbb-bbb'),
        ('ord_ccc-ccc', 1, 1, 'pay_aaa-aaa'),
        ('ord_ddd-ddd', 1, 1, 'pay_bbb-bbb');
        """,
        """
        INSERT INTO order_item VALUES
        ('ord_aaa-aaa', 1, 1, 1),
        ('ord_bbb-bbb', 1, 1, 1),
        ('ord_ccc-ccc', 1, 1, 1),
        ('ord_ccc-ccc', 2, 2, 1),
        ('ord_ddd-ddd', 1, 1, 1);
        """,
        """
        INSERT INTO visit VALUES
        ('customer-1@example.com', '2021-01-06 01:00:00'),
        ('customer-2@example.com', '2021-01-06 01:00:00');
        """,
        """
        INSERT INTO login VALUES
        (1, 1, '2021-01-01 01:00:00'),
        (2, 1, '2021-01-02 01:00:00'),
        (3, 1, '2021-01-03 01:00:00'),
        (4, 1, '2021-01-04 01:00:00'),
        (5, 1, '2021-01-05 01:00:00'),
        (6, 1, '2021-01-06 01:00:00'),
        (7, 2, '2021-01-06 01:00:00');
        """,
        """
        INSERT INTO service_request VALUES
        ('ser_aaa-aaa', 'customer-1@example.com', 'customer-1-alt@example.com', '2021-01-01', '2021-01-03', 1),
        ('ser_bbb-bbb', 'customer-2@example.com', null, '2021-01-04', null, 1),
        ('ser_ccc-ccc', 'customer-3@example.com', null, '2021-01-05', '2020-01-07', 1),
        ('ser_ddd-ddd', 'customer-3@example.com', null, '2021-05-05', '2020-05-08', 2);
        """,
        """
        INSERT INTO report VALUES
        (1, 'admin-account@example.com', 'Monthly Report', 2021, 8, 100),
        (2, 'admin-account@example.com', 'Monthly Report', 2021, 9, 100),
        (3, 'admin-account@example.com', 'Monthly Report', 2021, 10, 100),
        (4, 'admin-account@example.com', 'Monthly Report', 2021, 11, 100);
        """,
    ]
    [mariadb_integration_session.execute(stmt) for stmt in statements]
    yield mariadb_integration_session
    truncate_all_tables(mariadb_integration_session)

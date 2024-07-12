from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.db.session import get_db_engine, get_db_session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.service.connectors import MySQLConnector
from fides.config import CONFIG

from .application_fixtures import integration_secrets


@pytest.fixture(scope="function")
def mysql_example_secrets():
    return integration_secrets["mysql_example"]


@pytest.fixture(scope="function")
def dataset_config_mysql(
    connection_config: ConnectionConfig,
    db: Session,
) -> Generator:
    dataset = {
        "fides_key": "mysql_example_subscriptions_dataset",
        "name": "Mysql Example Subscribers Dataset",
        "description": "Example Mysql dataset created in test fixtures",
        "dataset_type": "MySQL",
        "location": "mysql_example.test",
        "collections": [
            {
                "name": "subscriptions",
                "fields": [
                    {
                        "name": "id",
                        "data_categories": ["system.operations"],
                    },
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {
                            "identity": "email",
                        },
                    },
                ],
            },
        ],
    }
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "mysql_example_subscriptions_dataset",
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db)
    ctl_dataset.delete(db)


@pytest.fixture
def mysql_example_test_dataset_config(
    connection_config_mysql: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    mysql_dataset = example_datasets[5]
    fides_key = mysql_dataset["fides_key"]
    connection_config_mysql.name = fides_key
    connection_config_mysql.key = fides_key
    connection_config_mysql.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, mysql_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_mysql.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def connection_config_mysql(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_mysql_db_1",
            "connection_type": ConnectionType.mysql,
            "access": AccessLevel.write,
            "secrets": integration_secrets["mysql_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def mysql_integration_session_cls(connection_config_mysql):
    example_postgres_uri = MySQLConnector(connection_config_mysql).build_uri()
    engine = get_db_engine(database_uri=example_postgres_uri)
    SessionLocal = get_db_session(
        config=CONFIG,
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
    yield SessionLocal


@pytest.fixture(scope="function")
def mysql_integration_session(mysql_integration_session_cls):
    yield mysql_integration_session_cls()


def truncate_all_tables(mysql_integration_session):
    tables = [
        "product",
        "customer",
        "employee",
        "address",
        "customer",
        "employee",
        "payment_card",
        "orders",
        "order_item",
        "visit",
        "login",
        "service_request",
        "report",
        "`Lead`",
    ]
    [mysql_integration_session.execute(f"TRUNCATE TABLE {table};") for table in tables]


@pytest.fixture(scope="function")
def mysql_integration_db(mysql_integration_session):
    truncate_all_tables(mysql_integration_session)
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
        """
        INSERT INTO `Lead` VALUES
        ('test@example.com', '2021-01-05'); -- test case for table with reserved keyword
        """,
    ]
    [mysql_integration_session.execute(stmt) for stmt in statements]
    yield mysql_integration_session
    truncate_all_tables(mysql_integration_session)

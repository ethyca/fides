import logging
from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fidesops.db.session import get_db_engine, get_db_session
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.service.connectors import MicrosoftSQLServerConnector

from .application_fixtures import integration_secrets

logger = logging.getLogger(__name__)


@pytest.fixture
def mssql_example_test_dataset_config(
    connection_config_mssql: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    mssql_dataset = example_datasets[4]
    fides_key = mssql_dataset["fides_key"]
    connection_config_mssql.name = fides_key
    connection_config_mssql.key = fides_key
    connection_config_mssql.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_mssql.id,
            "fides_key": fides_key,
            "dataset": mssql_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def connection_config_mssql(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_mssql_db_1",
            "connection_type": ConnectionType.mssql,
            "access": AccessLevel.write,
            "secrets": integration_secrets["mssql_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def mssql_integration_session_cls(connection_config_mssql):
    uri = MicrosoftSQLServerConnector(connection_config_mssql).build_uri()
    engine = get_db_engine(database_uri=uri)
    SessionLocal = get_db_session(
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
    yield SessionLocal


@pytest.fixture(scope="function")
def mssql_integration_session(mssql_integration_session_cls):
    yield mssql_integration_session_cls()


def truncate_all_tables(mssql_integration_session):
    tables = [
        "dbo.product",
        "dbo.customer",
        "dbo.employee",
        "dbo.address",
        "dbo.customer",
        "dbo.employee",
        "dbo.payment_card",
        "dbo.orders",
        "dbo.order_item",
        "dbo.visit",
        "dbo.login",
        "dbo.service_request",
        "dbo.report",
        "dbo.type_link_test",
        "dbo.composite_pk_test",
    ]
    [mssql_integration_session.execute(f"DELETE FROM {table};") for table in tables]


@pytest.fixture(scope="function")
def mssql_integration_db(mssql_integration_session):
    truncate_all_tables(mssql_integration_session)
    statements = [
        "INSERT INTO dbo.product VALUES (1, 'Example Product 1', '$10.00'), (2, 'Example Product 2', '$20.00'), (3, 'Example Product 3', '$50.00');",
        "INSERT INTO dbo.address VALUES (1, '123', 'Example Street', 'Exampletown', 'NY', '12345'), (2, '4', 'Example Lane', 'Exampletown', 'NY', '12321'), (3, '555', 'Example Ave', 'Example City', 'NY', '12000'), (4, '1111', 'Example Place', 'Example Mountain', 'TX', '54321');",
        "INSERT INTO dbo.customer VALUES (1, 'customer-1@example.com', 'John Customer', '2020-04-01 11:47:42', 1), (2, 'customer-2@example.com', 'Jill Customer', '2020-04-01 11:47:42', 2), (3, 'jane@example.com', 'Jane Customer', '2020-04-01 11:47:42', 4);",
        "INSERT INTO dbo.employee VALUES (1, 'employee-1@example.com', 'Jack Employee', 3), (2, 'employee-2@example.com', 'Jane Employee', 3);",
        "INSERT INTO dbo.payment_card VALUES ('pay_aaa-aaa', 'Example Card 1', 123456789, 321, 1, 1, 1), ('pay_bbb-bbb', 'Example Card 2', 987654321, 123, 0, 2, 1), ('pay_ccc-ccc', 'Example Card 3', 373719391, 222, 0, 3, 4);",
        "INSERT INTO dbo.orders VALUES ('ord_aaa-aaa', 1, 2, 'pay_aaa-aaa'), ('ord_bbb-bbb', 2, 1, 'pay_bbb-bbb'), ('ord_ccc-ccc', 1, 1, 'pay_aaa-aaa'), ('ord_ddd-ddd', 1, 1, 'pay_bbb-bbb'), ('ord_ddd-eee', 3, 4, 'pay-ccc-ccc');",
        "INSERT INTO dbo.order_item VALUES ('ord_aaa-aaa', 1, 1, 1), ('ord_bbb-bbb', 1, 1, 1), ('ord_ccc-ccc', 1, 1, 1), ('ord_ccc-ccc', 2, 2, 1), ('ord_ddd-ddd', 1, 1, 1), ('ord_eee-eee', 3, 4, 3);",
        "INSERT INTO dbo.visit VALUES ('customer-1@example.com', '2021-01-06 01:00:00'), ('customer-2@example.com', '2021-01-06 01:00:00');",
        "INSERT INTO dbo.login VALUES (1, 1, '2021-01-01 01:00:00'), (2, 1, '2021-01-02 01:00:00'), (3, 1, '2021-01-03 01:00:00'), (4, 1, '2021-01-04 01:00:00'), (5, 1, '2021-01-05 01:00:00'), (6, 1, '2021-01-06 01:00:00'), (7, 2, '2021-01-06 01:00:00'), (8, 3, '2021-01-06 01:00:00');",
        "INSERT INTO dbo.service_request VALUES ('ser_aaa-aaa', 'customer-1@example.com', 'customer-1-alt@example.com', '2021-01-01', '2021-01-03', 1), ('ser_bbb-bbb', 'customer-2@example.com', null, '2021-01-04', null, 1), ('ser_ccc-ccc', 'customer-3@example.com', null, '2021-01-05', '2020-01-07', 1), ('ser_ddd-ddd', 'customer-3@example.com', null, '2021-05-05', '2020-05-08', 2);",
        "INSERT INTO dbo.report VALUES (1, 'admin-account@example.com', 'Monthly Report', 2021, 8, 100), (2, 'admin-account@example.com', 'Monthly Report', 2021, 9, 100), (3, 'admin-account@example.com', 'Monthly Report', 2021, 10, 100), (4, 'admin-account@example.com', 'Monthly Report', 2021, 11, 100);",
        "INSERT INTO dbo.type_link_test VALUES ('1', 'name1'), ('2', 'name2');",
        "INSERT INTO dbo.composite_pk_test VALUES (1,10,'linked to customer 1',1), (1,11,'linked to customer 2',2), (2,10,'linked to customer 3',3);",
    ]
    [mssql_integration_session.execute(stmt) for stmt in statements]
    yield mssql_integration_session
    truncate_all_tables(mssql_integration_session)

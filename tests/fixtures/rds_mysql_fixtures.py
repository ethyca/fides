import os
from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.db.session import get_db_session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.connection_configuration import RDSMySQLSchema
from fides.api.service.connectors import RDSMySQLConnector
from fides.config import CONFIG

from .application_fixtures import integration_config


@pytest.fixture(scope="function")
def rds_mysql_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_rds_mysql_config",
            "connection_type": ConnectionType.rds_mysql,
            "access": AccessLevel.write,
        },
    )

    # Pulling from integration config file or GitHub secrets
    rds_mysql_integration_config = integration_config.get("rds_mysql", {})

    region = rds_mysql_integration_config.get("region") or os.environ.get(
        "RDS_MYSQL_REGION"
    )
    aws_access_key_id = rds_mysql_integration_config.get(
        "aws_access_key_id"
    ) or os.environ.get("RDS_MYSQL_AWS_ACCESS_KEY_ID")
    aws_secret_access_key = rds_mysql_integration_config.get(
        "aws_secret_access_key"
    ) or os.environ.get("RDS_MYSQL_AWS_SECRET_ACCESS_KEY")
    db_username = rds_mysql_integration_config.get("db_username") or os.environ.get(
        "RDS_MYSQL_DB_USERNAME"
    )
    db_instance = rds_mysql_integration_config.get("db_instance") or os.environ.get(
        "RDS_MYSQL_DB_INSTANCE"
    )
    db_name = rds_mysql_integration_config.get("db_name") or os.environ.get(
        "RDS_MYSQL_DB_NAME"
    )

    if not region:
        raise RuntimeError("Missing region for RDS MySQL")

    if not aws_access_key_id:
        raise RuntimeError("Missing aws_access_key_id for RDS MySQL")

    if not aws_secret_access_key:
        raise RuntimeError("Missing aws_secret_access_key for RDS MySQL")

    if not db_username:
        raise RuntimeError("Missing db_username for RDS MySQL")

    if not db_instance:
        raise RuntimeError("Missing db_instance for RDS MySQL")

    if not db_name:
        raise RuntimeError("Missing db_name for RDS MySQL")

    schema = RDSMySQLSchema(
        auth_method="secret_keys",
        region=region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        db_username=db_username,
    )
    connection_config.secrets = schema.model_dump()
    connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def rds_mysql_integration_session(
    rds_mysql_connection_config,
):
    connector = RDSMySQLConnector(rds_mysql_connection_config)
    # connector.
    engine = connector.client()

    yield get_db_session(
        config=CONFIG,
        engine=engine,
        autocommit=True,
        autoflush=True,
    )()


@pytest.fixture(scope="function")
def rds_mysql_integration_db(
    rds_mysql_integration_session,
):
    # The database scheme has been preloaded with
    # https://github.com/ethyca/fides/blob/5a485387d8af247ec6479e4115088cbbb8394d77/docker/sample_data/postgres_example.sql
    """
    INSERT INTO product VALUES
    (1, 'Example Product 1', 10.00),
    (2, 'Example Product 2', 20.00),
    (3, 'Example Product 3', 50.00);

    INSERT INTO address VALUES
    (1, '123', 'Example Street', 'Exampletown', 'NY', '12345'),
    (2, '4', 'Example Lane', 'Exampletown', 'NY', '12321'),
    (3, '555', 'Example Ave', 'Example City', 'NY', '12000');

    INSERT INTO customer VALUES
    (1, 'customer-1@example.com', 'John Customer', '2020-04-01 11:47:42', 1),
    (2, 'customer-2@example.com', 'Jill Customer', '2020-04-01 11:47:42', 2);

    INSERT INTO employee VALUES
    (1, 'employee-1@example.com', 'Jack Employee', 3),
    (2, 'employee-2@example.com', 'Jane Employee', 3);

    INSERT INTO payment_card VALUES
    ('pay_aaa-aaa', 'Example Card 1', 123456789, 321, true, 1, 1),
    ('pay_bbb-bbb', 'Example Card 2', 987654321, 123, false, 2, 1);

    INSERT INTO orders VALUES
    ('ord_aaa-aaa', 1, 2, 'pay_aaa-aaa'),
    ('ord_bbb-bbb', 2, 1, 'pay_bbb-bbb'),
    ('ord_ccc-ccc', 1, 1, 'pay_aaa-aaa'),
    ('ord_ddd-ddd', 1, 1, 'pay_bbb-bbb');

    INSERT INTO order_item VALUES
    ('ord_aaa-aaa', 1, 1, 1),
    ('ord_bbb-bbb', 1, 1, 1),
    ('ord_ccc-ccc', 1, 1, 1),
    ('ord_ccc-ccc', 2, 2, 1),
    ('ord_ddd-ddd', 1, 1, 1);

    INSERT INTO visit VALUES
    ('customer-1@example.com', '2021-01-06 01:00:00'),
    ('customer-2@example.com', '2021-01-06 01:00:00');

    INSERT INTO login VALUES
    (1, 1, '2021-01-01 01:00:00'),
    (2, 1, '2021-01-02 01:00:00'),
    (3, 1, '2021-01-03 01:00:00'),
    (4, 1, '2021-01-04 01:00:00'),
    (5, 1, '2021-01-05 01:00:00'),
    (6, 1, '2021-01-06 01:00:00'),
    (7, 2, '2021-01-06 01:00:00');

    INSERT INTO service_request VALUES
    ('ser_aaa-aaa', 'customer-1@example.com', 'customer-1-alt@example.com', '2021-01-01', '2021-01-03', 1),
    ('ser_bbb-bbb', 'customer-2@example.com', null, '2021-01-04', null, 1),
    ('ser_ccc-ccc', 'customer-3@example.com', null, '2021-01-05', '2020-01-07', 1),
    ('ser_ddd-ddd', 'customer-3@example.com', null, '2021-05-05', '2020-05-08', 2);

    INSERT INTO report VALUES
    (1, 'admin-account@example.com', 'Monthly Report', 2021, 8, 100),
    (2, 'admin-account@example.com', 'Monthly Report', 2021, 9, 100),
    (3, 'admin-account@example.com', 'Monthly Report', 2021, 10, 100),
    (4, 'admin-account@example.com', 'Monthly Report', 2021, 11, 100);
    """
    yield rds_mysql_integration_session


@pytest.fixture
def rds_mysql_example_test_dataset_config(
    rds_mysql_connection_config: ConnectionConfig,
    db: Session,
    example_datasets_function,
) -> Generator:
    dataset = example_datasets_function("data/dataset/rds_mysql_test_dataset.yml")
    fides_key = dataset["fides_key"]
    rds_mysql_connection_config.name = fides_key
    rds_mysql_connection_config.key = fides_key
    rds_mysql_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": rds_mysql_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)

import logging
from typing import Dict, Generator, List
from uuid import uuid4

import pytest
import sqlalchemy
from sqlalchemy.orm import Session

from fidesops.db.session import get_db_engine, get_db_session
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
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
    SessionLocal = get_db_session(
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
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
    with open("./data/sql/mariadb_example_data.sql", "r") as query_file:
        lines = query_file.read().splitlines()
        filtered = [line for line in lines if not line.startswith("--")]
        queries = " ".join(filtered).split(";")
        [
            mariadb_integration_session.execute(f"{sqlalchemy.text(query.strip())};")
            for query in queries
            if query
        ]
    yield mariadb_integration_session
    truncate_all_tables(mariadb_integration_session)

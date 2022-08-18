import logging
from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from fideslib.db.session import get_db_engine, get_db_session
from fidesops.ops.core.config import config
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.models.policy import ActionType
from fidesops.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fidesops.ops.service.connectors import PostgreSQLConnector
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from .application_fixtures import integration_secrets

logger = logging.getLogger(__name__)


@pytest.fixture
def postgres_example_test_dataset_config(
    connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[0]
    fides_key = postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "dataset": postgres_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture
def postgres_example_test_dataset_config_read_access(
    read_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[0]
    fides_key = postgres_dataset["fides_key"]
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": read_connection_config.id,
            "fides_key": fides_key,
            "dataset": postgres_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def postgres_execution_log(
    db: Session,
    privacy_request: PrivacyRequest,
) -> ExecutionLog:
    el = ExecutionLog.create(
        db=db,
        data={
            "dataset_name": "my-postgres-db",
            "collection_name": "user",
            "fields_affected": [
                {
                    "path": "my-postgres-db:user:email",
                    "field_name": "email",
                    "data_categories": ["user.contact.email"],
                }
            ],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.pending,
            "privacy_request_id": privacy_request.id,
        },
    )
    yield el
    el.delete(db)


# TODO: Consolidate these
@pytest.fixture(scope="function")
def second_postgres_execution_log(
    db: Session, privacy_request: PrivacyRequest
) -> ExecutionLog:
    el = ExecutionLog.create(
        db=db,
        data={
            "dataset_name": "my-postgres-db",
            "collection_name": "address",
            "fields_affected": [
                {
                    "path": "my-postgres-db:address:street",
                    "field_name": "street",
                    "data_categories": ["user.contact.address.street"],
                },
                {
                    "path": "my-postgres-db:address:city",
                    "field_name": "city",
                    "data_categories": ["user.contact.address.city"],
                },
            ],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.error,
            "privacy_request_id": privacy_request.id,
            "message": "Database timed out.",
        },
    )
    yield el
    el.delete(db)


@pytest.fixture(scope="function")
def connection_config(
    db: Session,
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_postgres_db_1",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
            "secrets": integration_secrets["postgres_example"],
            "disabled": False,
            "description": "Primary postgres connection",
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def disabled_connection_config(
    db: Session,
) -> Generator:
    disabled_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "disabled_postgres_connection",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.read,
            "secrets": integration_secrets["postgres_example"],
            "disabled": True,
            "description": "Old postgres connection",
        },
    )
    yield connection_config
    disabled_config.delete(db)


@pytest.fixture(scope="function")
def read_connection_config(
    db: Session,
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_postgres_db_1_read_config",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.read,
            "secrets": integration_secrets["postgres_example"],
            "description": "Read-only connection config",
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def postgres_integration_session_cls(connection_config):
    example_postgres_uri = PostgreSQLConnector(connection_config).build_uri()
    engine = get_db_engine(database_uri=example_postgres_uri)
    SessionLocal = get_db_session(
        config=config,
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
    yield SessionLocal


@pytest.fixture(scope="function")
def postgres_integration_session(postgres_integration_session_cls):
    yield postgres_integration_session_cls()


@pytest.fixture(scope="function")
def postgres_integration_db(postgres_integration_session):
    if database_exists(postgres_integration_session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(postgres_integration_session.bind.url)
    create_database(postgres_integration_session.bind.url)
    with open("./docker/sample_data/postgres_example.sql", "r") as query_file:
        lines = query_file.read().splitlines()
        filtered = [line for line in lines if not line.startswith("--")]
        queries = " ".join(filtered).split(";")
        [
            postgres_integration_session.execute(f"{text(query.strip())};")
            for query in queries
            if query
        ]
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)

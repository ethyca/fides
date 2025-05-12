from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from fideslang.models import Dataset as FideslangDataset
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError
from sqlalchemy_utils.functions import drop_database

from fides.api.db.session import get_db_engine, get_db_session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import ActionType
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.models.sql_models import System
from fides.api.schemas.privacy_request import ExecutionLogStatus
from fides.api.service.connectors import PostgreSQLConnector
from fides.config import CONFIG
from tests.ops.test_helpers.dataset_utils import remove_primary_keys
from tests.ops.test_helpers.db_utils import seed_postgres_data

from .application_fixtures import integration_secrets


@pytest.fixture(scope="function")
def postgres_example_secrets():
    return integration_secrets["postgres_example"]


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

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def postgres_example_test_extended_dataset_config(
    connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[12]
    fides_key = postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def postgres_example_test_dataset_config_read_access(
    read_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[0]
    fides_key = postgres_dataset["fides_key"]

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": read_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def postgres_example_test_dataset_config_read_access_without_primary_keys(
    read_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[0]
    fides_key = postgres_dataset["fides_key"]

    dataset = FideslangDataset(**postgres_dataset)
    updated_dataset = remove_primary_keys(dataset)
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db, updated_dataset.model_dump(mode="json")
    )

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": read_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def postgres_example_test_dataset_config_skipped_login_collection(
    read_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[0].copy()
    fides_key = postgres_dataset["fides_key"]

    skipped_collection = next(
        col for col in postgres_dataset["collections"] if col["name"] == "login"
    )
    skipped_collection["fides_meta"] = {}
    skipped_collection["fides_meta"]["skip_processing"] = True

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": read_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def postgres_example_test_dataset_config_skipped_address_collection(
    read_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[0].copy()
    fides_key = postgres_dataset["fides_key"]

    skipped_collection = next(
        col for col in postgres_dataset["collections"] if col["name"] == "address"
    )
    skipped_collection["fides_meta"] = {}
    skipped_collection["fides_meta"]["skip_processing"] = True

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": read_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


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
def async_execution_log(db: Session, privacy_request: PrivacyRequest) -> ExecutionLog:
    el = ExecutionLog.create(
        db=db,
        data={
            "dataset_name": "my-async-connector",
            "collection_name": "my_async_collection",
            "fields_affected": [
                {
                    "path": "my-async-connector:my_async_collection:street",
                    "field_name": "street",
                    "data_categories": ["user.contact.address.street"],
                },
                {
                    "path": "my-async-connector:my_async_collection:city",
                    "field_name": "city",
                    "data_categories": ["user.contact.address.city"],
                },
            ],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.awaiting_processing,
            "privacy_request_id": privacy_request.id,
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

    try:
        connection_config.delete(db)
    except ObjectDeletedError:
        pass


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
    system: System,
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_postgres_db_1_read_config",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.read,
            "system_id": system.id,
            "secrets": integration_secrets["postgres_example"],
            "description": "Read-only connection config",
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def postgres_connection_config_with_schema(
    db: Session,
) -> Generator:
    """Create a connection config with a db_schema set which allows the PostgresConnector to connect
    to a non-default schema"""
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_postgres_db_backup_schema",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
            "secrets": integration_secrets["postgres_example"],
            "disabled": False,
            "description": "Backup postgres data",
        },
    )
    connection_config.secrets["db_schema"] = (
        "backup_schema"  # Matches the second schema created in postgres_example.schema
    )
    connection_config.save(db)
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def postgres_integration_session_cls(connection_config):
    example_postgres_uri = PostgreSQLConnector(connection_config).build_uri()
    engine = get_db_engine(database_uri=example_postgres_uri)
    SessionLocal = get_db_session(
        config=CONFIG,
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
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./src/fides/data/sample_project/postgres_sample.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)

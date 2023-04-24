from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session
from sqlalchemy_utils import drop_database

from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.service.connectors import TimescaleConnector
from fides.core.config import CONFIG
from fides.api.ops.db.session import get_db_engine, get_db_session
from tests.ops.test_helpers.db_utils import seed_postgres_data

from .application_fixtures import integration_secrets


@pytest.fixture(scope="function")
def timescale_connection_config(
    db: Session,
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_timescale_db_1",
            "connection_type": ConnectionType.timescale,
            "access": AccessLevel.write,
            "secrets": integration_secrets["timescale_example"],
            "disabled": False,
            "description": "Primary timescaleDB connection",
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def timescale_integration_session_cls(timescale_connection_config):
    example_timescale_uri = TimescaleConnector(timescale_connection_config).build_uri()
    engine = get_db_engine(database_uri=example_timescale_uri)
    SessionLocal = get_db_session(
        config=CONFIG,
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
    yield SessionLocal


@pytest.fixture(scope="function")
def timescale_integration_session(timescale_integration_session_cls):
    session = timescale_integration_session_cls()
    yield session
    session.close()


@pytest.fixture(scope="function")
def timescale_integration_db(timescale_integration_session):
    timescale_integration_session = seed_postgres_data(
        timescale_integration_session, "./docker/sample_data/timescale_example.sql"
    )
    yield timescale_integration_session
    drop_database(timescale_integration_session.bind.url)

from typing import Generator
from uuid import uuid4

import pytest
from fideslib.db.session import get_db_engine, get_db_session
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

from fidesops.ops.core.config import config
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.service.connectors import TimescaleConnector

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
        config=config,
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
    if database_exists(timescale_integration_session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(timescale_integration_session.bind.url)
    create_database(timescale_integration_session.bind.url)
    with open("./docker/sample_data/timescale_example.sql", "r") as query_file:
        lines = query_file.read().splitlines()
        filtered = [line for line in lines if not line.startswith("--")]
        queries = " ".join(filtered).split(";")
        [
            timescale_integration_session.execute(f"{text(query.strip())};")
            for query in queries
            if query
        ]
    yield timescale_integration_session
    drop_database(timescale_integration_session.bind.url)

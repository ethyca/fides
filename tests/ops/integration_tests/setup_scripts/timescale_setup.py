from uuid import uuid4

import pydash
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database
from toml import load as load_toml

from fides.api.db.session import get_db_engine, get_db_session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.privacy_experience import PrivacyExperienceConfig
from fides.api.service.connectors import TimescaleConnector
from fides.config import CONFIG

integration_config = load_toml("tests/ops/integration_test_config.toml")


def seed_postgres_data(db: Session, query_file_path: str) -> Session:
    """
    :param db: SQLAlchemy session for the Postgres DB
    :param query_file_path: file path pointing to the `.sql` file
     that contains the query to seed the data in the DB. e.g.,
     `./docker/sample_data/postgres_example.sql`

    Using the provided sesion, creates the database, dropping it if it
    already existed. Seeds the created database using the query found
    in the  relative path provided. Some processing is done on the query
    text so that it can be executed properly.
    """
    if database_exists(db.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(db.bind.url)
    create_database(db.bind.url)
    with open(query_file_path, "r") as query_file:
        lines = query_file.read().splitlines()
        filtered = [line for line in lines if not line.startswith("--")]
        queries = " ".join(filtered).split(";")
        [db.execute(f"{text(query.strip())};") for query in queries if query]
    return db


def setup():
    """
    Set up the Timescale Database for testing - setup is identical to Postgres
    The query file must have each query on a separate line.
    Initial connection must be done to the master database.
    """
    uri = TimescaleConnector(
        ConnectionConfig(
            **{
                "name": str(uuid4()),
                "key": "my_timescale_db_1",
                "connection_type": ConnectionType.timescale,
                "access": AccessLevel.write,
                "secrets": {
                    "host": pydash.get(integration_config, "timescale_example.server"),
                    "port": pydash.get(integration_config, "timescale_example.port"),
                    "dbname": pydash.get(integration_config, "timescale_example.db"),
                    "username": pydash.get(
                        integration_config, "timescale_example.user"
                    ),
                    "password": pydash.get(
                        integration_config, "timescale_example.password"
                    ),
                },
            },
        )
    ).build_uri()

    engine = get_db_engine(database_uri=uri)
    SessionLocal = get_db_session(
        config=CONFIG,
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
    session = SessionLocal()

    seed_postgres_data(session, "./docker/sample_data/timescale_example.sql")


if __name__ == "__main__":
    setup()

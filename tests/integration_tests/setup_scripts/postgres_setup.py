from uuid import uuid4

import pydash
import sqlalchemy
from fideslib.core.config import load_toml
from fideslib.db.session import get_db_engine, get_db_session
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from fidesops.core.config import config
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.service.connectors.sql_connector import PostgreSQLConnector

integration_config = load_toml(["fidesops-integration.toml"])


def setup():
    """
    Set up the Postgres Database for testing.
    The query file must have each query on a separate line.
    Initial connection must be done to the master database.
    """
    uri = PostgreSQLConnector(
        ConnectionConfig(
            **{
                "name": str(uuid4()),
                "key": "my_postgres_db_1",
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.write,
                "secrets": {
                    "host": pydash.get(integration_config, "postgres_example.SERVER"),
                    "port": pydash.get(integration_config, "postgres_example.PORT"),
                    "dbname": pydash.get(integration_config, "postgres_example.DB"),
                    "username": pydash.get(integration_config, "postgres_example.USER"),
                    "password": pydash.get(
                        integration_config, "postgres_example.PASSWORD"
                    ),
                },
            },
        )
    ).build_uri()

    engine = get_db_engine(database_uri=uri)
    SessionLocal = get_db_session(
        config=config,
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
    session = SessionLocal()

    if database_exists(session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(session.bind.url)
    create_database(session.bind.url)

    with open("./docker/sample_data/postgres_example.sql", "r") as query_file:
        lines = query_file.read().splitlines()
        filtered = [line for line in lines if not line.startswith("--")]
        queries = " ".join(filtered).split(";")
        [
            session.execute(f"{sqlalchemy.text(query.strip())};")
            for query in queries
            if query
        ]


if __name__ == "__main__":
    setup()

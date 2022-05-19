from os import truncate
from uuid import uuid4

import pydash
import sqlalchemy

from fidesops.core.config import load_toml
from fidesops.db.session import get_db_engine, get_db_session
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.service.connectors.sql_connector import MariaDBConnector

integration_config = load_toml("fidesops-integration.toml")


def truncate_tables(db_session):
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


def setup():
    """
    Set up the MariaDB Database for testing.
    The query file must have each query on a separate line.
    Initial connection must be done to the master database.
    """
    uri = MariaDBConnector(
        ConnectionConfig(
            **{
                "name": str(uuid4()),
                "key": "my_mariadb_db_1",
                "connection_type": ConnectionType.mariadb,
                "access": AccessLevel.write,
                "secrets": {
                    "host": pydash.get(integration_config, "mariadb_example.SERVER"),
                    "port": pydash.get(integration_config, "mariadb_example.PORT"),
                    "dbname": pydash.get(integration_config, "mariadb_example.DB"),
                    "username": pydash.get(integration_config, "mariadb_example.USER"),
                    "password": pydash.get(
                        integration_config, "mariadb_example.PASSWORD"
                    ),
                },
            },
        )
    ).build_uri()

    engine = get_db_engine(database_uri=uri)
    SessionLocal = get_db_session(
        engine=engine,
        autocommit=True,
        autoflush=True,
    )
    session = SessionLocal()

    truncate_tables(session)

    with open("./data/sql/mariadb_example_data.sql", "r") as query_file:
        lines = query_file.read().splitlines()
        filtered = [line for line in lines if not line.startswith("--")]
        queries = " ".join(filtered).split(";")
        for query in queries:
            if query:
                session.execute(f"{sqlalchemy.text(query.strip())};")


if __name__ == "__main__":
    setup()

from uuid import uuid4

import pydash
import sqlalchemy
from toml import load as load_toml

from fides.api.db.session import get_db_engine, get_db_session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.privacy_experience import PrivacyExperienceConfig
from fides.api.service.connectors.sql_connector import MariaDBConnector
from fides.config import CONFIG

integration_config = load_toml("tests/ops/integration_test_config.toml")


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
                    "host": pydash.get(integration_config, "mariadb_example.server"),
                    "port": pydash.get(integration_config, "mariadb_example.port"),
                    "dbname": pydash.get(integration_config, "mariadb_example.db"),
                    "username": pydash.get(integration_config, "mariadb_example.user"),
                    "password": pydash.get(
                        integration_config, "mariadb_example.password"
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

    truncate_tables(session)

    with open("./docker/sample_data/mariadb_example_data.sql", "r") as query_file:
        lines = query_file.read().splitlines()
        filtered = [line for line in lines if not line.startswith("--")]
        queries = " ".join(filtered).split(";")
        for query in queries:
            if query:
                session.execute(f"{sqlalchemy.text(query.strip())};")


if __name__ == "__main__":
    setup()

from uuid import uuid4

import pydash
from fideslib.core.config import load_toml
from fideslib.db.session import get_db_engine, get_db_session

from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.service.connectors.sql_connector import PostgreSQLConnector
from fides.ctl.core.config import get_config
from tests.ops.test_helpers.db_utils import seed_postgres_data

CONFIG = get_config()
integration_config = load_toml(["tests/ops/integration_test_config.toml"])


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
                    "host": pydash.get(integration_config, "postgres_example.server"),
                    "port": pydash.get(integration_config, "postgres_example.port"),
                    "dbname": pydash.get(integration_config, "postgres_example.db"),
                    "username": pydash.get(integration_config, "postgres_example.user"),
                    "password": pydash.get(
                        integration_config, "postgres_example.password"
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

    seed_postgres_data(
        session.bind.url, "./src/fides/data/sample_project/postgres_sample.sql"
    )


if __name__ == "__main__":
    setup()

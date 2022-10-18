from uuid import uuid4

import pydash
from fideslib.core.config import load_toml
from fideslib.db.session import get_db_engine, get_db_session

from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.service.connectors import TimescaleConnector
from fides.ctl.core.config import get_config
from tests.ops.test_helpers.db_utils import seed_postgres_data

CONFIG = get_config()
integration_config = load_toml(["tests/ops/integration_test_config.toml"])


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

    seed_postgres_data(session.bind.url, "./docker/sample_data/timescale_example.sql")


if __name__ == "__main__":
    setup()

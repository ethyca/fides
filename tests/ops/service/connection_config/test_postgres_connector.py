from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.connectors import PostgreSQLConnector


def test_postgres_connector_build_uri(connection_config: ConnectionConfig, db: Session):
    connector = PostgreSQLConnector(configuration=connection_config)
    s = connection_config.secrets
    assert (
        connector.build_uri()
        == f"postgresql://{s['username']}:{s['password']}@{s['host']}:{s['port']}/{s['dbname']}"
    )

    connection_config.secrets = {
        "username": "postgres",
        "password": "postgres",
        "host": "host.docker.internal",
        "dbname": "postgres_example",
        "port": "6432",
    }
    connection_config.save(db)
    assert (
        connector.build_uri()
        == "postgresql://postgres:postgres@host.docker.internal:6432/postgres_example"
    )

    connection_config.secrets = {
        "username": "postgres",
        "password": "postgres",
        "host": "host.docker.internal",
        "dbname": "postgres_example",
    }
    connection_config.save(db)
    assert (
        connector.build_uri()
        == "postgresql://postgres:postgres@host.docker.internal:5432/postgres_example"
    )

    connection_config.secrets = {
        "username": "postgres",
        "host": "host.docker.internal",
        "dbname": "postgres_example",
    }
    connection_config.save(db)
    assert (
        connector.build_uri()
        == "postgresql://postgres@host.docker.internal:5432/postgres_example"
    )

    connection_config.secrets = {
        "host": "host.docker.internal",
        "dbname": "postgres_example",
    }
    assert (
        connector.build_uri()
        == "postgresql://host.docker.internal:5432/postgres_example"
    )

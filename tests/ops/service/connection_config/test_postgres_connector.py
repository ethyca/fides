from fidesops.ops.models.connectionconfig import ConnectionConfig
from fidesops.ops.service.connectors import PostgreSQLConnector
from sqlalchemy.orm import Session


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
        "port": "6432",
    }
    connection_config.save(db)
    assert (
        connector.build_uri()
        == "postgresql://postgres:postgres@host.docker.internal:6432"
    )

    connection_config.secrets = {
        "username": "postgres",
        "password": "postgres",
        "host": "host.docker.internal",
    }
    connection_config.save(db)
    assert (
        connector.build_uri() == "postgresql://postgres:postgres@host.docker.internal"
    )

    connection_config.secrets = {
        "username": "postgres",
        "host": "host.docker.internal",
    }
    connection_config.save(db)
    assert connector.build_uri() == "postgresql://postgres@host.docker.internal"

    connection_config.secrets = {
        "host": "host.docker.internal",
    }
    assert connector.build_uri() == "postgresql://host.docker.internal"

from sqlalchemy.orm import Session

from fidesops.service.connectors import PostgreSQLConnector


def test_postgres_connector_build_uri(connection_config, db: Session):
    connector = PostgreSQLConnector(configuration=connection_config)
    assert (
        connector.build_uri()
        == "postgresql://postgres:postgres@postgres_example/postgres_example"
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

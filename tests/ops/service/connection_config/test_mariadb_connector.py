from sqlalchemy.orm import Session

from fides.api.service.connectors.sql_connector import MariaDBConnector


def test_mariadb_connector_build_uri(connection_config_mariadb, db: Session):
    connector = MariaDBConnector(configuration=connection_config_mariadb)
    s = connection_config_mariadb.secrets
    port = s["port"] and f":{s['port']}" or ""
    uri = f"mariadb+pymysql://{s['username']}:{s['password']}@{s['host']}{port}/{s['dbname']}"
    assert connector.build_uri() == uri

    connection_config_mariadb.secrets = {
        "username": "mariadb_user",
        "password": "mariadb_pw",
        "host": "host.docker.internal",
        "dbname": "mariadb_example",
        "port": "3307",
    }
    connection_config_mariadb.save(db)
    assert (
        connector.build_uri()
        == "mariadb+pymysql://mariadb_user:mariadb_pw@host.docker.internal:3307/mariadb_example"
    )

    connection_config_mariadb.secrets = {
        "username": "mariadb_user",
        "password": "mariadb_pw",
        "host": "host.docker.internal",
        "dbname": "mariadb_example",
    }
    connection_config_mariadb.save(db)
    assert (
        connector.build_uri()
        == "mariadb+pymysql://mariadb_user:mariadb_pw@host.docker.internal:3306/mariadb_example"
    )

    connection_config_mariadb.secrets = {
        "username": "mariadb_user",
        "host": "host.docker.internal",
        "dbname": "mariadb_example",
    }
    connection_config_mariadb.save(db)
    assert (
        connector.build_uri()
        == "mariadb+pymysql://mariadb_user@host.docker.internal:3306/mariadb_example"
    )

    connection_config_mariadb.secrets = {
        "host": "host.docker.internal",
        "dbname": "mariadb_example",
    }
    assert (
        connector.build_uri()
        == "mariadb+pymysql://host.docker.internal:3306/mariadb_example"
    )

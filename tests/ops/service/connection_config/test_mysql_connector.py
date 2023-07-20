from sqlalchemy.orm import Session

from fides.api.service.connectors.sql_connector import MySQLConnector


def test_mysql_connector_build_uri(connection_config_mysql, db: Session):
    connector = MySQLConnector(configuration=connection_config_mysql)
    s = connection_config_mysql.secrets
    port = s["port"] and f":{s['port']}" or ""
    uri = f"mysql+pymysql://{s['username']}:{s['password']}@{s['host']}{port}/{s['dbname']}"
    assert connector.build_uri() == uri

    connection_config_mysql.secrets = {
        "username": "mysql_user",
        "password": "mysql_pw",
        "host": "host.docker.internal",
        "dbname": "mysql_example",
        "port": "3307",
    }
    connection_config_mysql.save(db)
    assert (
        connector.build_uri()
        == "mysql+pymysql://mysql_user:mysql_pw@host.docker.internal:3307/mysql_example"
    )

    connection_config_mysql.secrets = {
        "username": "mysql_user",
        "password": "mysql_pw",
        "host": "host.docker.internal",
        "dbname": "mysql_example",
    }
    connection_config_mysql.save(db)
    assert (
        connector.build_uri()
        == "mysql+pymysql://mysql_user:mysql_pw@host.docker.internal:3306/mysql_example"
    )

    connection_config_mysql.secrets = {
        "username": "mysql_user",
        "host": "host.docker.internal",
        "dbname": "mysql_example",
    }
    connection_config_mysql.save(db)
    assert (
        connector.build_uri()
        == "mysql+pymysql://mysql_user@host.docker.internal:3306/mysql_example"
    )

    connection_config_mysql.secrets = {
        "host": "host.docker.internal",
        "dbname": "mysql_example",
    }
    assert (
        connector.build_uri()
        == "mysql+pymysql://host.docker.internal:3306/mysql_example"
    )

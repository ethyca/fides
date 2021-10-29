from sqlalchemy.orm import Session

from fidesops.service.connectors.sql_connector import MySQLConnector


def test_mysql_connector_build_uri(connection_config_mysql, db: Session):
    connector = MySQLConnector(configuration=connection_config_mysql)
    assert (
        connector.build_uri()
        == "mysql+pymysql://mysql_user:mysql_pw@mysql_example/mysql_example"
    )

    connection_config_mysql.secrets = {
        "username": "mysql_user",
        "password": "mysql_pw",
        "host": "host.docker.internal",
    }
    connection_config_mysql.save(db)
    assert (
        connector.build_uri()
        == "mysql+pymysql://mysql_user:mysql_pw@host.docker.internal"
    )

    connection_config_mysql.secrets = {
        "username": "mysql_user",
        "password": "mysql_pw",
        "host": "host.docker.internal",
    }
    connection_config_mysql.save(db)
    assert (
        connector.build_uri()
        == "mysql+pymysql://mysql_user:mysql_pw@host.docker.internal"
    )

    connection_config_mysql.secrets = {
        "username": "mysql_user",
        "host": "host.docker.internal",
    }
    connection_config_mysql.save(db)
    assert connector.build_uri() == "mysql+pymysql://mysql_user@host.docker.internal"

    connection_config_mysql.secrets = {
        "host": "host.docker.internal",
    }
    assert connector.build_uri() == "mysql+pymysql://host.docker.internal"

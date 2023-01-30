import json

import pytest
from pymongo import MongoClient
from sqlalchemy.engine import Engine

from fides.api.ops.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    STORAGE_READ,
)
from fides.api.ops.api.v1.urn_registry import CONNECTIONS, V1_URL_PREFIX
from fides.api.ops.common_exceptions import ConnectionException
from fides.api.ops.models.connectionconfig import ConnectionTestStatus
from fides.api.ops.service.connectors import (
    MongoDBConnector,
    PostgreSQLConnector,
    SaaSConnector,
    get_connector,
)
from fides.api.ops.service.connectors.sql_connector import (
    MariaDBConnector,
    MicrosoftSQLServerConnector,
    MySQLConnector,
)


@pytest.mark.integration_postgres
@pytest.mark.integration
class TestPostgresConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, connection_config):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}/secret"

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_postgres_db_connection_incorrect_secrets(
        self,
        auth_header,
        api_client,
        db,
        connection_config,
        url,
    ):
        payload = {"host": "localhost", "port": "1234", "dbname": "my_test_db"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config.key}."
        )
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to postgres db." == body["failure_reason"]
        db.refresh(connection_config)

        assert connection_config.secrets == {
            "host": "localhost",
            "port": 1234,
            "dbname": "my_test_db",
            "username": None,
            "password": None,
            "url": None,
            "db_schema": None,
        }
        assert connection_config.last_test_timestamp is not None
        assert connection_config.last_test_succeeded is False

    @pytest.mark.usefixtures("postgres_integration_db")
    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_postgres_db_connection_connect_with_components(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config,
    ):
        payload = {
            "host": "postgres_example",
            "dbname": "postgres_example",
            "username": "postgres",
            "password": "postgres",
            "db_schema": None,
        }

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config.key}."
        )
        assert body["test_status"] == "succeeded"
        assert body["failure_reason"] is None
        db.refresh(connection_config)
        assert connection_config.secrets == {
            "host": "postgres_example",
            "port": None,
            "dbname": "postgres_example",
            "username": "postgres",
            "password": "postgres",
            "url": None,
            "db_schema": None,
        }
        assert connection_config.last_test_timestamp is not None
        assert connection_config.last_test_succeeded is True

    @pytest.mark.usefixtures("postgres_integration_db")
    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_postgres_db_connection_connect_with_url(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config,
    ):
        payload = {
            "url": "postgresql://postgres:postgres@postgres_example/postgres_example"
        }

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config)
        assert connection_config.secrets == {
            "host": None,
            "port": None,
            "dbname": None,
            "username": None,
            "password": None,
            "url": payload["url"],
            "db_schema": None,
        }
        assert connection_config.last_test_timestamp is not None
        assert connection_config.last_test_succeeded is True


@pytest.mark.integration_postgres
@pytest.mark.integration
class TestPostgresConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, connection_config):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client,
        db,
        connection_config,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 401
        db.refresh(connection_config)
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_connection_configuration_test_incorrect_scopes(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config,
    ):
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config)
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test_failed_response(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config,
    ):
        assert connection_config.last_test_timestamp is None
        connection_config.secrets = {"host": "invalid_host"}
        connection_config.save(db)

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        db.refresh(connection_config)
        assert connection_config.last_test_timestamp is not None
        assert connection_config.last_test_succeeded is False
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to postgres db." == body["failure_reason"]
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config.key}."
        )

    @pytest.mark.usefixtures("postgres_integration_db")
    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config,
    ):
        assert connection_config.last_test_timestamp is None

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config)
        assert connection_config.last_test_timestamp is not None
        assert connection_config.last_test_succeeded is True


@pytest.mark.integration_postgres
@pytest.mark.integration
class TestPostgresConnector:
    def test_postgres_db_connector(
        self,
        db,
        connection_config,
    ):
        connector = get_connector(connection_config)
        assert connector.__class__ == PostgreSQLConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        connection_config.secrets = {"host": "bad_host"}
        connection_config.save(db)
        connector = get_connector(connection_config)
        with pytest.raises(ConnectionException):
            connector.test_connection()


@pytest.mark.integration_mysql
@pytest.mark.integration
class TestMySQLConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, connection_config_mysql):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mysql.key}/secret"

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mysql_db_connection_incorrect_secrets(
        self,
        auth_header,
        api_client,
        db,
        connection_config_mysql,
        url,
    ):
        payload = {"host": "mysql_example", "port": 1234, "dbname": "my_test_db"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mysql.key}."
        )
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to mysql db." == body["failure_reason"]
        db.refresh(connection_config_mysql)

        assert connection_config_mysql.secrets == {
            "host": "mysql_example",
            "port": 1234,
            "dbname": "my_test_db",
            "username": None,
            "password": None,
            "url": None,
        }
        assert connection_config_mysql.last_test_timestamp is not None
        assert connection_config_mysql.last_test_succeeded is False

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mysql_db_connection_connect_with_components(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mysql,
    ):
        payload = {
            "host": "mysql_example",
            "dbname": "mysql_example",
            "username": "mysql_user",
            "password": "mysql_pw",
        }

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = resp.json()

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mysql.key}."
        )
        assert body["test_status"] == "succeeded"
        assert body["failure_reason"] is None
        db.refresh(connection_config_mysql)
        assert connection_config_mysql.secrets == {
            "host": "mysql_example",
            "dbname": "mysql_example",
            "username": "mysql_user",
            "password": "mysql_pw",
            "url": None,
            "port": None,
        }
        assert connection_config_mysql.last_test_timestamp is not None
        assert connection_config_mysql.last_test_succeeded is True

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mysql_db_connection_connect_with_url(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mysql,
    ):
        payload = {
            "url": "mysql+pymysql://mysql_user:mysql_pw@mysql_example/mysql_example"
        }

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mysql.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config_mysql)
        assert connection_config_mysql.secrets == {
            "host": None,
            "port": None,
            "dbname": None,
            "username": None,
            "password": None,
            "url": payload["url"],
        }
        assert connection_config_mysql.last_test_timestamp is not None
        assert connection_config_mysql.last_test_succeeded is True


@pytest.mark.integration_mysql
@pytest.mark.integration
class TestMySQLConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, connection_config_mysql):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mysql.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client,
        db,
        connection_config_mysql,
    ):
        assert connection_config_mysql.last_test_timestamp is None

        resp = api_client.get(url)
        assert resp.status_code == 401
        db.refresh(connection_config_mysql)
        assert connection_config_mysql.last_test_timestamp is None
        assert connection_config_mysql.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_connection_configuration_test_incorrect_scopes(
        self,
        auth_header,
        url,
        api_client,
        connection_config_mysql,
        db,
    ):
        assert connection_config_mysql.last_test_timestamp is None

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config_mysql)
        assert connection_config_mysql.last_test_timestamp is None
        assert connection_config_mysql.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test_failed_response(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mysql,
    ):
        assert connection_config_mysql.last_test_timestamp is None
        connection_config_mysql.secrets = {"host": "invalid_host"}
        connection_config_mysql.save(db)

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        db.refresh(connection_config_mysql)
        assert connection_config_mysql.last_test_timestamp is not None
        assert connection_config_mysql.last_test_succeeded is False
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to mysql db." == body["failure_reason"]
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_mysql.key}."
        )

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mysql,
    ):
        assert connection_config_mysql.last_test_timestamp is None

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_mysql.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config_mysql)
        assert connection_config_mysql.last_test_timestamp is not None
        assert connection_config_mysql.last_test_succeeded is True


@pytest.mark.integration_mysql
@pytest.mark.integration
class TestMySQLConnector:
    def test_mysql_db_connector(
        self,
        db,
        connection_config_mysql,
    ):
        connector = get_connector(connection_config_mysql)
        assert connector.__class__ == MySQLConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        connection_config_mysql.secrets = {"host": "bad_host"}
        connection_config_mysql.save(db)
        connector = get_connector(connection_config_mysql)
        with pytest.raises(ConnectionException):
            connector.test_connection()


@pytest.mark.integration_mariadb
@pytest.mark.integration
class TestMariaDBConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, connection_config_mariadb):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mariadb.key}/secret"

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mariadb_db_connection_incorrect_secrets(
        self,
        auth_header,
        api_client,
        db,
        connection_config_mariadb,
        url,
    ):
        payload = {"host": "mariadb_example", "port": 1234, "dbname": "my_test_db"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mariadb.key}."
        )
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to mariadb db." == body["failure_reason"]
        db.refresh(connection_config_mariadb)

        assert connection_config_mariadb.secrets == {
            "host": "mariadb_example",
            "port": 1234,
            "dbname": "my_test_db",
            "username": None,
            "password": None,
            "url": None,
        }
        assert connection_config_mariadb.last_test_timestamp is not None
        assert connection_config_mariadb.last_test_succeeded is False

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mariadb_db_connection_connect_with_components(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mariadb,
    ):
        payload = {
            "host": "mariadb_example",
            "dbname": "mariadb_example",
            "username": "mariadb_user",
            "password": "mariadb_pw",
        }

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = resp.json()

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mariadb.key}."
        )
        assert body["test_status"] == "succeeded"
        assert body["failure_reason"] is None
        db.refresh(connection_config_mariadb)
        assert connection_config_mariadb.secrets == {
            "host": "mariadb_example",
            "dbname": "mariadb_example",
            "username": "mariadb_user",
            "password": "mariadb_pw",
            "url": None,
            "port": None,
        }
        assert connection_config_mariadb.last_test_timestamp is not None
        assert connection_config_mariadb.last_test_succeeded is True

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mariadb_db_connection_connect_with_url(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mariadb,
    ):
        payload = {
            "url": "mariadb+pymysql://mariadb_user:mariadb_pw@mariadb_example/mariadb_example"
        }

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mariadb.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config_mariadb)
        assert connection_config_mariadb.secrets == {
            "host": None,
            "port": None,
            "dbname": None,
            "username": None,
            "password": None,
            "url": payload["url"],
        }
        assert connection_config_mariadb.last_test_timestamp is not None
        assert connection_config_mariadb.last_test_succeeded is True


@pytest.mark.integration_mariadb
@pytest.mark.integration
class TestMariaDBConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, connection_config_mariadb):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mariadb.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client,
        db,
        connection_config_mariadb,
    ):
        assert connection_config_mariadb.last_test_timestamp is None

        resp = api_client.get(url)
        assert resp.status_code == 401
        db.refresh(connection_config_mariadb)
        assert connection_config_mariadb.last_test_timestamp is None
        assert connection_config_mariadb.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_connection_configuration_test_incorrect_scopes(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mariadb,
    ):
        assert connection_config_mariadb.last_test_timestamp is None

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config_mariadb)
        assert connection_config_mariadb.last_test_timestamp is None
        assert connection_config_mariadb.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test_failed_response(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mariadb,
    ):
        assert connection_config_mariadb.last_test_timestamp is None
        connection_config_mariadb.secrets = {"host": "invalid_host"}
        connection_config_mariadb.save(db)

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        db.refresh(connection_config_mariadb)
        assert connection_config_mariadb.last_test_timestamp is not None
        assert connection_config_mariadb.last_test_succeeded is False
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to mariadb db." == body["failure_reason"]
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_mariadb.key}."
        )

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test(
        self,
        auth_header,
        url,
        api_client,
        db,
        connection_config_mariadb,
    ):
        assert connection_config_mariadb.last_test_timestamp is None

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_mariadb.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config_mariadb)
        assert connection_config_mariadb.last_test_timestamp is not None
        assert connection_config_mariadb.last_test_succeeded is True


@pytest.mark.integration_mariadb
@pytest.mark.integration
class TestMariaDBConnector:
    def test_mariadb_db_connector(
        self,
        db,
        connection_config_mariadb,
    ):
        connector = get_connector(connection_config_mariadb)
        assert connector.__class__ == MariaDBConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        connection_config_mariadb.secrets = {"host": "bad_host"}
        connection_config_mariadb.save(db)
        connector = get_connector(connection_config_mariadb)
        with pytest.raises(ConnectionException):
            connector.test_connection()


@pytest.mark.integration_mssql
@pytest.mark.integration
class TestMicrosoftSQLServerConnection:
    @pytest.fixture(scope="function")
    def url_put_secret(self, connection_config_mssql):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mssql.key}/secret"

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mssql_db_connection_incorrect_secrets(
        self,
        auth_header,
        api_client,
        db,
        connection_config_mssql,
        url_put_secret,
    ):
        payload = {
            "username": "sa",
            "password": "incorrect",
            "host": "mssql_example",
            "port": 1433,
            "dbname": "mssql_example",
            "url": None,
        }
        resp = api_client.put(
            url_put_secret,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mssql.key}."
        )
        assert body["test_status"] == "failed"
        assert "Connection error." == body["failure_reason"]
        db.refresh(connection_config_mssql)

        assert connection_config_mssql.secrets == {
            "username": "sa",
            "password": "incorrect",
            "host": "mssql_example",
            "port": 1433,
            "dbname": "mssql_example",
            "url": None,
        }
        assert connection_config_mssql.last_test_timestamp is not None
        assert connection_config_mssql.last_test_succeeded is False

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mssql_db_connection_connect_with_components(
        self,
        auth_header,
        url_put_secret,
        api_client,
        db,
        connection_config_mssql,
    ):
        payload = {
            "username": "sa",
            "password": "Mssql_pw1",
            "host": "mssql_example",
            "port": 1433,
            "dbname": "mssql_example",
        }

        resp = api_client.put(
            url_put_secret,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = resp.json()

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mssql.key}."
        )
        assert body["test_status"] == "succeeded"
        assert body["failure_reason"] is None
        db.refresh(connection_config_mssql)
        assert connection_config_mssql.secrets == {
            "username": "sa",
            "password": "Mssql_pw1",
            "host": "mssql_example",
            "port": 1433,
            "dbname": "mssql_example",
            "url": None,
        }
        assert connection_config_mssql.last_test_timestamp is not None
        assert connection_config_mssql.last_test_succeeded is True

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mssql_db_connection_connect_with_url(
        self,
        auth_header,
        url_put_secret,
        api_client,
        db,
        connection_config_mssql,
    ):
        payload = {
            "url": "mssql+pyodbc://sa:Mssql_pw1@mssql_example:1433/mssql_example?driver=ODBC+Driver+17+for+SQL+Server"
        }

        resp = api_client.put(
            url_put_secret,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mssql.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config_mssql)
        assert connection_config_mssql.secrets == {
            "username": None,
            "password": None,
            "host": None,
            "port": None,
            "dbname": None,
            "url": payload["url"],
        }
        assert connection_config_mssql.last_test_timestamp is not None
        assert connection_config_mssql.last_test_succeeded is True

    @pytest.fixture(scope="function")
    def url_test_secrets(self, connection_config_mssql):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mssql.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url_test_secrets,
        api_client,
        db,
        connection_config_mssql,
    ):
        resp = api_client.get(url_test_secrets)
        assert resp.status_code == 401
        db.refresh(connection_config_mssql)
        assert connection_config_mssql.last_test_timestamp is None
        assert connection_config_mssql.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_connection_configuration_test_incorrect_scopes(
        self,
        auth_header,
        url_test_secrets,
        api_client,
        db,
        connection_config_mssql,
    ):
        resp = api_client.get(
            url_test_secrets,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config_mssql)
        assert connection_config_mssql.last_test_timestamp is None
        assert connection_config_mssql.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test_failed_response(
        self,
        auth_header,
        url_test_secrets,
        api_client,
        db,
        connection_config_mssql,
    ):
        connection_config_mssql.secrets = {"host": "invalid_host"}
        connection_config_mssql.save(db)

        resp = api_client.get(
            url_test_secrets,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        db.refresh(connection_config_mssql)
        assert connection_config_mssql.last_test_timestamp is not None
        assert connection_config_mssql.last_test_succeeded is False
        assert body["test_status"] == "failed"
        assert "Connection error." == body["failure_reason"]
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_mssql.key}."
        )

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test(
        self,
        auth_header,
        url_test_secrets,
        api_client,
        db,
        connection_config_mssql,
    ):
        resp = api_client.get(
            url_test_secrets,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_mssql.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config_mssql)
        assert connection_config_mssql.last_test_timestamp is not None
        assert connection_config_mssql.last_test_succeeded is True

    def test_mssql_db_connector(
        self,
        db,
        connection_config_mssql,
    ):
        connector = get_connector(connection_config_mssql)
        assert connector.__class__ == MicrosoftSQLServerConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        connection_config_mssql.secrets = {"host": "bad_host"}
        connection_config_mssql.save(db)
        connector = get_connector(connection_config_mssql)
        with pytest.raises(ConnectionException):
            connector.test_connection()


@pytest.mark.integration_mongodb
@pytest.mark.integration
class TestMongoConnector:
    def test_mongo_db_connector(
        self,
        db,
        mongo_connection_config,
    ):
        connector = get_connector(mongo_connection_config)
        assert connector.__class__ == MongoDBConnector

        client = connector.client()
        assert client.__class__ == MongoClient
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        mongo_connection_config.secrets = {"host": "bad_host"}
        mongo_connection_config.save(db)
        connector = get_connector(mongo_connection_config)
        with pytest.raises(ConnectionException):
            connector.test_connection()


@pytest.mark.integration_mongodb
@pytest.mark.integration
class TestMongoConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, mongo_connection_config):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{mongo_connection_config.key}/secret"

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mongo_db_connection_incorrect_secrets(
        self,
        auth_header,
        url,
        api_client,
        db,
        mongo_connection_config,
    ):
        payload = {"host": "incorrect_host", "port": "1234"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {mongo_connection_config.key}."
        )
        assert body["test_status"] == "failed"
        assert (
            "Server Selection Timeout Error connecting to MongoDB."
            == body["failure_reason"]
        )
        db.refresh(mongo_connection_config)

        assert mongo_connection_config.secrets == {
            "host": "incorrect_host",
            "port": 1234,
            "username": None,
            "password": None,
            "defaultauthdb": None,
            "url": None,
        }
        assert mongo_connection_config.last_test_timestamp is not None
        assert mongo_connection_config.last_test_succeeded is False

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mongo_db_connection_connect_with_components(
        self,
        auth_header,
        url,
        api_client,
        db,
        mongo_connection_config,
    ):
        payload = {
            "host": "mongodb_example",
            "defaultauthdb": "mongo_test",
            "username": "mongo_user",
            "password": "mongo_pass",
        }

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {mongo_connection_config.key}."
        )
        assert body["test_status"] == "succeeded"
        assert body["failure_reason"] is None
        db.refresh(mongo_connection_config)
        assert mongo_connection_config.secrets == {
            "host": "mongodb_example",
            "defaultauthdb": "mongo_test",
            "username": "mongo_user",
            "password": "mongo_pass",
            "url": None,
            "port": None,
        }
        assert mongo_connection_config.last_test_timestamp is not None
        assert mongo_connection_config.last_test_succeeded is True

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_mongo_db_connection_connect_with_url(
        self,
        auth_header,
        url,
        api_client,
        db,
        mongo_connection_config,
    ):
        payload = {"url": "mongodb://mongo_user:mongo_pass@mongodb_example/mongo_test"}

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {mongo_connection_config.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(mongo_connection_config)
        assert mongo_connection_config.secrets == {
            "host": None,
            "port": None,
            "defaultauthdb": None,
            "username": None,
            "password": None,
            "url": payload["url"],
        }

        assert mongo_connection_config.last_test_timestamp is not None
        assert mongo_connection_config.last_test_succeeded is True


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
class TestSaaSConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, mailchimp_connection_config):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{mailchimp_connection_config.key}/secret"

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_saas_connection_incorrect_secrets(
        self,
        auth_header,
        api_client,
        db,
        mailchimp_connection_config,
        url,
    ):
        payload = {"domain": "can", "username": "someone", "api_key": "letmein"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200

        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {mailchimp_connection_config.key}."
        )
        assert body["test_status"] == "failed"
        assert (
            f"Operational Error connecting to '{mailchimp_connection_config.key}'"
            in body["failure_reason"]
        )

        db.refresh(mailchimp_connection_config)
        assert mailchimp_connection_config.secrets == {
            "domain": "can",
            "username": "someone",
            "api_key": "letmein",
        }
        assert mailchimp_connection_config.last_test_timestamp is not None
        assert mailchimp_connection_config.last_test_succeeded is False

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_saas_connection_connect_with_components(
        self,
        auth_header,
        url,
        api_client,
        db,
        mailchimp_connection_config,
    ):
        payload = mailchimp_connection_config.secrets
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200

        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {mailchimp_connection_config.key}."
        )
        assert body["test_status"] == "succeeded"
        assert body["failure_reason"] is None

        db.refresh(mailchimp_connection_config)
        assert mailchimp_connection_config.secrets == payload
        assert mailchimp_connection_config.last_test_timestamp is not None
        assert mailchimp_connection_config.last_test_succeeded is True

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_saas_connection_connect_missing_secrets(
        self,
        auth_header,
        url,
        api_client,
        saas_example_secrets,
    ):
        payload = {
            "domain": saas_example_secrets["domain"],
            "username": saas_example_secrets["username"],
        }
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422

        body = json.loads(resp.text)
        assert body["detail"][0]["msg"] == "field required"

    @pytest.mark.parametrize(
        "auth_header", [[CONNECTION_CREATE_OR_UPDATE]], indirect=True
    )
    def test_saas_connection_connect_with_extra_secrets(
        self,
        auth_header,
        url,
        api_client,
        mailchimp_connection_config,
    ):
        payload = {**mailchimp_connection_config.secrets, "extra": "junk"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422

        body = json.loads(resp.text)
        assert body["detail"][0]["msg"] == "extra fields not permitted"


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
class TestSaaSConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(
        self,
        mailchimp_connection_config,
    ):
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{mailchimp_connection_config.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client,
        db,
        mailchimp_connection_config,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 401

        db.refresh(mailchimp_connection_config)
        assert mailchimp_connection_config.last_test_timestamp is None
        assert mailchimp_connection_config.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[STORAGE_READ]], indirect=True)
    def test_connection_configuration_test_incorrect_scopes(
        self,
        auth_header,
        url,
        api_client,
        db,
        mailchimp_connection_config,
    ):
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

        db.refresh(mailchimp_connection_config)
        assert mailchimp_connection_config.last_test_timestamp is None
        assert mailchimp_connection_config.last_test_succeeded is None

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test_failed_response(
        self,
        auth_header,
        url,
        api_client,
        db,
        mailchimp_connection_config,
    ):
        mailchimp_connection_config.secrets = {"domain": "invalid_domain"}
        mailchimp_connection_config.save(db)
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200

        body = json.loads(resp.text)
        assert body["test_status"] == "failed"
        assert (
            f"Operational Error connecting to '{mailchimp_connection_config.key}'"
            in body["failure_reason"]
        )
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {mailchimp_connection_config.key}."
        )

        db.refresh(mailchimp_connection_config)
        assert mailchimp_connection_config.last_test_timestamp is not None
        assert mailchimp_connection_config.last_test_succeeded is False

    @pytest.mark.parametrize("auth_header", [[CONNECTION_READ]], indirect=True)
    def test_connection_configuration_test(
        self,
        auth_header,
        url,
        api_client,
        db,
        mailchimp_connection_config,
    ):
        assert mailchimp_connection_config.last_test_timestamp is None

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200

        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {mailchimp_connection_config.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"

        db.refresh(mailchimp_connection_config)
        assert mailchimp_connection_config.last_test_timestamp is not None
        assert mailchimp_connection_config.last_test_succeeded is True


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
class TestSaasConnectorIntegration:
    def test_saas_connector(self, db, mailchimp_connection_config):
        connector = get_connector(mailchimp_connection_config)
        assert connector.__class__ == SaaSConnector

        # We can't create a saas connector client outside the context of a request
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        mailchimp_connection_config.secrets = {"domain": "bad_host"}
        mailchimp_connection_config.save(db)
        connector = get_connector(mailchimp_connection_config)
        with pytest.raises(ConnectionException):
            connector.test_connection()

import json
from typing import Type

import pytest
from botocore.client import BaseClient
from pymongo import MongoClient
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.common_exceptions import ConnectionException
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.service.connectors import (
    MongoDBConnector,
    PostgreSQLConnector,
    RDSMySQLConnector,
    SaaSConnector,
    ScyllaConnector,
    get_connector,
)
from fides.api.service.connectors.sql_connector import (
    MariaDBConnector,
    MicrosoftSQLServerConnector,
    MySQLConnector,
)
from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    STORAGE_READ,
)
from fides.common.api.v1.urn_registry import CONNECTIONS, V1_URL_PREFIX


@pytest.mark.integration_postgres
@pytest.mark.integration
class TestPostgresConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy, connection_config) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}/secret"

    def test_postgres_db_connection_incorrect_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
        url,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
            "db_schema": None,
            "ssh_required": False,
        }
        assert connection_config.last_test_timestamp is not None
        assert connection_config.last_test_succeeded is False

    def test_postgres_db_connection_connect_with_components(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
        postgres_integration_db,
    ) -> None:
        payload = {
            "host": "postgres_example",
            "dbname": "postgres_example",
            "username": "postgres",
            "password": "postgres",
            "db_schema": None,
        }

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
            "port": 5432,
            "dbname": "postgres_example",
            "username": "postgres",
            "password": "postgres",
            "db_schema": None,
            "ssh_required": False,
        }
        assert connection_config.last_test_timestamp is not None
        assert connection_config.last_test_succeeded is True


@pytest.mark.integration_postgres
@pytest.mark.integration
class TestPostgresConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy, connection_config) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
    ) -> None:
        assert connection_config.last_test_timestamp is None

        resp = api_client.get(url)
        assert resp.status_code == 401
        db.refresh(connection_config)
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

    def test_connection_configuration_test_incorrect_scopes(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
    ) -> None:
        assert connection_config.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config)
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

    def test_connection_configuration_test_failed_response(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
    ) -> None:
        assert connection_config.last_test_timestamp is None
        connection_config.secrets = {
            "host": "invalid_host",
            "dbname": "postgres_example",
        }
        connection_config.save(db)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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

    def test_connection_configuration_test(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
        postgres_integration_db,
    ) -> None:
        assert connection_config.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
        postgres_integration_db,
        postgres_example_secrets,
    ) -> None:
        connector = get_connector(connection_config)
        assert connector.__class__ == PostgreSQLConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        connection_config.secrets = {
            "url": str(
                URL.create(
                    "postgresql",
                    username=postgres_example_secrets["username"],
                    password=postgres_example_secrets["password"],
                    host=postgres_example_secrets["host"],
                    database=postgres_example_secrets["dbname"],
                )
            )
        }
        connection_config.save(db)
        connector = get_connector(connection_config)
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
    def url(self, connection_config_mysql) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mysql.key}/secret"

    def test_mysql_db_connection_incorrect_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mysql,
        url,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
            "ssh_required": False,
        }
        assert connection_config_mysql.last_test_timestamp is not None
        assert connection_config_mysql.last_test_succeeded is False

    def test_mysql_db_connection_connect_with_components(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mysql,
    ) -> None:
        payload = {
            "host": "mysql_example",
            "dbname": "mysql_example",
            "username": "mysql_user",
            "password": "mysql_pw",
        }

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
            "port": 3306,
            "ssh_required": False,
        }
        assert connection_config_mysql.last_test_timestamp is not None
        assert connection_config_mysql.last_test_succeeded is True


@pytest.mark.integration_mysql
@pytest.mark.integration
class TestMySQLConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, connection_config_mysql) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mysql.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client: TestClient,
        db: Session,
        connection_config_mysql,
    ) -> None:
        assert connection_config_mysql.last_test_timestamp is None

        resp = api_client.get(url)
        assert resp.status_code == 401
        db.refresh(connection_config_mysql)
        assert connection_config_mysql.last_test_timestamp is None
        assert connection_config_mysql.last_test_succeeded is None

    def test_connection_configuration_test_incorrect_scopes(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mysql,
    ) -> None:
        assert connection_config_mysql.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config_mysql)
        assert connection_config_mysql.last_test_timestamp is None
        assert connection_config_mysql.last_test_succeeded is None

    def test_connection_configuration_test_failed_response(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mysql,
    ) -> None:
        assert connection_config_mysql.last_test_timestamp is None
        connection_config_mysql.secrets = {
            "host": "invalid_host",
            "dbname": "mysql_example",
        }
        connection_config_mysql.save(db)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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

    def test_connection_configuration_test(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mysql,
    ) -> None:
        assert connection_config_mysql.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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
        db: Session,
        connection_config_mysql,
        mysql_example_secrets,
    ) -> None:
        connector = get_connector(connection_config_mysql)
        assert connector.__class__ == MySQLConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        connection_config_mysql.secrets = {
            "url": str(
                URL.create(
                    "mysql+pymysql",
                    username=mysql_example_secrets["username"],
                    password=mysql_example_secrets["password"],
                    host=mysql_example_secrets["host"],
                    database=mysql_example_secrets["dbname"],
                )
            )
        }
        connection_config_mysql.save(db)
        connector = get_connector(connection_config_mysql)
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
    def url(self, oauth_client, policy, connection_config_mariadb) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mariadb.key}/secret"

    def test_mariadb_db_connection_incorrect_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mariadb,
        url,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
        }
        assert connection_config_mariadb.last_test_timestamp is not None
        assert connection_config_mariadb.last_test_succeeded is False

    def test_mariadb_db_connection_connect_with_components(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mariadb,
    ) -> None:
        payload = {
            "host": "mariadb_example",
            "dbname": "mariadb_example",
            "username": "mariadb_user",
            "password": "mariadb_pw",
        }

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
            "port": 3306,
        }
        assert connection_config_mariadb.last_test_timestamp is not None
        assert connection_config_mariadb.last_test_succeeded is True


@pytest.mark.integration_mariadb
@pytest.mark.integration
class TestMariaDBConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, oauth_client, policy, connection_config_mariadb) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mariadb.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mariadb,
    ) -> None:
        assert connection_config_mariadb.last_test_timestamp is None

        resp = api_client.get(url)
        assert resp.status_code == 401
        db.refresh(connection_config_mariadb)
        assert connection_config_mariadb.last_test_timestamp is None
        assert connection_config_mariadb.last_test_succeeded is None

    def test_connection_configuration_test_incorrect_scopes(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mariadb,
    ) -> None:
        assert connection_config_mariadb.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config_mariadb)
        assert connection_config_mariadb.last_test_timestamp is None
        assert connection_config_mariadb.last_test_succeeded is None

    def test_connection_configuration_test_failed_response(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mariadb,
    ) -> None:
        assert connection_config_mariadb.last_test_timestamp is None
        connection_config_mariadb.secrets = {
            "host": "invalid_host",
            "dbname": "mariadb_example",
        }
        connection_config_mariadb.save(db)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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

    def test_connection_configuration_test(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mariadb,
    ) -> None:
        assert connection_config_mariadb.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mariadb,
        mariadb_example_secrets,
    ) -> None:
        connector = get_connector(connection_config_mariadb)
        assert connector.__class__ == MariaDBConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        connection_config_mariadb.secrets = {
            "url": str(
                URL.create(
                    "mariadb+pymysql",
                    username=mariadb_example_secrets["username"],
                    password=mariadb_example_secrets["password"],
                    host=mariadb_example_secrets["host"],
                    database=mariadb_example_secrets["dbname"],
                )
            )
        }
        connection_config_mariadb.save(db)
        connector = get_connector(connection_config_mariadb)
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
    def url_put_secret(self, oauth_client, policy, connection_config_mssql) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mssql.key}/secret"

    def test_mssql_db_connection_incorrect_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mssql,
        url_put_secret,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "username": "sa",
            "password": "incorrect",
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
        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config_mssql.key}."
        )
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to mssql db." == body["failure_reason"]
        db.refresh(connection_config_mssql)

        assert connection_config_mssql.secrets == {
            "username": "sa",
            "password": "incorrect",
            "host": "mssql_example",
            "port": 1433,
            "dbname": "mssql_example",
        }
        assert connection_config_mssql.last_test_timestamp is not None
        assert connection_config_mssql.last_test_succeeded is False

    def test_mssql_db_connection_connect_with_components(
        self,
        url_put_secret,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mssql,
    ) -> None:
        payload = {
            "username": "sa",
            "password": "Mssql_pw1",
            "host": "mssql_example",
            "port": 1433,
            "dbname": "mssql_example",
        }

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
        }
        assert connection_config_mssql.last_test_timestamp is not None
        assert connection_config_mssql.last_test_succeeded is True

    @pytest.fixture(scope="function")
    def url_test_secrets(self, oauth_client, policy, connection_config_mssql) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_mssql.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url_test_secrets,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mssql,
    ) -> None:
        assert connection_config_mssql.last_test_timestamp is None

        resp = api_client.get(url_test_secrets)
        assert resp.status_code == 401
        db.refresh(connection_config_mssql)
        assert connection_config_mssql.last_test_timestamp is None
        assert connection_config_mssql.last_test_succeeded is None

    def test_connection_configuration_test_incorrect_scopes(
        self,
        url_test_secrets,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mssql,
    ) -> None:
        assert connection_config_mssql.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[STORAGE_READ])
        resp = api_client.get(
            url_test_secrets,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config_mssql)
        assert connection_config_mssql.last_test_timestamp is None
        assert connection_config_mssql.last_test_succeeded is None

    def test_connection_configuration_test_failed_response(
        self,
        url_test_secrets,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mssql,
    ) -> None:
        assert connection_config_mssql.last_test_timestamp is None
        connection_config_mssql.secrets = {
            "host": "invalid_host",
            "username": "sa",
            "password": "Mssql_pw1",
            "dbname": "mssql_example",
        }
        connection_config_mssql.save(db)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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
        assert "Operational Error connecting to mssql db." == body["failure_reason"]
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_mssql.key}."
        )

    def test_connection_configuration_test(
        self,
        url_test_secrets,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mssql,
    ) -> None:
        assert connection_config_mssql.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_mssql,
        mssql_example_secrets,
    ) -> None:
        connector = get_connector(connection_config_mssql)
        assert connector.__class__ == MicrosoftSQLServerConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        connection_config_mssql.secrets = {
            "url": str(
                URL.create(
                    "mssql+pymssql",
                    username=mssql_example_secrets["username"],
                    password=mssql_example_secrets["password"],
                    host=mssql_example_secrets["host"],
                    database=mssql_example_secrets["dbname"],
                )
            )
        }
        connection_config_mssql.save(db)
        connector = get_connector(connection_config_mssql)
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
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mongo_connection_config,
        mongo_example_secrets,
    ) -> None:
        connector = get_connector(mongo_connection_config)
        assert connector.__class__ == MongoDBConnector

        client = connector.client()
        assert client.__class__ == MongoClient
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        mongo_connection_config.secrets = {
            "url": str(
                URL.create(
                    "mongodb",
                    username=mongo_example_secrets["username"],
                    password=mongo_example_secrets["password"],
                    host=mongo_example_secrets["host"],
                    database=mongo_example_secrets["defaultauthdb"],
                )
            )
        }
        mongo_connection_config.save(db)
        connector = get_connector(mongo_connection_config)
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        mongo_connection_config.secrets = {
            "host": "bad_host",
            "username": "mongo_user",
            "password": "mongo_pass",
            "defaultauthdb": "mongo_test",
        }
        mongo_connection_config.save(db)
        connector = get_connector(mongo_connection_config)
        with pytest.raises(ConnectionException):
            connector.test_connection()


@pytest.mark.integration_mongodb
@pytest.mark.integration
class TestMongoConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy, mongo_connection_config) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{mongo_connection_config.key}/secret"

    def test_mongo_db_connection_incorrect_secrets(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mongo_connection_config,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "host": "incorrect_host",
            "port": 1234,
            "username": "mongo_user",
            "password": "mongo_pass",
            "defaultauthdb": "mongo_test",
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
        assert body["test_status"] == "failed"
        assert (
            "Server Selection Timeout Error connecting to MongoDB."
            == body["failure_reason"]
        )
        db.refresh(mongo_connection_config)

        assert mongo_connection_config.secrets == {
            "host": "incorrect_host",
            "port": 1234,
            "username": "mongo_user",
            "password": "mongo_pass",
            "defaultauthdb": "mongo_test",
        }
        assert mongo_connection_config.last_test_timestamp is not None
        assert mongo_connection_config.last_test_succeeded is False

    def test_mongo_db_connection_connect_with_components(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mongo_connection_config,
    ) -> None:
        payload = {
            "host": "mongodb_example",
            "defaultauthdb": "mongo_test",
            "username": "mongo_user",
            "password": "mongo_pass",
        }

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
            "port": 27017,
        }
        assert mongo_connection_config.last_test_timestamp is not None
        assert mongo_connection_config.last_test_succeeded is True


@pytest.mark.integration_saas
class TestSaaSConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(
        self, oauth_client: ClientDetail, policy, mailchimp_connection_config
    ) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{mailchimp_connection_config.key}/secret"

    def test_saas_connection_incorrect_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mailchimp_connection_config,
        url,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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

    def test_saas_connection_connect_with_components(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mailchimp_connection_config,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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

    def test_saas_connection_connect_missing_secrets(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        saas_example_secrets,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
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
        assert (
            body["detail"][0]["msg"]
            == "Value error, mailchimp_schema must be supplied all of: [domain, username, api_key]."
        )

    def test_saas_connection_connect_with_extra_secrets(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        mailchimp_connection_config,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        # extra fields should be ignored
        payload = {**mailchimp_connection_config.secrets, "extra": "junk"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200


@pytest.mark.integration_saas
class TestSaaSConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(
        self,
        oauth_client: ClientDetail,
        policy,
        mailchimp_connection_config,
        mailchimp_dataset_config,
    ) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{mailchimp_connection_config.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mailchimp_connection_config,
    ):
        assert mailchimp_connection_config.last_test_timestamp is None

        resp = api_client.get(url)
        assert resp.status_code == 401

        db.refresh(mailchimp_connection_config)
        assert mailchimp_connection_config.last_test_timestamp is None
        assert mailchimp_connection_config.last_test_succeeded is None

    def test_connection_configuration_test_incorrect_scopes(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mailchimp_connection_config,
    ):
        assert mailchimp_connection_config.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

        db.refresh(mailchimp_connection_config)
        assert mailchimp_connection_config.last_test_timestamp is None
        assert mailchimp_connection_config.last_test_succeeded is None

    def test_connection_configuration_test_failed_response(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mailchimp_connection_config,
    ):
        assert mailchimp_connection_config.last_test_timestamp is None

        mailchimp_connection_config.secrets = {"domain": "invalid_domain"}
        mailchimp_connection_config.save(db)
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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

    def test_connection_configuration_test(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        mailchimp_connection_config,
    ):
        assert mailchimp_connection_config.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
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
class TestSaasConnectorIntegration:
    def test_saas_connector(
        self, db: Session, mailchimp_connection_config, mailchimp_dataset_config
    ):
        connector = get_connector(mailchimp_connection_config)
        assert connector.__class__ == SaaSConnector

        # We can't create a saas connector client outside the context of a request
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        mailchimp_connection_config.secrets = {"domain": "bad_host"}
        mailchimp_connection_config.save(db)
        connector = get_connector(mailchimp_connection_config)
        with pytest.raises(ConnectionException):
            connector.test_connection()


@pytest.mark.integration_mongodb
@pytest.mark.integration
class TestScyllaDBConnector:
    def test_scylla_db_connector(
        self,
        db: Session,
        integration_scylladb_config,
    ) -> None:
        orig_secrets = integration_scylladb_config.secrets.copy()

        # Test good creds
        connector = ScyllaConnector(integration_scylladb_config)
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        # Test bad username
        integration_scylladb_config.secrets["username"] = "bad_username"
        integration_scylladb_config.save(db)
        connector = ScyllaConnector(integration_scylladb_config)
        with pytest.raises(ConnectionException) as exc:
            connector.test_connection()
        assert exc._excinfo[1].args[0] == "Authentication failed."

        # Test bad host
        integration_scylladb_config.secrets = orig_secrets  # Reset
        integration_scylladb_config.secrets["host"] = "myserver.myname.com"
        integration_scylladb_config.save(db)
        connector = ScyllaConnector(integration_scylladb_config)
        with pytest.raises(ConnectionException) as exc:
            connector.test_connection()
        assert exc._excinfo[1].args[0] == "No host available."

        # Test bad keyspace
        integration_scylladb_config.secrets = orig_secrets  # Reset
        integration_scylladb_config.secrets["keyspace"] = "nonexistent_keyspace"
        integration_scylladb_config.save(db)
        connector = ScyllaConnector(integration_scylladb_config)
        with pytest.raises(ConnectionException) as exc:
            connector.test_connection()
        assert exc._excinfo[1].args[0] == "Unknown keyspace."

        # Test bad password
        integration_scylladb_config.secrets = orig_secrets  # Reset
        integration_scylladb_config.secrets["password"] = "bad pass"
        integration_scylladb_config.save(db)
        connector = ScyllaConnector(integration_scylladb_config)
        with pytest.raises(ConnectionException) as exc:
            connector.test_connection()
        assert exc._excinfo[1].args[0] == "Authentication failed."

        # Test specific, valid keyspace
        integration_scylladb_config.secrets = orig_secrets  # Reset
        integration_scylladb_config.secrets["keyspace"] = "vendors_keyspace"
        integration_scylladb_config.save(db)
        connector = ScyllaConnector(integration_scylladb_config)
        assert connector.test_connection() == ConnectionTestStatus.succeeded


@pytest.mark.integration_external
@pytest.mark.integration_rds_mysql
class TestRDSMySQLConnector:
    def test_connector(
        self,
        db: Session,
        rds_mysql_connection_config,
    ) -> None:
        connector = get_connector(rds_mysql_connection_config)
        assert connector.__class__ == RDSMySQLConnector

        assert connector.rds_client
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        rds_mysql_connection_config.save(db)
        connector = get_connector(rds_mysql_connection_config)
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        rds_mysql_connection_config.secrets["aws_secret_access_key"] = "bad_key"
        rds_mysql_connection_config.save(db)
        connector = get_connector(rds_mysql_connection_config)
        with pytest.raises(ConnectionException):
            connector.test_connection()

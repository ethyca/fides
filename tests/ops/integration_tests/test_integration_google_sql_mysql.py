import json

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    STORAGE_READ,
)
from fides.common.api.v1.urn_registry import CONNECTIONS, V1_URL_PREFIX
from fides.api.service.connectors import (
    get_connector,
)
from fides.api.service.connectors.sql_connector import (
    GoogleCloudSQLMySQLConnector,
)


#pytest tests/ops/integration_tests/test_external_database_connections.py --no-cov -m integration_google_cloud_sql_mysql1
@pytest.mark.integration_google_cloud_sql_mysql1
@pytest.mark.integration
class TestGoogleCloudSQLMySQLConnector:
    def test_google_cloud_sql_mysql_db_connector(
        self,
        db: Session,
        connection_config_google_cloud_sql_mysql,
        # google_cloud_sql_mysql_secrets,
    ) -> None:
        connector = get_connector(connection_config_google_cloud_sql_mysql)

        assert connector.__class__ == GoogleCloudSQLMySQLConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        # connection_config_google_cloud_sql_mysql.secrets = {
        #     "url": str(
        #         URL.create(
        #             "mysql+pymysql",
        #             username=google_cloud_sql_mysql_secrets["username"],
        #             password=google_cloud_sql_mysql_secrets["password"],
        #             host=google_cloud_sql_mysql_secrets["host"],
        #             database=google_cloud_sql_mysql_secrets["dbname"],
        #         )
        #     )
        # }
        # connection_config_google_cloud_sql_mysql.save(db)
        # connector = get_connector(connection_config_google_cloud_sql_mysql)
        # assert connector.test_connection() == ConnectionTestStatus.succeeded

        # connection_config_google_cloud_sql_mysql.secrets = {"host": "bad_host"}
        # connection_config_google_cloud_sql_mysql.save(db)
        # connector = get_connector(connection_config_google_cloud_sql_mysql)
        # with pytest.raises(ConnectionException):
        #     connector.test_connection()


@pytest.mark.integration_google_cloud_sql_mysql
@pytest.mark.integration
class TestGoogleCloudSQLMySQLConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, oauth_client, policy, connection_config_google_cloud_sql_mysql) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_google_cloud_sql_mysql.key}/secret"

    def test_google_cloud_sql_mysql_db_connection_incorrect_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_google_cloud_sql_mysql,
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
            == f"Secrets updated for ConnectionConfig with key: {connection_config_google_cloud_sql_mysql.key}."
        )
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to google_cloud_sql_mysql db." == body["failure_reason"]
        db.refresh(connection_config_google_cloud_sql_mysql)

        assert connection_config_google_cloud_sql_mysql.secrets == {
            "host": "mysql_example",
            "port": 1234,
            "dbname": "my_test_db",
            "username": None,
            "password": None,
            "ssh_required": False,
        }
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is not None
        assert connection_config_google_cloud_sql_mysql.last_test_succeeded is False

    def test_google_cloud_sql_mysql_db_connection_connect_with_components(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_google_cloud_sql_mysql,
        google_cloud_sql_mysql_secrets,
    ) -> None:
        payload = {
            "host": google_cloud_sql_mysql_secrets['host'],
            "dbname": google_cloud_sql_mysql_secrets['dbname'],
            "username": google_cloud_sql_mysql_secrets['username'],
            "password": google_cloud_sql_mysql_secrets['password'],
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
            == f"Secrets updated for ConnectionConfig with key: {connection_config_google_cloud_sql_mysql.key}."
        )
        assert body["test_status"] == "succeeded"
        assert body["failure_reason"] is None
        db.refresh(connection_config_google_cloud_sql_mysql)
        assert connection_config_google_cloud_sql_mysql.secrets == {
            "host": "34.132.168.106",
            "dbname": "mysql",
            "username": "root",
            "password": "ethyca",
            "port": 3306,
            "ssh_required": False,
        }
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is not None
        assert connection_config_google_cloud_sql_mysql.last_test_succeeded is True


@pytest.mark.integration_google_cloud_sql_mysql
@pytest.mark.integration
class TestGoogleCloudSQLMySQLConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(self, oauth_client, policy, connection_config_google_cloud_sql_mysql) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config_google_cloud_sql_mysql.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_google_cloud_sql_mysql,
    ) -> None:
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is None

        resp = api_client.get(url)
        assert resp.status_code == 401
        db.refresh(connection_config_google_cloud_sql_mysql)
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is None
        assert connection_config_google_cloud_sql_mysql.last_test_succeeded is None

    def test_connection_configuration_test_incorrect_scopes(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_google_cloud_sql_mysql,
    ) -> None:
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(connection_config_google_cloud_sql_mysql)
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is None
        assert connection_config_google_cloud_sql_mysql.last_test_succeeded is None

    def test_connection_configuration_test_failed_response(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_google_cloud_sql_mysql,
    ) -> None:
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is None
        connection_config_google_cloud_sql_mysql.secrets = {
            "host": "invalid_host",
            "dbname": "mysql_example",
        }
        connection_config_google_cloud_sql_mysql.save(db)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        db.refresh(connection_config_google_cloud_sql_mysql)
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is not None
        assert connection_config_google_cloud_sql_mysql.last_test_succeeded is False
        assert body["test_status"] == "failed"
        assert "Operational Error connecting to google_cloud_sql_mysql db." == body["failure_reason"]
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_google_cloud_sql_mysql.key}."
        )

    def test_connection_configuration_test(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config_google_cloud_sql_mysql,
    ) -> None:
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {connection_config_google_cloud_sql_mysql.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(connection_config_google_cloud_sql_mysql)
        assert connection_config_google_cloud_sql_mysql.last_test_timestamp is not None
        assert connection_config_google_cloud_sql_mysql.last_test_succeeded is True

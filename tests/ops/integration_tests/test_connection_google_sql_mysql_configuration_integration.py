import json

import pytest
from sqlalchemy import func, select, table
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.common_exceptions import ConnectionException
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.service.connectors import get_connector
from fides.api.service.connectors.sql_connector import GoogleCloudSQLMySQLConnector
from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    STORAGE_READ,
)
from fides.common.api.v1.urn_registry import CONNECTIONS, V1_URL_PREFIX


@pytest.mark.integration_google_cloud_sql_mysql
@pytest.mark.integration
class TestGoogleCloudSQLMySQLConnector:
    def test_google_cloud_sql_mysql_db_connector(
        self,
        db: Session,
        google_cloud_sql_mysql_connection_config,
    ) -> None:
        connector = get_connector(google_cloud_sql_mysql_connection_config)

        assert connector.__class__ == GoogleCloudSQLMySQLConnector

        client = connector.client()
        assert client.__class__ == Engine
        assert connector.test_connection() == ConnectionTestStatus.succeeded

        google_cloud_sql_mysql_connection_config.secrets["keyfile_creds"] = {}
        google_cloud_sql_mysql_connection_config.save(db)
        connector = get_connector(google_cloud_sql_mysql_connection_config)
        with pytest.raises(ConnectionException):
            connector.test_connection()


@pytest.mark.integration_google_cloud_sql_mysql
@pytest.mark.integration
class TestGoogleCloudSQLMySQLConnectionPutSecretsAPI:
    @pytest.fixture(scope="function")
    def url(
        self, oauth_client, policy, google_cloud_sql_mysql_connection_config
    ) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{google_cloud_sql_mysql_connection_config.key}/secret"

    def test_google_cloud_sql_mysql_db_connection_incorrect_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        google_cloud_sql_mysql_connection_config,
        url,
    ) -> None:
        payload = dict(google_cloud_sql_mysql_connection_config.secrets)
        payload["instance_connection_name"] = "wrong:instance:connection_name"

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
            == f"Secrets updated for ConnectionConfig with key: {google_cloud_sql_mysql_connection_config.key}."
        )

        assert body["test_status"] == "failed"
        assert "Connection error." == body["failure_reason"]

        db.refresh(google_cloud_sql_mysql_connection_config)
        assert (
            google_cloud_sql_mysql_connection_config.secrets["instance_connection_name"]
            == "wrong:instance:connection_name"
        )
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is not None
        assert google_cloud_sql_mysql_connection_config.last_test_succeeded is False

    def test_google_cloud_sql_mysql_db_connection_connect_with_components(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        google_cloud_sql_mysql_connection_config,
    ) -> None:
        payload = dict(google_cloud_sql_mysql_connection_config.secrets)

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
            == f"Secrets updated for ConnectionConfig with key: {google_cloud_sql_mysql_connection_config.key}."
        )
        assert body["test_status"] == "succeeded"
        assert body["failure_reason"] is None

        db.refresh(google_cloud_sql_mysql_connection_config)
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is not None
        assert google_cloud_sql_mysql_connection_config.last_test_succeeded is True


@pytest.mark.integration_google_cloud_sql_mysql
@pytest.mark.integration
class TestGoogleCloudSQLMySQLConnectionTestSecretsAPI:
    @pytest.fixture(scope="function")
    def url(
        self, oauth_client, policy, google_cloud_sql_mysql_connection_config
    ) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{google_cloud_sql_mysql_connection_config.key}/test"

    def test_connection_configuration_test_not_authenticated(
        self,
        url,
        api_client: TestClient,
        db: Session,
        google_cloud_sql_mysql_connection_config,
    ) -> None:
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is None

        resp = api_client.get(url)
        assert resp.status_code == 401
        db.refresh(google_cloud_sql_mysql_connection_config)
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is None
        assert google_cloud_sql_mysql_connection_config.last_test_succeeded is None

    def test_connection_configuration_test_incorrect_scopes(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        google_cloud_sql_mysql_connection_config,
    ) -> None:
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403
        db.refresh(google_cloud_sql_mysql_connection_config)
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is None
        assert google_cloud_sql_mysql_connection_config.last_test_succeeded is None

    def test_connection_configuration_test_failed_response(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        google_cloud_sql_mysql_connection_config,
    ) -> None:
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is None
        google_cloud_sql_mysql_connection_config.secrets = {
            "host": "invalid_host",
            "dbname": "mysql_example",
        }
        google_cloud_sql_mysql_connection_config.save(db)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        db.refresh(google_cloud_sql_mysql_connection_config)
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is not None
        assert google_cloud_sql_mysql_connection_config.last_test_succeeded is False
        assert body["test_status"] == "failed"
        assert "Connection error." == body["failure_reason"]
        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {google_cloud_sql_mysql_connection_config.key}."
        )

    def test_connection_configuration_test(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        google_cloud_sql_mysql_connection_config,
    ) -> None:
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is None

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)

        assert (
            body["msg"]
            == f"Test completed for ConnectionConfig with key: {google_cloud_sql_mysql_connection_config.key}."
        )
        assert body["failure_reason"] is None
        assert body["test_status"] == "succeeded"
        db.refresh(google_cloud_sql_mysql_connection_config)
        assert google_cloud_sql_mysql_connection_config.last_test_timestamp is not None
        assert google_cloud_sql_mysql_connection_config.last_test_succeeded is True


@pytest.mark.integration
@pytest.mark.integration_google_cloud_sql_mysql
@pytest.mark.integration_google_cloud_sql_mysql_x
def test_mysql_example_data(google_cloud_sql_mysql_integration_db):
    """Confirm that the example database is populated with simulated data"""
    expected_counts = {
        "product": 3,
        "address": 3,
        "customer": 2,
        "employee": 2,
        "payment_card": 2,
        "orders": 4,
        "order_item": 5,
        "visit": 2,
        "login": 7,
        "service_request": 4,
        "report": 4,
    }

    for table_name, expected_count in expected_counts.items():
        # NOTE: we could use text() here, but we want to avoid SQL string
        # templating as much as possible. instead, use the table() helper to
        # dynamically generate the FROM clause for each table_name
        count_sql = select(func.count()).select_from(table(table_name))
        assert google_cloud_sql_mysql_integration_db.execute(count_sql).scalar() == expected_count

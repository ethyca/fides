import json
from datetime import datetime
from typing import Dict, List
from unittest import mock
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi_pagination import Params
from fideslib.models.client import ClientDetail
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fidesops.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_READ,
    STORAGE_DELETE,
)
from fidesops.api.v1.urn_registry import CONNECTIONS, SAAS_CONFIG, V1_URL_PREFIX
from fidesops.models.connectionconfig import ConnectionConfig

page_size = Params().size


class TestPatchConnections:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + CONNECTIONS

    @pytest.fixture(scope="function")
    def payload(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "My Main Postgres DB",
                "key": "postgres_db_1",
                "connection_type": "postgres",
                "access": "write",
            },
            {"name": "My Mongo DB", "connection_type": "mongodb", "access": "read"},
        ]

    def test_patch_connections_not_authenticated(
        self, api_client: TestClient, url, payload
    ) -> None:
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_patch_connections_incorrect_scope(
        self, api_client: TestClient, generate_auth_header, url, payload
    ) -> None:
        auth_header = generate_auth_header(scopes=[STORAGE_DELETE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_connections_add_secret_invalid(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        payload_with_secrets = [
            {
                "name": "My Main Postgres DB",
                "key": "postgres_db_1",
                "connection_type": "postgres",
                "access": "write",
                "secrets": {"host": "localhost"},
            },
            {"name": "My Mongo DB", "connection_type": "mongodb", "access": "read"},
        ]
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload_with_secrets)
        assert 422 == response.status_code
        response_body = json.loads(response.text)
        assert "extra fields not permitted" == response_body["detail"][0]["msg"]

    def test_patch_http_connection(
        self, url, api_client, db: Session, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = [
            {
                "name": "My Post-Execution Webhook",
                "key": "webhook_key",
                "connection_type": "https",
                "access": "read",
            }
        ]
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        body = json.loads(response.text)
        assert body["succeeded"][0]["connection_type"] == "https"
        http_config = ConnectionConfig.get_by(db, field="key", value="webhook_key")
        http_config.delete(db)

    def test_patch_connections_bulk_create(
        self, api_client: TestClient, db: Session, generate_auth_header, url, payload
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = json.loads(response.text)
        assert len(response_body) == 2
        assert len(response_body["succeeded"]) == 2

        postgres_connection = response_body["succeeded"][0]
        postgres_resource = (
            db.query(ConnectionConfig).filter_by(key="postgres_db_1").first()
        )
        assert postgres_connection["name"] == "My Main Postgres DB"
        assert postgres_connection["key"] == "postgres_db_1"
        assert postgres_connection["connection_type"] == "postgres"
        assert postgres_connection["access"] == "write"
        assert postgres_connection["created_at"] is not None
        assert postgres_connection["updated_at"] is not None
        assert postgres_connection["last_test_timestamp"] is None
        assert postgres_connection["disabled"] is False
        assert "secrets" not in postgres_connection

        mongo_connection = response_body["succeeded"][1]
        mongo_resource = db.query(ConnectionConfig).filter_by(key="my_mongo_db").first()
        assert mongo_connection["name"] == "My Mongo DB"
        assert mongo_connection["key"] == "my_mongo_db"  # stringified name
        assert mongo_connection["connection_type"] == "mongodb"
        assert mongo_connection["access"] == "read"
        assert postgres_connection["disabled"] is False
        assert mongo_connection["created_at"] is not None
        assert mongo_connection["updated_at"] is not None
        assert mongo_connection["last_test_timestamp"] is None
        assert "secrets" not in mongo_connection

        assert response_body["failed"] == []  # No failures

        postgres_resource.delete(db)
        mongo_resource.delete(db)

    def test_patch_connections_bulk_update_key_error(
        self, url, api_client: TestClient, generate_auth_header, payload
    ) -> None:
        # Create resources first
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        api_client.patch(url, headers=auth_header, json=payload)

        # Update resources
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert response.status_code == 200
        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 1

        succeeded = response_body["succeeded"]
        failed = response_body["failed"]

        # key supplied matches existing key, so the rest of the configs are updated
        assert succeeded[0]["key"] == "postgres_db_1"

        # No key was supplied in request body, just a name, and that name turned into a key that exists
        assert failed[0]["data"]["key"] is None
        assert (
            "Key my_mongo_db already exists in ConnectionConfig" in failed[0]["message"]
        )

    def test_patch_connections_bulk_create_limit_exceeded(
        self, url, api_client: TestClient, db: Session, generate_auth_header
    ):
        payload = []
        for i in range(0, 51):
            payload.append(
                {
                    "name": f"My Main Postgres DB {i}",
                    "key": f"postgres_db_{i}",
                    "connection_type": "postgres",
                    "access": "read",
                }
            )

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "ensure this value has at most 50 items"
        )

    def test_patch_connections_bulk_update(
        self, url, api_client: TestClient, db: Session, generate_auth_header, payload
    ) -> None:
        # Create resources first
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        api_client.patch(url, headers=auth_header, json=payload)

        # Update resources
        payload = [
            {
                "name": "My Main Postgres DB",
                "key": "postgres_db_1",
                "connection_type": "postgres",
                "access": "read",
                "disabled": True,
            },
            {
                "key": "my_mongo_db",
                "name": "My Mongo DB",
                "connection_type": "mongodb",
                "access": "write",
            },
            {
                "key": "my_mysql_db",
                "name": "My MySQL DB",
                "connection_type": "mysql",
                "access": "read",
            },
            {
                "key": "my_mssql_db",
                "name": "My MsSQL DB",
                "connection_type": "mssql",
                "access": "write",
            },
            {
                "key": "my_mariadb_db",
                "name": "My MariaDB",
                "connection_type": "mariadb",
                "access": "write",
            },
            {
                "key": "my_bigquery_db",
                "name": "BigQuery Warehouse",
                "connection_type": "bigquery",
                "access": "write",
            },
            {
                "key": "my_redshift_cluster",
                "name": "My Amazon Redshift",
                "connection_type": "redshift",
                "access": "read",
            },
            {
                "key": "my_snowflake",
                "name": "Snowflake Warehouse",
                "connection_type": "snowflake",
                "access": "write",
                "description": "Backup snowflake db",
            },
        ]

        response = api_client.patch(
            V1_URL_PREFIX + CONNECTIONS, headers=auth_header, json=payload
        )

        assert 200 == response.status_code
        response_body = json.loads(response.text)
        assert len(response_body) == 2
        assert len(response_body["succeeded"]) == 8
        assert len(response_body["failed"]) == 0

        postgres_connection = response_body["succeeded"][0]
        assert postgres_connection["access"] == "read"
        assert postgres_connection["disabled"] is True
        assert "secrets" not in postgres_connection
        assert postgres_connection["updated_at"] is not None
        postgres_resource = (
            db.query(ConnectionConfig).filter_by(key="postgres_db_1").first()
        )
        assert postgres_resource.access.value == "read"
        assert postgres_resource.disabled

        mongo_connection = response_body["succeeded"][1]
        assert mongo_connection["access"] == "write"
        assert mongo_connection["disabled"] is False
        assert mongo_connection["updated_at"] is not None
        mongo_resource = db.query(ConnectionConfig).filter_by(key="my_mongo_db").first()
        assert mongo_resource.access.value == "write"
        assert "secrets" not in mongo_connection
        assert not mongo_resource.disabled

        mysql_connection = response_body["succeeded"][2]
        assert mysql_connection["access"] == "read"
        assert mysql_connection["updated_at"] is not None
        mysql_resource = db.query(ConnectionConfig).filter_by(key="my_mysql_db").first()
        assert mysql_resource.access.value == "read"
        assert "secrets" not in mysql_connection

        mssql_connection = response_body["succeeded"][3]
        assert mssql_connection["access"] == "write"
        assert mssql_connection["updated_at"] is not None
        mssql_resource = db.query(ConnectionConfig).filter_by(key="my_mssql_db").first()
        assert mssql_resource.access.value == "write"
        assert "secrets" not in mssql_connection

        mariadb_connection = response_body["succeeded"][4]
        assert mariadb_connection["access"] == "write"
        assert mariadb_connection["updated_at"] is not None
        mariadb_resource = (
            db.query(ConnectionConfig).filter_by(key="my_mariadb_db").first()
        )
        assert mariadb_resource.access.value == "write"
        assert "secrets" not in mariadb_connection

        bigquery_connection = response_body["succeeded"][5]
        assert bigquery_connection["access"] == "write"
        assert bigquery_connection["updated_at"] is not None
        bigquery_resource = (
            db.query(ConnectionConfig).filter_by(key="my_bigquery_db").first()
        )
        assert bigquery_resource.access.value == "write"
        assert "secrets" not in bigquery_connection

        redshift_connection = response_body["succeeded"][6]
        assert redshift_connection["access"] == "read"
        assert redshift_connection["updated_at"] is not None
        redshift_resource = (
            db.query(ConnectionConfig).filter_by(key="my_redshift_cluster").first()
        )
        assert redshift_resource.access.value == "read"
        assert "secrets" not in redshift_connection

        snowflake_connection = response_body["succeeded"][7]
        assert snowflake_connection["access"] == "write"
        assert snowflake_connection["updated_at"] is not None
        assert snowflake_connection["description"] == "Backup snowflake db"
        snowflake_resource = (
            db.query(ConnectionConfig).filter_by(key="my_snowflake").first()
        )
        assert snowflake_resource.access.value == "write"
        assert snowflake_resource.description == "Backup snowflake db"
        assert "secrets" not in snowflake_connection

        postgres_resource.delete(db)
        mongo_resource.delete(db)
        redshift_resource.delete(db)
        snowflake_resource.delete(db)
        mariadb_resource.delete(db)
        mysql_resource.delete(db)
        mssql_resource.delete(db)
        bigquery_resource.delete(db)

    @mock.patch("fideslib.db.base_class.OrmWrappedFidesBase.create_or_update")
    def test_patch_connections_failed_response(
        self, mock_create: Mock, api_client: TestClient, generate_auth_header, url
    ) -> None:
        mock_create.side_effect = HTTPException(mock.Mock(status=400), "Test error")

        payload = [
            {
                "name": "My Main Postgres DB",
                "key": "postgres_db_1",
                "connection_type": "postgres",
                "access": "write",
            },
            {"name": "My Mongo DB", "connection_type": "mongodb", "access": "read"},
        ]
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 200  # Returns 200 regardless
        response_body = json.loads(response.text)
        assert response_body["succeeded"] == []
        assert len(response_body["failed"]) == 2

        for failed_response in response_body["failed"]:
            assert (
                "This connection configuration could not be added"
                in failed_response["message"]
            )
            assert set(failed_response.keys()) == {"message", "data"}

        assert response_body["failed"][0]["data"] == {
            "name": "My Main Postgres DB",
            "key": "postgres_db_1",
            "connection_type": "postgres",
            "access": "write",
            "disabled": False,
            "description": None,
        }
        assert response_body["failed"][1]["data"] == {
            "name": "My Mongo DB",
            "key": None,
            "connection_type": "mongodb",
            "access": "read",
            "disabled": False,
            "description": None,
        }

    @mock.patch("fidesops.main.prepare_and_log_request")
    def test_patch_connections_incorrect_scope_analytics(
        self,
        mocked_prepare_and_log_request,
        api_client: TestClient,
        generate_auth_header,
        payload,
    ) -> None:
        url = V1_URL_PREFIX + CONNECTIONS
        auth_header = generate_auth_header(scopes=[STORAGE_DELETE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code
        assert mocked_prepare_and_log_request.called
        call_args = mocked_prepare_and_log_request._mock_call_args[0]

        assert call_args[0] == "PATCH: http://testserver/api/v1/connection"
        assert call_args[1] == "testserver"
        assert call_args[2] == 403
        assert isinstance(call_args[3], datetime)
        assert call_args[4] is None
        assert call_args[5] == "HTTPException"

    @mock.patch("fidesops.main.prepare_and_log_request")
    def test_patch_http_connection_successful_analytics(
        self,
        mocked_prepare_and_log_request,
        api_client,
        db: Session,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = [
            {
                "name": "My Post-Execution Webhook",
                "key": "webhook_key",
                "connection_type": "https",
                "access": "read",
            }
        ]
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        body = json.loads(response.text)
        assert body["succeeded"][0]["connection_type"] == "https"
        http_config = ConnectionConfig.get_by(db, field="key", value="webhook_key")
        http_config.delete(db)

        call_args = mocked_prepare_and_log_request._mock_call_args[0]

        assert call_args[0] == "PATCH: http://testserver/api/v1/connection"
        assert call_args[1] == "testserver"
        assert call_args[2] == 200
        assert isinstance(call_args[3], datetime)
        assert call_args[4] is None
        assert call_args[5] is None


class TestGetConnections:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + CONNECTIONS

    def test_get_connections_not_authenticated(
        self, api_client: TestClient, generate_auth_header, connection_config, url
    ) -> None:
        resp = api_client.get(url, headers={})
        assert resp.status_code == 401

    def test_get_connections_wrong_scope(
        self, api_client: TestClient, generate_auth_header, connection_config, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[STORAGE_DELETE])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 403

    def test_get_connection_configs(
        self, api_client: TestClient, generate_auth_header, connection_config, url
    ) -> None:
        # Test get connection configs happy path
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200

        response_body = json.loads(resp.text)
        assert len(response_body["items"]) == 1
        connection = response_body["items"][0]
        assert set(connection.keys()) == {
            "connection_type",
            "access",
            "updated_at",
            "name",
            "last_test_timestamp",
            "last_test_succeeded",
            "key",
            "created_at",
            "disabled",
            "description",
        }

        assert connection["key"] == "my_postgres_db_1"
        assert connection["connection_type"] == "postgres"
        assert connection["access"] == "write"
        assert connection["updated_at"] is not None
        assert connection["last_test_timestamp"] is None

        assert response_body["total"] == 1
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

    def test_filter_connections_disabled_and_type(
        self,
        db,
        connection_config,
        disabled_connection_config,
        read_connection_config,
        redshift_connection_config,
        mongo_connection_config,
        api_client,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])

        resp = api_client.get(url, headers=auth_header)
        items = resp.json()["items"]
        assert len(items) == 5

        resp = api_client.get(url + "?connection_type=postgres", headers=auth_header)
        items = resp.json()["items"]
        assert len(items) == 3
        assert all(
            [con["connection_type"] == "postgres" for con in resp.json()["items"]]
        )

        resp = api_client.get(
            url + "?connection_type=postgres&connection_type=redshift",
            headers=auth_header,
        )
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 4
        assert all(
            [
                con["connection_type"] in ["redshift", "postgres"]
                for con in resp.json()["items"]
            ]
        )

        resp = api_client.get(
            url + "?connection_type=postgres&disabled=false", headers=auth_header
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2
        assert all(
            [con["connection_type"] in ["postgres"] for con in resp.json()["items"]]
        )
        assert all([con["disabled"] is False for con in resp.json()["items"]])

        resp = api_client.get(
            url + "?connection_type=postgres&disabled=True", headers=auth_header
        )
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 1
        assert all(
            [con["connection_type"] in ["postgres"] for con in resp.json()["items"]]
        )
        assert all([con["disabled"] is True for con in resp.json()["items"]])

    def test_filter_test_status(
        self,
        db,
        connection_config,
        disabled_connection_config,
        read_connection_config,
        redshift_connection_config,
        mongo_connection_config,
        api_client,
        generate_auth_header,
        url,
    ):
        mongo_connection_config.last_test_succeeded = True
        mongo_connection_config.save(db)
        redshift_connection_config.last_test_succeeded = False
        redshift_connection_config.save(db)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url + "?test_status=passed", headers=auth_header)
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 1
        assert items[0]["last_test_succeeded"] is True
        assert items[0]["key"] == mongo_connection_config.key

        resp = api_client.get(url + "?test_status=failed", headers=auth_header)
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 1
        assert items[0]["last_test_succeeded"] is False
        assert items[0]["key"] == redshift_connection_config.key

        resp = api_client.get(url + "?test_status=untested", headers=auth_header)
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 3
        assert [item["last_test_succeeded"] is None for item in items]

    def test_filter_system_type(
        self,
        db,
        connection_config,
        disabled_connection_config,
        read_connection_config,
        redshift_connection_config,
        mongo_connection_config,
        api_client,
        generate_auth_header,
        stripe_connection_config,
        integration_manual_config,
        url,
    ):

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url + "?system_type=saas", headers=auth_header)
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 1
        assert items[0]["connection_type"] == "saas"
        assert items[0]["key"] == stripe_connection_config.key

        resp = api_client.get(url + "?system_type=database", headers=auth_header)
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 5

        resp = api_client.get(url + "?system_type=manual", headers=auth_header)
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 1
        assert items[0]["connection_type"] == "manual"
        assert items[0]["key"] == integration_manual_config.key

        # Conflicting filters
        resp = api_client.get(
            url + "?system_type=saas&connection_type=mongodb", headers=auth_header
        )
        items = resp.json()["items"]
        assert resp.status_code == 200
        assert len(items) == 0

    def test_search_connections(
        self,
        db,
        connection_config,
        read_connection_config,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])

        resp = api_client.get(url + "?search=primary", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1
        assert "primary" in resp.json()["items"][0]["description"].lower()

        resp = api_client.get(url + "?search=read", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1
        assert "read" in resp.json()["items"][0]["description"].lower()

        resp = api_client.get(url + "?search=nonexistent", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 0

        resp = api_client.get(url + "?search=postgres", headers=auth_header)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2

        ordered = (
            db.query(ConnectionConfig)
            .filter(
                ConnectionConfig.key.in_(
                    [read_connection_config.key, connection_config.key]
                )
            )
            .order_by(ConnectionConfig.name.asc())
            .all()
        )
        assert len(ordered) == 2
        assert ordered[0].key == items[0]["key"]
        assert ordered[1].key == items[1]["key"]


class TestGetConnection:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy, connection_config) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}"

    def test_get_connection_not_authenticated(
        self, url, api_client: TestClient, connection_config
    ) -> None:
        resp = api_client.get(url, headers={})
        assert resp.status_code == 401

    def test_get_connection_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        auth_header = generate_auth_header(scopes=[STORAGE_DELETE])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 403

    def test_get_connection_does_not_exist(
        self, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(
            f"{V1_URL_PREFIX}{CONNECTIONS}/this_is_a_nonexistent_key",
            headers=auth_header,
        )
        assert resp.status_code == 404

    def test_get_connection_config(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200

        response_body = json.loads(resp.text)
        assert set(response_body.keys()) == {
            "connection_type",
            "access",
            "updated_at",
            "name",
            "last_test_timestamp",
            "last_test_succeeded",
            "key",
            "created_at",
            "disabled",
            "description",
        }

        assert response_body["key"] == "my_postgres_db_1"
        assert response_body["connection_type"] == "postgres"
        assert response_body["access"] == "write"
        assert response_body["updated_at"] is not None
        assert response_body["last_test_timestamp"] is None


class TestDeleteConnection:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy, connection_config) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}"

    def test_delete_connection_config_not_authenticated(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        # Test not authenticated
        resp = api_client.delete(url, headers={})
        assert resp.status_code == 401

    def test_delete_connection_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == 403

    def test_delete_connection_config_does_not_exist(
        self, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_DELETE])
        resp = api_client.delete(
            f"{V1_URL_PREFIX}{CONNECTIONS}/non_existent_config", headers=auth_header
        )
        assert resp.status_code == 404

    def test_delete_connection_config(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_DELETE])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == 204

        assert (
            db.query(ConnectionConfig).filter_by(key=connection_config.key).first()
            is None
        )


class TestPutConnectionConfigSecrets:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy, connection_config) -> str:
        return f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}/secret"

    def test_put_connection_config_secrets_not_authenticated(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        resp = api_client.put(url, headers={})
        assert resp.status_code == 401

    def test_put_connection_config_secrets_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.put(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_put_connection_config_secrets_invalid_config(
        self, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        resp = api_client.put(
            f"{V1_URL_PREFIX}{CONNECTIONS}/this_is_not_a_known_key/secret",
            headers=auth_header,
            json={},
        )
        assert resp.status_code == 404

    def test_put_connection_config_secrets_schema_validation(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {"incorrect_postgres_uri_component": "test-1"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert json.loads(resp.text)["detail"][0]["msg"] == "extra fields not permitted"

        payload = {"dbname": "my_db"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            json.loads(resp.text)["detail"][0]["msg"]
            == "PostgreSQLSchema must be supplied a 'url' or all of: ['host']."
        )

        payload = {"port": "cannot be turned into an integer"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            json.loads(resp.text)["detail"][0]["msg"] == "value is not a valid integer"
        )

    def test_put_connection_config_secrets(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
    ) -> None:
        """Note: this test does not attempt to actually connect to the db, via use of verify query param."""
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {"host": "localhost", "port": "1234", "dbname": "my_test_db"}
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        assert (
            json.loads(resp.text)["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config.key}."
        )
        db.refresh(connection_config)
        assert connection_config.secrets == {
            "host": "localhost",
            "port": 1234,
            "dbname": "my_test_db",
            "username": None,
            "password": None,
            "url": None,
        }

        payload = {"url": "postgresql://test_user:test_pass@localhost:1234/my_test_db"}
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        assert (
            json.loads(resp.text)["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config.key}."
        )
        db.refresh(connection_config)
        assert connection_config.secrets == {
            "host": None,
            "port": None,
            "dbname": None,
            "username": None,
            "password": None,
            "url": payload["url"],
        }
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

    def test_put_connection_config_redshift_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        redshift_connection_config,
    ) -> None:
        """Note: this test does not attempt to actually connect to the db, via use of verify query param."""
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{redshift_connection_config.key}/secret"
        payload = {
            "host": "examplecluster.abc123xyz789.us-west-1.redshift.amazonaws.com",
            "port": 5439,
            "database": "dev",
            "user": "awsuser",
            "password": "test_password",
            "db_schema": "test",
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        assert (
            json.loads(resp.text)["msg"]
            == f"Secrets updated for ConnectionConfig with key: {redshift_connection_config.key}."
        )
        db.refresh(redshift_connection_config)
        assert redshift_connection_config.secrets == {
            "host": "examplecluster.abc123xyz789.us-west-1.redshift.amazonaws.com",
            "port": 5439,
            "database": "dev",
            "user": "awsuser",
            "password": "test_password",
            "db_schema": "test",
            "url": None,
        }
        assert redshift_connection_config.last_test_timestamp is None
        assert redshift_connection_config.last_test_succeeded is None

    def test_put_connection_config_bigquery_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        bigquery_connection_config_without_secrets,
    ) -> None:
        """Note: this test does not attempt to actually connect to the db, via use of verify query param."""
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{bigquery_connection_config_without_secrets.key}/secret"
        payload = {
            "dataset": "some-dataset",
            "keyfile_creds": {
                "type": "service_account",
                "project_id": "project-12345",
                "private_key_id": "qo28cy4nlwu",
                "private_key": "-----BEGIN PRIVATE KEY-----\nqi2unhflhncflkjas\nkqiu34c\n-----END PRIVATE KEY-----\n",
                "client_email": "something@project-12345.iam.gserviceaccount.com",
                "client_id": "287345028734538",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/something%40project-12345.iam.gserviceaccount.com",
            },
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        assert (
            json.loads(resp.text)["msg"]
            == f"Secrets updated for ConnectionConfig with key: {bigquery_connection_config_without_secrets.key}."
        )
        db.refresh(bigquery_connection_config_without_secrets)
        assert bigquery_connection_config_without_secrets.secrets == {
            "url": None,
            "dataset": "some-dataset",
            "keyfile_creds": {
                "type": "service_account",
                "project_id": "project-12345",
                "private_key_id": "qo28cy4nlwu",
                "private_key": "-----BEGIN PRIVATE KEY-----\nqi2unhflhncflkjas\nkqiu34c\n-----END PRIVATE KEY-----\n",
                "client_email": "something@project-12345.iam.gserviceaccount.com",
                "client_id": "287345028734538",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/something%40project-12345.iam.gserviceaccount.com",
            },
        }
        assert bigquery_connection_config_without_secrets.last_test_timestamp is None
        assert bigquery_connection_config_without_secrets.last_test_succeeded is None

    def test_put_connection_config_snowflake_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        snowflake_connection_config,
    ) -> None:
        """Note: this test does not attempt to actually connect to the db, via use of verify query param."""
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{snowflake_connection_config.key}/secret"
        payload = {
            "user_login_name": "test_user",
            "password": "test_password",
            "account_identifier": "flso2222test",
            "database_name": "test",
        }

        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        assert (
            json.loads(resp.text)["msg"]
            == f"Secrets updated for ConnectionConfig with key: {snowflake_connection_config.key}."
        )
        db.refresh(snowflake_connection_config)
        assert snowflake_connection_config.secrets == {
            "user_login_name": "test_user",
            "password": "test_password",
            "account_identifier": "flso2222test",
            "database_name": "test",
            "schema_name": None,
            "warehouse_name": None,
            "role_name": None,
            "url": None,
        }
        assert snowflake_connection_config.last_test_timestamp is None
        assert snowflake_connection_config.last_test_succeeded is None

    def test_put_http_connection_config_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        https_connection_config,
    ) -> None:
        """Note: HTTP Connection Configs don't attempt to test secrets"""
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{https_connection_config.key}/secret"
        payload = {"url": "example.com", "authorization": "test_authorization123"}

        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {https_connection_config.key}."
        )
        assert body["test_status"] == "skipped"
        db.refresh(https_connection_config)
        assert https_connection_config.secrets == {
            "url": "example.com",
            "authorization": "test_authorization123",
        }
        assert https_connection_config.last_test_timestamp is None
        assert https_connection_config.last_test_succeeded is None

    @pytest.mark.unit_saas
    def test_put_saas_example_connection_config_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        saas_example_connection_config,
        saas_example_secrets,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = (
            f"{V1_URL_PREFIX}{CONNECTIONS}/{saas_example_connection_config.key}/secret"
        )
        payload = saas_example_secrets

        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200

        body = json.loads(resp.text)
        assert (
            body["msg"]
            == f"Secrets updated for ConnectionConfig with key: {saas_example_connection_config.key}."
        )

        db.refresh(saas_example_connection_config)
        assert saas_example_connection_config.secrets == saas_example_secrets
        assert saas_example_connection_config.last_test_timestamp is None
        assert saas_example_connection_config.last_test_succeeded is None

    @pytest.mark.unit_saas
    def test_put_saas_example_connection_config_secrets_missing_saas_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        saas_example_connection_config_without_saas_config,
        saas_example_secrets,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{saas_example_connection_config_without_saas_config.key}/secret"
        payload = saas_example_secrets

        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422

        body = json.loads(resp.text)
        assert (
            body["detail"]
            == f"A SaaS config to validate the secrets is unavailable for this connection config, please add one via {SAAS_CONFIG}"
        )

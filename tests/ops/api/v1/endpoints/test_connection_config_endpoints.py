import json
from datetime import datetime
from unittest import mock
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.privacy_request import PrivacyRequestStatus
from fides.api.models.sql_models import Dataset
from fides.api.oauth.roles import APPROVER, OWNER, VIEWER
from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_READ,
    STORAGE_DELETE,
)
from fides.common.api.v1.urn_registry import CONNECTIONS, SAAS_CONFIG, V1_URL_PREFIX
from tests.fixtures.application_fixtures import integration_secrets
from tests.fixtures.saas.connection_template_fixtures import instantiate_connector

page_size = Params().size


class TestPatchConnections:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + CONNECTIONS

    @pytest.fixture(scope="function")
    def payload(self):
        return [
            {
                "name": "My Main Postgres DB",
                "key": "postgres_db_1",
                "connection_type": "postgres",
                "access": "write",
                "secrets": {
                    "url": None,
                    "host": "http://localhost",
                    "port": 5432,
                    "dbname": "test",
                    "db_schema": "test",
                    "username": "test",
                    "password": "test",
                },
            },
            {"name": "My Mongo DB", "connection_type": "mongodb", "access": "read"},
        ]

    def test_patch_connections_not_authenticated(
        self, api_client: TestClient, url, payload
    ) -> None:
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_malformed_token_is_forbidden(self, api_client: TestClient, url, payload):
        auth_header = {"Authorization": "Bearer invalid"}
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_connections_incorrect_scope(
        self, api_client: TestClient, generate_auth_header, url, payload
    ) -> None:
        auth_header = generate_auth_header(scopes=[STORAGE_DELETE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_connections_viewer_role(
        self, api_client: TestClient, generate_role_header, url, payload
    ) -> None:
        auth_header = generate_role_header(roles=[VIEWER])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_connections_approver_role(
        self, api_client: TestClient, generate_role_header, url, payload
    ) -> None:
        auth_header = generate_role_header(roles=[APPROVER])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_connection_owner_role(
        self, url, api_client, db: Session, generate_role_header
    ):
        auth_header = generate_role_header(roles=[OWNER])
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

    def test_patch_connection_saas_with_secrets_exists(
        self, url, api_client, generate_auth_header, db, mailchimp_config
    ):
        payload = [
            {
                "secrets": {
                    "domain": "test_mailchimp_domain",
                    "username": "test_mailchimp_username",
                    "api_key": "test_mailchimp_api_key",
                },
                "name": "My Mailchimp Test",
                "description": "Mailchimp ConnectionConfig description",
                "key": f"mailchimp{uuid4()}",
                "connection_type": "saas",
                "access": "read",
            },
        ]

        ConnectionConfig.create(
            db=db,
            data={
                "key": payload[0]["key"],
                "name": payload[0]["name"],
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {"domain": "test", "username": "test", "api_key": "test"},
                "saas_config": mailchimp_config,
                "description": "some description",
            },
        )

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        assert (
            response.json()["succeeded"][0]["connection_type"]
            == payload[0]["connection_type"]
        )
        assert (
            response.json()["succeeded"][0]["description"] == payload[0]["description"]
        )

        config = ConnectionConfig.get_by(db, field="key", value=payload[0]["key"])
        assert config.secrets == payload[0]["secrets"]

    def test_patch_connection_saas_with_secrets_exists_minimal_payload(
        self, url, api_client, generate_auth_header, db, mailchimp_config
    ):
        payload = [
            {
                "key": f"mailchimp{uuid4()}",
                "name": "My Mailchimp Test",
                "description": "Mailchimp ConnectionConfig description",
                "disabled": "true",
                "connection_type": "saas",
                "access": "read",
            },
        ]

        ConnectionConfig.create(
            db=db,
            data={
                "key": payload[0]["key"],
                "name": payload[0]["name"],
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {"domain": "test", "username": "test", "api_key": "test"},
                "saas_config": mailchimp_config,
                "description": "some description",
            },
        )

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        assert (
            response.json()["succeeded"][0]["connection_type"]
            == payload[0]["connection_type"]
        )
        assert (
            response.json()["succeeded"][0]["description"] == payload[0]["description"]
        )

        config = ConnectionConfig.get_by(db, field="key", value=payload[0]["key"])
        assert config.secrets == {
            "domain": "test",
            "username": "test",
            "api_key": "test",
        }

    def test_patch_connection_saas_with_secrets_new(
        self, url, api_client, generate_auth_header, db
    ):
        payload = [
            {
                "secrets": {
                    "domain": "test_mailchimp_domain",
                    "username": "test_mailchimp_username",
                    "api_key": "test_mailchimp_api_key",
                },
                "name": "My Mailchimp Test",
                "description": "Mailchimp ConnectionConfig description",
                "key": "mailchimp_1",
                "connection_type": "saas",
                "saas_connector_type": "mailchimp",
                "access": "read",
            },
        ]

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        body = json.loads(response.text)
        assert body["succeeded"][0]["connection_type"] == payload[0]["connection_type"]
        assert (
            response.json()["succeeded"][0]["description"] == payload[0]["description"]
        )

        config = ConnectionConfig.get_by(db, field="key", value=payload[0]["key"])
        assert config.secrets == payload[0]["secrets"]

    @pytest.mark.parametrize(
        "payload, expected",
        [
            (
                [
                    {
                        "name": "My Main Postgres DB",
                        "key": "postgres_key",
                        "connection_type": "postgres",
                        "access": "write",
                        "secrets": {
                            "username": "test",
                            "password": "test",
                            "dbname": "test",
                            "db_schema": "test",
                        },
                        "port": 5432,
                    },
                ],
                200,
            ),
            (
                [
                    {
                        "instance_key": "mailchimp_instance_1",
                        "secrets": {
                            "bad": "test_mailchimp",
                        },
                        "name": "My Mailchimp Test",
                        "description": "Mailchimp ConnectionConfig description",
                        "saas_connector_type": "mailchimp",
                        "key": "mailchimp_1",
                    },
                ],
                422,
            ),
        ],
    )
    def test_patch_connection_invalid_secrets(
        self, payload, expected, url, api_client, generate_auth_header
    ):
        # extra fields are ignored but missing fields are still invalid
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == expected

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
        assert postgres_resource.secrets == payload[0]["secrets"]
        assert postgres_connection["name"] == "My Main Postgres DB"
        assert postgres_connection["key"] == "postgres_db_1"
        assert postgres_connection["connection_type"] == "postgres"
        assert postgres_connection["access"] == "write"
        assert postgres_connection["created_at"] is not None
        assert postgres_connection["updated_at"] is not None
        assert postgres_connection["last_test_timestamp"] is None
        assert postgres_connection["disabled"] is False
        assert postgres_connection["secrets"]["password"] == "**********"
        # assert "secrets" not in postgres_connection

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
        assert mongo_connection["secrets"] is None

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
            == "List should have at most 50 items after validation, not 51"
        )

    @mock.patch("fides.api.util.connection_util.queue_privacy_request")
    def test_disable_manual_webhook(
        self,
        mock_queue,
        db,
        url,
        generate_auth_header,
        api_client,
        privacy_request_requires_input,
        integration_manual_webhook_config,
        access_manual_webhook,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])

        # Update resources
        payload = [
            {
                "name": integration_manual_webhook_config.name,
                "key": integration_manual_webhook_config.key,
                "connection_type": ConnectionType.manual_webhook.value,
                "access": "write",
                "disabled": True,
            }
        ]

        response = api_client.patch(
            V1_URL_PREFIX + CONNECTIONS, headers=auth_header, json=payload
        )

        assert 200 == response.status_code

        assert (
            mock_queue.called
        ), "Disabling this last webhook caused 'requires_input' privacy requests to be queued"
        assert (
            mock_queue.call_args.kwargs["privacy_request_id"]
            == privacy_request_requires_input.id
        )
        db.refresh(privacy_request_requires_input)
        assert (
            privacy_request_requires_input.status == PrivacyRequestStatus.in_processing
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
                "secrets": {
                    "url": None,
                    "host": "http://localhost",
                    "port": 5432,
                    "dbname": "test",
                    "db_schema": "test",
                    "username": "test",
                    "password": "test",
                },
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
            {
                "key": "manual_webhook_type",
                "name": "Third Party Manual Webhook",
                "connection_type": "manual_webhook",
                "access": "read",
            },
        ]

        response = api_client.patch(
            V1_URL_PREFIX + CONNECTIONS, headers=auth_header, json=payload
        )

        assert 200 == response.status_code
        response_body = response.json()
        assert len(response_body) == 2
        assert len(response_body["succeeded"]) == 9
        assert len(response_body["failed"]) == 0

        postgres_connection = response_body["succeeded"][0]
        assert postgres_connection["access"] == "read"
        assert postgres_connection["disabled"] is True
        assert postgres_connection["secrets"]["password"] == "**********"
        assert postgres_connection["updated_at"] is not None
        postgres_resource = (
            db.query(ConnectionConfig).filter_by(key="postgres_db_1").first()
        )
        assert postgres_resource.access.value == "read"
        assert postgres_resource.disabled

        assert postgres_resource.secrets == payload[0]["secrets"]

        mongo_connection = response_body["succeeded"][1]
        assert mongo_connection["access"] == "write"
        assert mongo_connection["disabled"] is False
        assert mongo_connection["updated_at"] is not None
        mongo_resource = db.query(ConnectionConfig).filter_by(key="my_mongo_db").first()
        assert mongo_resource.access.value == "write"
        assert mongo_connection["secrets"] is None
        assert not mongo_resource.disabled

        mysql_connection = response_body["succeeded"][2]
        assert mysql_connection["access"] == "read"
        assert mysql_connection["updated_at"] is not None
        mysql_resource = db.query(ConnectionConfig).filter_by(key="my_mysql_db").first()
        assert mysql_resource.access.value == "read"
        assert mysql_connection["secrets"] is None

        mssql_connection = response_body["succeeded"][3]
        assert mssql_connection["access"] == "write"
        assert mssql_connection["updated_at"] is not None
        mssql_resource = db.query(ConnectionConfig).filter_by(key="my_mssql_db").first()
        assert mssql_resource.access.value == "write"
        assert mssql_connection["secrets"] is None

        mariadb_connection = response_body["succeeded"][4]
        assert mariadb_connection["access"] == "write"
        assert mariadb_connection["updated_at"] is not None
        mariadb_resource = (
            db.query(ConnectionConfig).filter_by(key="my_mariadb_db").first()
        )
        assert mariadb_resource.access.value == "write"
        assert mariadb_connection["secrets"] is None

        bigquery_connection = response_body["succeeded"][5]
        assert bigquery_connection["access"] == "write"
        assert bigquery_connection["updated_at"] is not None
        bigquery_resource = (
            db.query(ConnectionConfig).filter_by(key="my_bigquery_db").first()
        )
        assert bigquery_resource.access.value == "write"
        assert bigquery_connection["secrets"] is None

        redshift_connection = response_body["succeeded"][6]
        assert redshift_connection["access"] == "read"
        assert redshift_connection["updated_at"] is not None
        redshift_resource = (
            db.query(ConnectionConfig).filter_by(key="my_redshift_cluster").first()
        )
        assert redshift_resource.access.value == "read"
        assert redshift_connection["secrets"] is None

        snowflake_connection = response_body["succeeded"][7]
        assert snowflake_connection["access"] == "write"
        assert snowflake_connection["updated_at"] is not None
        assert snowflake_connection["description"] == "Backup snowflake db"
        snowflake_resource = (
            db.query(ConnectionConfig).filter_by(key="my_snowflake").first()
        )
        assert snowflake_resource.access.value == "write"
        assert snowflake_resource.description == "Backup snowflake db"
        assert snowflake_connection["secrets"] is None

        manual_webhook_connection = response_body["succeeded"][8]
        assert manual_webhook_connection["access"] == "read"
        assert manual_webhook_connection["updated_at"] is not None
        manual_webhook_resource = (
            db.query(ConnectionConfig).filter_by(key="manual_webhook_type").first()
        )
        assert manual_webhook_resource.access.value == "read"
        assert manual_webhook_resource.connection_type == ConnectionType.manual_webhook
        assert manual_webhook_connection["secrets"] is None

        postgres_resource.delete(db)
        mongo_resource.delete(db)
        redshift_resource.delete(db)
        snowflake_resource.delete(db)
        mariadb_resource.delete(db)
        mysql_resource.delete(db)
        mssql_resource.delete(db)
        bigquery_resource.delete(db)
        manual_webhook_resource.delete(db)

    @mock.patch("fides.api.db.base_class.OrmWrappedFidesBase.create_or_update")
    def test_patch_connections_failed_response(
        self, mock_create: Mock, api_client: TestClient, generate_auth_header, url
    ) -> None:
        mock_create.side_effect = HTTPException(
            mock.Mock(status_code=400), "Test error"
        )

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
        response_body = response.json()
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

    @mock.patch("fides.api.main.prepare_and_log_request")
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

    @mock.patch("fides.api.main.prepare_and_log_request")
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

        assert call_args[0] == f"PATCH: http://testserver{url}"
        assert call_args[1] == "testserver"
        assert call_args[2] == 200
        assert isinstance(call_args[3], datetime)
        assert call_args[4] is None
        assert call_args[5] is None

    def test_patch_connections_no_name(self, api_client, generate_auth_header, url):
        # two connection configs without names
        payload = [
            {
                "key": "postgres_db_1",
                "connection_type": "postgres",
                "access": "write",
                "secrets": {
                    "url": None,
                    "host": "http://localhost",
                    "port": 5432,
                    "dbname": "test",
                    "db_schema": "test",
                    "username": "test",
                    "password": "test",
                },
            },
            {
                "key": "mongo_db_1",
                "connection_type": "mongodb",
                "access": "read",
            },
        ]
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        assert len(response.json()["succeeded"]) == 2
        assert response.json()["succeeded"][0]["name"] is None
        assert response.json()["succeeded"][1]["name"] is None

    def test_patch_connections_ignore_enabled_actions(
        self, db, api_client: TestClient, generate_auth_header, url
    ) -> None:
        payload = [
            {
                "name": "My Connection",
                "key": "my_connection",
                "connection_type": "postgres",
                "access": "write",
                "enabled_actions": ["access"],
            }
        ]

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 200 == response.status_code
        response_body = response.json()
        assert response_body["succeeded"][0]["enabled_actions"] is None

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "my_connection")
        ).first()
        assert connection_config.enabled_actions is None


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
            "saas_config",
            "secrets",
            "name",
            "last_test_timestamp",
            "last_test_succeeded",
            "key",
            "created_at",
            "disabled",
            "description",
            "authorized",
            "enabled_actions",
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

    @pytest.mark.integration_saas
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
        assert items[0]["saas_config"]["type"] == "stripe"

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

    @pytest.mark.unit_saas
    def test_filter_connection_type(
        self,
        db,
        connection_config,
        read_connection_config,
        api_client,
        generate_auth_header,
        saas_example_connection_config,
        url,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url + "?connection_type=postgres", headers=auth_header)
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

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url + "?connection_type=POSTGRES", headers=auth_header)
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

        resp = api_client.get(url + "?connection_type=custom", headers=auth_header)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        ordered = (
            db.query(ConnectionConfig)
            .filter(ConnectionConfig.key == saas_example_connection_config.key)
            .order_by(ConnectionConfig.name.asc())
            .all()
        )
        assert len(ordered) == 1
        assert ordered[0].key == items[0]["key"]

        resp = api_client.get(url + "?connection_type=CUSTOM", headers=auth_header)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        ordered = (
            db.query(ConnectionConfig)
            .filter(ConnectionConfig.key == saas_example_connection_config.key)
            .order_by(ConnectionConfig.name.asc())
            .all()
        )
        assert len(ordered) == 1
        assert ordered[0].key == items[0]["key"]

        resp = api_client.get(
            url + "?connection_type=custom&connection_type=postgres",
            headers=auth_header,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 3
        ordered = (
            db.query(ConnectionConfig)
            .filter(
                ConnectionConfig.key.in_(
                    [
                        read_connection_config.key,
                        connection_config.key,
                        saas_example_connection_config.key,
                    ]
                )
            )
            .order_by(ConnectionConfig.name.asc())
            .all()
        )
        assert len(ordered) == 3
        assert ordered[0].key == items[0]["key"]

    def test_orphaned_connections_filter(
        self, db, api_client: TestClient, generate_auth_header, url, system
    ):
        configs = []
        total_orphaned_configs = 10
        for i in range(0, total_orphaned_configs):
            data = {
                "name": str(uuid4()),
                "key": f"my_postgres_db_{i}_orphaned_read_config",
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.read,
                "secrets": integration_secrets["postgres_example"],
                "description": "Read-only connection config",
            }

            configs.append(
                ConnectionConfig.create(
                    db=db,
                    data=data,
                )
            )

        total_non_orphaned_configs = 12
        for i in range(0, total_non_orphaned_configs):
            data = {
                "name": str(uuid4()),
                "key": f"my_postgres_db_{i}_non_orphaned_read_config",
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.read,
                "secrets": integration_secrets["postgres_example"],
                "description": "Read-only connection config",
            }
            data["system_id"] = system.id

            configs.append(
                ConnectionConfig.create(
                    db=db,
                    data=data,
                )
            )
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])

        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200
        assert (
            len(resp.json()["items"])
            == total_orphaned_configs + total_non_orphaned_configs
        )

        resp = api_client.get(url + "?orphaned_from_system=True", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == total_orphaned_configs

        resp = api_client.get(url + "?orphaned_from_system=False", headers=auth_header)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == total_non_orphaned_configs

        for config in configs:
            config.delete(db)


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
            "saas_config",
            "secrets",
            "authorized",
            "enabled_actions",
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

    @mock.patch("fides.api.util.connection_util.queue_privacy_request")
    def test_delete_manual_webhook_connection_config(
        self,
        mock_queue,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        integration_manual_webhook_config,
        access_manual_webhook,
        privacy_request_requires_input,
    ) -> None:
        """Assert both the connection config and its webhook are deleted"""
        assert (
            db.query(AccessManualWebhook).filter_by(id=access_manual_webhook.id).first()
            is not None
        )

        assert (
            db.query(ConnectionConfig)
            .filter_by(key=integration_manual_webhook_config.key)
            .first()
            is not None
        )

        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{integration_manual_webhook_config.key}"
        auth_header = generate_auth_header(scopes=[CONNECTION_DELETE])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == 204

        assert (
            db.query(AccessManualWebhook).filter_by(id=access_manual_webhook.id).first()
            is None
        )

        assert (
            db.query(ConnectionConfig)
            .filter_by(key=integration_manual_webhook_config.key)
            .first()
            is None
        )
        assert (
            mock_queue.called
        ), "Deleting this last webhook caused 'requires_input' privacy requests to be queued"
        assert (
            mock_queue.call_args.kwargs["privacy_request_id"]
            == privacy_request_requires_input.id
        )
        db.refresh(privacy_request_requires_input)
        assert (
            privacy_request_requires_input.status == PrivacyRequestStatus.in_processing
        )

    def test_delete_saas_connection_config(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ) -> None:
        secrets = {
            "domain": "test_hubspot_domain",
            "private_app_token": "test_hubspot_api_key",
        }
        connection_config, dataset_config = instantiate_connector(
            db,
            "hubspot",
            "secondary_hubspot_instance",
            "hubspot ConnectionConfig description",
            secrets,
        )
        dataset = dataset_config.ctl_dataset

        auth_header = generate_auth_header(scopes=[CONNECTION_DELETE])
        resp = api_client.delete(
            f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}", headers=auth_header
        )
        assert resp.status_code == 204
        assert (
            db.query(ConnectionConfig).filter_by(key=connection_config.key).first()
            is None
        )
        assert db.query(DatasetConfig).filter_by(id=dataset_config.id).first() is None
        assert db.query(Dataset).filter_by(id=dataset.id).first() is None


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
        payload = {
            "host": "host.docker.internal",
            "dbname": "postgres_example",
            "incorrect_postgres_uri_component": "test-1",
        }
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200

        payload = {"dbname": "my_db"}
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            resp.json()["detail"][0]["msg"]
            == "Value error, PostgreSQLSchema must be supplied all of: ['host', 'dbname']."
        )

        payload = {
            "host": "host.docker.internal",
            "dbname": "postgres_example",
            "port": "cannot be turned into an integer",
        }
        resp = api_client.put(
            url,
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            json.loads(resp.text)["detail"][0]["msg"]
            == "Input should be a valid integer, unable to parse string as an integer"
        )
        assert set(resp.json()["detail"][0].keys()) == {
            "loc",
            "msg",
            "type",
        }  # Assert url, input, ctx keys have been removed to suppress sensitive information

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
        payload = {
            "host": "localhost",
            "port": "1234",
            "dbname": "my_test_db",
        }
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
            "db_schema": None,
            "ssh_required": False,
        }
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

    def test_put_sovrn_connection_config_secrets(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        sovrn_email_connection_config,
    ) -> None:
        """Note: this test does not attempt to send an email, via use of verify query param."""
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{sovrn_email_connection_config.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "test_email_address": "processor_address@example.com",
            "recipient_email_address": "sovrn@example.com",
            "advanced_settings": {
                "identity_types": {
                    "email": False,
                    "phone_number": False,
                    "cookie_ids": ["ljt_readerID"],
                }
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
            == f"Secrets updated for ConnectionConfig with key: {sovrn_email_connection_config.key}."
        )
        db.refresh(sovrn_email_connection_config)

        assert sovrn_email_connection_config.secrets == {
            "test_email_address": "processor_address@example.com",
            "recipient_email_address": "sovrn@example.com",
            "advanced_settings": {
                "identity_types": {
                    "email": False,
                    "phone_number": False,
                    "cookie_ids": ["ljt_readerID"],
                },
            },
            "third_party_vendor_name": "Sovrn",
        }
        assert sovrn_email_connection_config.last_test_timestamp is None
        assert sovrn_email_connection_config.last_test_succeeded is None

    def test_put_sovrn_connection_config_secrets_missing(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        sovrn_email_connection_config,
    ) -> None:
        """
        Test that the request uses default AdvancedSettings if none are provided
        """

        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{sovrn_email_connection_config.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "test_email_address": "processor_address@example.com",
            "recipient_email_address": "sovrn@example.com",
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200

    def test_put_dynamic_erasure_email_connection_config_secrets(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        dynamic_erasure_email_connection_config_no_secrets,
        dynamic_email_address_config_dataset_config,
    ) -> None:
        """Note: this test does not attempt to send an email, via use of verify query param."""
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{dynamic_erasure_email_connection_config_no_secrets.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "test_email_address": "test@example.com",
            "third_party_vendor_name": {
                "dataset": dynamic_email_address_config_dataset_config.fides_key,
                "field": "dynamic_email_address_config.vendor_name",
                "direction": "from",
            },
            "recipient_email_address": {
                "dataset": dynamic_email_address_config_dataset_config.fides_key,
                "field": "dynamic_email_address_config.email_address",
                "direction": "from",
            },
            "advanced_settings": {
                "identity_types": {
                    "email": True,
                    "phone_number": False,
                }
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
            == f"Secrets updated for ConnectionConfig with key: {dynamic_erasure_email_connection_config_no_secrets.key}."
        )
        db.refresh(dynamic_erasure_email_connection_config_no_secrets)

        assert dynamic_erasure_email_connection_config_no_secrets.secrets == {
            "test_email_address": "test@example.com",
            "recipient_email_address": {
                "dataset": dynamic_email_address_config_dataset_config.fides_key,
                "field": "dynamic_email_address_config.email_address",
                "direction": "from",
            },
            "advanced_settings": {
                "identity_types": {
                    "email": True,
                    "phone_number": False,
                }
            },
            "third_party_vendor_name": {
                "dataset": dynamic_email_address_config_dataset_config.fides_key,
                "field": "dynamic_email_address_config.vendor_name",
                "direction": "from",
            },
        }
        assert (
            dynamic_erasure_email_connection_config_no_secrets.last_test_timestamp
            is None
        )
        assert (
            dynamic_erasure_email_connection_config_no_secrets.last_test_succeeded
            is None
        )

    def test_put_dynamic_erasure_email_connection_config_invalid_secrets(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        dynamic_erasure_email_connection_config_no_secrets,
    ) -> None:
        """Note: this test does not attempt to send an email, via use of verify query param."""
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{dynamic_erasure_email_connection_config_no_secrets.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "test_email_address": "test@example.com",
            "third_party_vendor_name": {
                "dataset": "nonexistent_dataset",
                "field": "dynamic_email_address_config.vendor_name",
                "direction": "from",
            },
            "recipient_email_address": {
                "dataset": "nonexistent_dataset",
                "field": "dynamic_email_address_config.email_address",
                "direction": "from",
            },
            "advanced_settings": {
                "identity_types": {
                    "email": True,
                    "phone_number": False,
                }
            },
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            json.loads(resp.text)["detail"]
            == "Unknown dataset 'nonexistent_dataset' referenced by external reference"
        )
        db.refresh(dynamic_erasure_email_connection_config_no_secrets)

        assert dynamic_erasure_email_connection_config_no_secrets.secrets == None
        assert (
            dynamic_erasure_email_connection_config_no_secrets.last_test_timestamp
            is None
        )
        assert (
            dynamic_erasure_email_connection_config_no_secrets.last_test_succeeded
            is None
        )

    def test_put_dynamic_erasure_email_connection_config_mismatched_datasets(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        dynamic_erasure_email_connection_config_no_secrets,
        dynamic_email_address_config_dataset_config,
        dynamic_email_address_config_dataset_config_second_dataset,
    ) -> None:
        """Note: this test does not attempt to send an email, via use of verify query param."""
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{dynamic_erasure_email_connection_config_no_secrets.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "test_email_address": "test@example.com",
            "third_party_vendor_name": {
                "dataset": dynamic_email_address_config_dataset_config.fides_key,
                "field": "dynamic_email_address_config.vendor_name",
                "direction": "from",
            },
            "recipient_email_address": {
                "dataset": dynamic_email_address_config_dataset_config_second_dataset.fides_key,
                "field": "dynamic_email_address_config.email_address",
                "direction": "from",
            },
            "advanced_settings": {
                "identity_types": {
                    "email": True,
                    "phone_number": False,
                }
            },
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            json.loads(resp.text)["detail"]
            == "Recipient email address and third party vendor name must reference the same dataset"
        )
        db.refresh(dynamic_erasure_email_connection_config_no_secrets)

        assert dynamic_erasure_email_connection_config_no_secrets.secrets == None
        assert (
            dynamic_erasure_email_connection_config_no_secrets.last_test_timestamp
            is None
        )
        assert (
            dynamic_erasure_email_connection_config_no_secrets.last_test_succeeded
            is None
        )

    def test_put_dynamic_erasure_email_connection_config_mismatched_collections(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        dynamic_erasure_email_connection_config_no_secrets,
        dynamic_email_address_config_dataset_config_second_dataset,
    ) -> None:
        """Note: this test does not attempt to send an email, via use of verify query param."""
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{dynamic_erasure_email_connection_config_no_secrets.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "test_email_address": "test@example.com",
            "third_party_vendor_name": {
                "dataset": dynamic_email_address_config_dataset_config_second_dataset.fides_key,
                "field": "dynamic_email_address_config.vendor_name",
                "direction": "from",
            },
            "recipient_email_address": {
                "dataset": dynamic_email_address_config_dataset_config_second_dataset.fides_key,
                "field": "dynamic_email_address_config_2.email_address2",
                "direction": "from",
            },
            "advanced_settings": {
                "identity_types": {
                    "email": True,
                    "phone_number": False,
                }
            },
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            json.loads(resp.text)["detail"]
            == "Recipient email address and third party vendor name must reference the same collection"
        )
        db.refresh(dynamic_erasure_email_connection_config_no_secrets)

        assert dynamic_erasure_email_connection_config_no_secrets.secrets == None
        assert (
            dynamic_erasure_email_connection_config_no_secrets.last_test_timestamp
            is None
        )
        assert (
            dynamic_erasure_email_connection_config_no_secrets.last_test_succeeded
            is None
        )

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
            "ssh_required": False,
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
            "user": "awsuser",
            "password": "test_password",
            "database": "dev",
            "db_schema": "test",
            "ssh_required": False,
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
            "dataset": "some-dataset",
        }
        assert bigquery_connection_config_without_secrets.last_test_timestamp is None
        assert bigquery_connection_config_without_secrets.last_test_succeeded is None

        payload = {
            "dataset": "some-dataset",
            "keyfile_creds": "bad_creds",
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert set(resp.json()["detail"][0].keys()) == {
            "type",
            "loc",
            "msg",
        }  # url, input, and ctx have been removed to help suppress sensitive information

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
            "warehouse_name": "warehouse",
            "schema_name": "schema",
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
            "private_key": None,
            "private_key_passphrase": None,
            "schema_name": "schema",
            "warehouse_name": "warehouse",
            "role_name": None,
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

    def test_put_datahub_connection_config_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        datahub_connection_config_no_secrets,
    ):
        """
        Note: this test does not call DataHub, via use of verify query param.
        """
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{datahub_connection_config_no_secrets.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "datahub_server_url": "https://datahub.example.com",
            "datahub_token": "test",
            "frequency": "weekly",
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        assert (
            json.loads(resp.text)["msg"]
            == f"Secrets updated for ConnectionConfig with key: {datahub_connection_config_no_secrets.key}."
        )

        db.refresh(datahub_connection_config_no_secrets)
        assert datahub_connection_config_no_secrets.secrets == {
            "datahub_server_url": "https://datahub.example.com",
            "datahub_token": "test",
            "frequency": "weekly",
        }
        assert datahub_connection_config_no_secrets.last_test_timestamp is None
        assert datahub_connection_config_no_secrets.last_test_succeeded is None

    def test_put_datahub_connection_config_secrets_default_frequency(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        datahub_connection_config_no_secrets,
    ):
        """
        Note: this test does not call DataHub, via use of verify query param.
        """
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{datahub_connection_config_no_secrets.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "datahub_server_url": "https://datahub.example.com",
            "datahub_token": "test",
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 200
        assert (
            json.loads(resp.text)["msg"]
            == f"Secrets updated for ConnectionConfig with key: {datahub_connection_config_no_secrets.key}."
        )

        db.refresh(datahub_connection_config_no_secrets)
        assert datahub_connection_config_no_secrets.secrets == {
            "datahub_server_url": "https://datahub.example.com",
            "datahub_token": "test",
            "frequency": "daily",
        }
        assert datahub_connection_config_no_secrets.last_test_timestamp is None
        assert datahub_connection_config_no_secrets.last_test_succeeded is None

    def test_put_datahub_connection_config_secrets_missing_url(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        datahub_connection_config_no_secrets,
    ):
        """
        Note: this test does not call DataHub, via use of verify query param.
        """
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{datahub_connection_config_no_secrets.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {"datahub_token": "test", "frequency": "weekly"}
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            resp.json()["detail"][0]["msg"]
            == "Value error, DatahubSchema must be supplied all of: ['datahub_server_url', 'datahub_token']."
        )

    def test_put_datahub_connection_config_secrets_missing_token(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        datahub_connection_config_no_secrets,
    ):
        """
        Note: this test does not call DataHub, via use of verify query param.
        """
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{datahub_connection_config_no_secrets.key}/secret"
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        payload = {
            "datahub_server_url": "https://datahub.example.com",
            "frequency": "weekly",
        }
        resp = api_client.put(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )
        assert resp.status_code == 422
        assert (
            resp.json()["detail"][0]["msg"]
            == "Value error, DatahubSchema must be supplied all of: ['datahub_server_url', 'datahub_token']."
        )

    @pytest.mark.unit_saas
    def test_put_saas_example_connection_config_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        saas_example_connection_config,
        saas_example_dataset_config,
        saas_external_example_dataset_config,
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
    def test_put_saas_example_connection_config_secrets_invalid_external_reference(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        saas_example_connection_config,
        saas_example_dataset_config,
        saas_external_example_dataset_config,
        saas_example_secrets,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = (
            f"{V1_URL_PREFIX}{CONNECTIONS}/{saas_example_connection_config.key}/secret"
        )

        # replace external reference entry with a pointer to an invalid dataset
        saas_example_secrets["customer_id"]["dataset"] = "non_existent_dataset"

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
            == f"Unknown dataset 'non_existent_dataset' referenced by external reference"
        )

        db.refresh(saas_example_connection_config)
        assert saas_example_connection_config.secrets != saas_example_secrets

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


class TestPatchConnectionConfigSecrets:
    def test_patch_connection_config_secrets_not_authenticated(
        self, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}/secret"
        resp = api_client.patch(url, headers={})
        assert resp.status_code == 401

    def test_patch_connection_config_secrets_wrong_scope(
        self, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}/secret"
        resp = api_client.patch(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_patch_connection_config_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
    ) -> None:
        """Note: this test does not attempt to actually connect to the db, via use of verify query param."""
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{connection_config.key}/secret"
        payload = {
            "host": "localhost",
            "port": "1234",
        }
        resp = api_client.patch(
            url + "?verify=False",
            headers=auth_header,
            json=payload,
        )

        previous_secrets = connection_config.secrets
        assert resp.status_code == 200
        assert (
            json.loads(resp.text)["msg"]
            == f"Secrets updated for ConnectionConfig with key: {connection_config.key}."
        )
        db.refresh(connection_config)
        assert connection_config.secrets == {
            "host": "localhost",
            "port": 1234,
            "dbname": previous_secrets["dbname"],
            "username": previous_secrets["username"],
            "password": previous_secrets["password"],
            "db_schema": None,  # Was not set in the payload nor in the fixture
            "ssh_required": False,  # Was not set in the payload nor in the fixture
        }
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

    def test_patch_connection_config_bigquery_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        bigquery_connection_config_without_secrets,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{bigquery_connection_config_without_secrets.key}/secret"

        # First we populate the secrets with a PUT request
        put_payload = {
            "dataset": "some-dataset",
            "keyfile_creds": {
                "type": "service_account",
                "project_id": "project-12345",
                "private_key_id": "qo28cy4nlwu",
                "private_key": "test_private_key",
                "client_email": "something@project-12345.iam.gserviceaccount.com",
                "client_id": "287345028734538",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/something%40project-12345.iam.gserviceaccount.com",
            },
        }
        resp = api_client.patch(
            url + "?verify=False",
            headers=auth_header,
            json=put_payload,
        )
        assert resp.status_code == 200

        # Change a single field
        payload = {
            "dataset": "new-dataset",
        }
        resp = api_client.patch(
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

        # Only dataset should have changed
        assert bigquery_connection_config_without_secrets.secrets == {
            "keyfile_creds": put_payload["keyfile_creds"],
            "dataset": "new-dataset",
        }
        assert bigquery_connection_config_without_secrets.last_test_timestamp is None
        assert bigquery_connection_config_without_secrets.last_test_succeeded is None

    def test_patch_http_connection_config_secrets(
        self,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        https_connection_config,
    ) -> None:
        """Note: HTTP Connection Configs don't attempt to test secrets"""
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        url = f"{V1_URL_PREFIX}{CONNECTIONS}/{https_connection_config.key}/secret"
        payload = {"authorization": "test_authorization123"}

        resp = api_client.patch(
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
            "url": "http://example.com",  # original value
            "authorization": "test_authorization123",  # new value
        }
        assert https_connection_config.last_test_timestamp is None
        assert https_connection_config.last_test_succeeded is None

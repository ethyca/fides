import json
from unittest import mock

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from starlette.testclient import TestClient

from fides.api.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    SAAS_CONNECTION_INSTANTIATE,
    STORAGE_DELETE,
)
from fides.api.api.v1.urn_registry import V1_URL_PREFIX
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig

page_size = Params().size


@pytest.fixture(scope="function")
def url(system) -> str:
    return V1_URL_PREFIX + f"/system/{system.fides_key}/connection"


@pytest.fixture(scope="function")
def url_invalid_system() -> str:
    return V1_URL_PREFIX + f"/system/not-a-real-system/connection"


@pytest.fixture(scope="function")
def payload():
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
            "enabled_actions": ["access", "erasure"],
        }
    ]


class TestPatchSystemConnections:
    def test_patch_connections_valid_system(
        self, api_client: TestClient, generate_auth_header, url, payload
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        resp = api_client.patch(url, headers=auth_header, json=payload)

        assert resp.status_code == 200

    def test_patch_connections_with_invalid_system(
        self, api_client: TestClient, generate_auth_header, url_invalid_system
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        resp = api_client.patch(url_invalid_system, headers=auth_header, json=[])

        assert resp.status_code == HTTP_404_NOT_FOUND
        assert (
            resp.json()["detail"]
            == "A valid system must be provided to create or update connections"
        )


class TestGetConnections:
    def test_get_connections_not_authenticated(
        self, api_client: TestClient, generate_auth_header, connection_config, url
    ) -> None:
        resp = api_client.get(url, headers={})
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_get_connections_with_invalid_system(
        self, api_client: TestClient, generate_auth_header, url_invalid_system
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url_invalid_system, headers=auth_header)

        assert (
            resp.json()["detail"]
            == "A valid system must be provided to create or update connections"
        )
        assert resp.status_code == HTTP_404_NOT_FOUND

    def test_get_connections_wrong_scope(
        self, api_client: TestClient, generate_auth_header, connection_config, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[STORAGE_DELETE])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_get_connection_configs(
        self,
        api_client: TestClient,
        generate_auth_header,
        connection_config,
        url,
        db: Session,
    ) -> None:
        connections = [
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
            {
                "name": "My Mongo DB",
                "connection_type": "mongodb",
                "access": "read",
                "key": "mongo-db-key",
            },
            {
                "secrets": {
                    "domain": "test_mailchimp_domain",
                    "username": "test_mailchimp_username",
                    "api_key": "test_mailchimp_api_key",
                },
                "name": "My Mailchimp Test",
                "description": "Mailchimp ConnectionConfig description",
                "key": "mailchimp-asdfasdf-asdftgg-dfgdfg",
                "connection_type": "saas",
                "saas_connector_type": "mailchimp",
                "access": "read",
            },
        ]

        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        api_client.patch(url, headers=auth_header, json=connections)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200

        response_body = json.loads(resp.text)
        assert len(response_body["items"]) == 3
        connection = response_body["items"][0]
        assert set(connection.keys()) == {
            "connection_type",
            "access",
            "updated_at",
            "saas_config",
            "name",
            "last_test_timestamp",
            "last_test_succeeded",
            "key",
            "created_at",
            "disabled",
            "description",
        }
        connection_keys = [connection["key"] for connection in connections]
        assert response_body["items"][0]["key"] in connection_keys
        assert response_body["items"][1]["key"] in connection_keys
        assert response_body["items"][2]["key"] in connection_keys

        assert response_body["total"] == 3
        assert response_body["page"] == 1
        assert response_body["size"] == page_size


class TestInstantiateSystemConnectionFromTemplate:
    @pytest.fixture(scope="function")
    def base_url(self, system) -> str:
        return f"{V1_URL_PREFIX}/system/{system.fides_key}/connection/instantiate/{{saas_connector_type}}"

    def test_instantiate_connection_not_authenticated(self, api_client, base_url):
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"), headers={}
        )
        assert resp.status_code == 401

    def test_instantiate_connection_wrong_scope(
        self, generate_auth_header, api_client, base_url
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"), headers=auth_header
        )
        assert resp.status_code == 403

    def test_instantiate_nonexistent_template(
        self, generate_auth_header, api_client, base_url
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "test_instance_key",
            "secrets": {},
            "name": "Unsupported Connector",
            "description": "Unsupported connector description",
            "key": "unsupported_connector",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="does_not_exist"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 404
        assert (
            resp.json()["detail"]
            == f"SaaS connector type 'does_not_exist' is not yet available in Fidesops. For a list of available SaaS connectors, refer to /connection_type."
        )

    def test_instance_key_already_exists(
        self, generate_auth_header, api_client, base_url, dataset_config
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": dataset_config.fides_key,
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 400
        assert (
            resp.json()["detail"]
            == f"SaaS connector instance key '{dataset_config.fides_key}' already exists."
        )

    def test_template_secrets_validation(
        self, generate_auth_header, api_client, base_url, db
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        # Secrets have one field missing, one field extra
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "bad_mailchimp_secret_key": "bad_key",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )

        assert resp.status_code == 422
        assert resp.json()["detail"][0] == {
            "loc": ["domain"],
            "msg": "field required",
            "type": "value_error.missing",
        }
        assert resp.json()["detail"][1] == {
            "loc": ["bad_mailchimp_secret_key"],
            "msg": "extra fields not permitted",
            "type": "value_error.extra",
        }

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        assert connection_config is None, "ConnectionConfig not persisted"

    def test_connection_config_key_already_exists(
        self, db, generate_auth_header, api_client, base_url, connection_config
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": connection_config.name,
            "description": "Mailchimp ConnectionConfig description",
            "key": connection_config.key,
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 400
        assert (
            f"Key {connection_config.key} already exists in ConnectionConfig"
            in resp.json()["detail"]
        )

    def test_connection_config_name_already_exists(
        self, db, generate_auth_header, api_client, base_url, connection_config
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": connection_config.name,
            "description": "Mailchimp ConnectionConfig description",
            "key": "brand_new_key",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 400
        assert (
            f"Name {connection_config.name} already exists in ConnectionConfig"
            in resp.json()["detail"]
        )

    def test_create_connection_from_template_without_supplying_connection_key(
        self, db, generate_auth_header, api_client, base_url
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 200

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.name == "Mailchimp Connector")
        ).first()
        dataset_config = DatasetConfig.filter(
            db=db,
            conditions=(DatasetConfig.fides_key == "secondary_mailchimp_instance"),
        ).first()

        assert connection_config is not None
        assert dataset_config is not None

        assert connection_config.key == "mailchimp_connector"
        dataset_config.delete(db)
        connection_config.delete(db)

    def test_invalid_instance_key(self, db, generate_auth_header, api_client, base_url):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "< this is an invalid key! >",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.json()["detail"][0] == {
            "loc": ["body", "instance_key"],
            "msg": "FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: < this is an invalid key! >",
            "type": "value_error.fidesvalidation",
        }

    @mock.patch(
        "fides.api.api.v1.endpoints.saas_config_endpoints.upsert_dataset_config_from_template"
    )
    def test_dataset_config_saving_fails(
        self, mock_create_dataset, db, generate_auth_header, api_client, base_url
    ):
        mock_create_dataset.side_effect = Exception("KeyError")

        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 500
        assert (
            resp.json()["detail"]
            == "SaaS Connector could not be created from the 'mailchimp' template at this time."
        )

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        assert connection_config is None

        dataset_config = DatasetConfig.filter(
            db=db,
            conditions=(DatasetConfig.fides_key == "secondary_mailchimp_instance"),
        ).first()
        assert dataset_config is None

    def test_instantiate_connection_from_template(
        self, db, generate_auth_header, api_client, base_url
    ):
        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        assert connection_config is None

        dataset_config = DatasetConfig.filter(
            db=db,
            conditions=(DatasetConfig.fides_key == "secondary_mailchimp_instance"),
        ).first()
        assert dataset_config is None

        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )

        assert resp.status_code == 200
        assert set(resp.json().keys()) == {"connection", "dataset"}
        connection_data = resp.json()["connection"]
        assert connection_data["key"] == "mailchimp_connection_config"
        assert connection_data["name"] == "Mailchimp Connector"
        assert "secrets" not in connection_data

        dataset_data = resp.json()["dataset"]
        assert dataset_data["fides_key"] == "secondary_mailchimp_instance"

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        dataset_config = DatasetConfig.filter(
            db=db,
            conditions=(DatasetConfig.fides_key == "secondary_mailchimp_instance"),
        ).first()

        assert connection_config is not None
        assert dataset_config is not None
        assert connection_config.name == "Mailchimp Connector"
        assert connection_config.description == "Mailchimp ConnectionConfig description"

        assert connection_config.access == AccessLevel.write
        assert connection_config.connection_type == ConnectionType.saas
        assert connection_config.saas_config is not None
        assert connection_config.disabled is False
        assert connection_config.disabled_at is None
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

        assert dataset_config.connection_config_id == connection_config.id
        assert dataset_config.ctl_dataset_id is not None

        dataset_config.delete(db)
        connection_config.delete(db)
        dataset_config.ctl_dataset.delete(db=db)

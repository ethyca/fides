from typing import List
from unittest import mock

import pytest
from fideslib.models.client import ClientDetail
from starlette.testclient import TestClient

from fidesops.ops.api.v1.scope_registry import (
    CONNECTION_READ,
    CONNECTION_TYPE_READ,
    SAAS_CONNECTION_INSTANTIATE,
)
from fidesops.ops.api.v1.urn_registry import (
    CONNECTION_TYPE_SECRETS,
    CONNECTION_TYPES,
    SAAS_CONNECTOR_FROM_TEMPLATE,
    V1_URL_PREFIX,
)
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.schemas.connection_configuration.connection_config import (
    ConnectionSystemTypeMap,
    SystemType,
)
from fidesops.ops.schemas.saas.saas_config import SaaSType


class TestGetConnections:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + CONNECTION_TYPES

    def test_get_connection_types_not_authenticated(self, api_client, url):
        resp = api_client.get(url, headers={})
        assert resp.status_code == 401

    def test_get_connection_types_forbidden(
        self, api_client, url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 403

    def test_get_connection_types(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(url, headers=auth_header)
        data = resp.json()["items"]
        assert resp.status_code == 200
        assert len(data) == 21

        assert {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
        } in data
        assert {
            "identifier": SaaSType.stripe.value,
            "type": SystemType.saas.value,
        } in data

        assert "saas" not in [item["identifier"] for item in data]
        assert "https" not in [item["identifier"] for item in data]
        assert "custom" not in [item["identifier"] for item in data]
        assert "manual" not in [item["identifier"] for item in data]

    def test_search_connection_types(self, api_client, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        resp = api_client.get(url + "?search=str", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 1
        assert data[0] == {
            "identifier": SaaSType.stripe.value,
            "type": SystemType.saas.value,
        }

        resp = api_client.get(url + "?search=re", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 3
        assert data == [
            {
                "identifier": ConnectionType.postgres.value,
                "type": SystemType.database.value,
            },
            {
                "identifier": ConnectionType.redshift.value,
                "type": SystemType.database.value,
            },
            {"identifier": SaaSType.outreach.value, "type": SystemType.saas.value},
        ]

    def test_search_system_type(self, api_client, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        resp = api_client.get(url + "?system_type=nothing", headers=auth_header)
        assert resp.status_code == 422

        resp = api_client.get(url + "?system_type=saas", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 13

        resp = api_client.get(url + "?system_type=database", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 8

    def test_search_system_type_and_connection_type(
        self, api_client, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        resp = api_client.get(url + "?search=str&system_type=saas", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 1

        resp = api_client.get(
            url + "?search=re&system_type=database", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 2


class TestGetConnectionSecretSchema:
    @pytest.fixture(scope="function")
    def base_url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + CONNECTION_TYPE_SECRETS

    def test_get_connection_secret_schema_not_authenticated(self, api_client, base_url):
        resp = api_client.get(base_url.format(connection_type="sentry"), headers={})
        assert resp.status_code == 401

    def test_get_connection_secret_schema_forbidden(
        self, api_client, base_url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(
            base_url.format(connection_type="sentry"), headers=auth_header
        )
        assert resp.status_code == 403

    def test_get_connection_secret_schema_not_found(
        self, api_client: TestClient, generate_auth_header, base_url
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="connection_type_we_do_not_support"),
            headers=auth_header,
        )
        assert resp.status_code == 404
        assert (
            resp.json()["detail"]
            == "No connection type found with name 'connection_type_we_do_not_support'."
        )

    def test_get_connection_secret_schema_mongodb(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="mongodb"), headers=auth_header
        )
        assert resp.json() == {
            "title": "MongoDBSchema",
            "description": "Schema to validate the secrets needed to connect to a MongoDB Database",
            "type": "object",
            "properties": {
                "url": {"title": "Url", "type": "string"},
                "username": {"title": "Username", "type": "string"},
                "password": {"title": "Password", "type": "string"},
                "host": {"title": "Host", "type": "string"},
                "port": {"title": "Port", "type": "integer"},
                "defaultauthdb": {"title": "Defaultauthdb", "type": "string"},
            },
            "additionalProperties": False,
        }

    def test_get_connection_secret_schema_hubspot(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="hubspot"), headers=auth_header
        )

        assert resp.json() == {
            "title": "hubspot_schema",
            "description": "Hubspot secrets schema",
            "type": "object",
            "properties": {
                "hapikey": {"title": "Hapikey", "type": "string"},
                "domain": {
                    "title": "Domain",
                    "default": "api.hubapi.com",
                    "type": "string",
                },
            },
            "required": ["hapikey"],
            "additionalProperties": False,
        }


class TestInstantiateConnectionFromTemplate:
    @pytest.fixture(scope="function")
    def base_url(self) -> str:
        return V1_URL_PREFIX + SAAS_CONNECTOR_FROM_TEMPLATE

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
            "msg": "FidesKey must only contain alphanumeric characters, '.', '_' or '-'.",
            "type": "value_error",
        }

    @mock.patch(
        "fidesops.ops.api.v1.endpoints.saas_config_endpoints.create_dataset_config_from_template"
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
        assert resp.json()["fides_key"] == "secondary_mailchimp_instance"

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
        assert dataset_config.dataset is not None

        dataset_config.delete(db)
        connection_config.delete(db)

import json

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from starlette.testclient import TestClient

from fides.api.ops.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    STORAGE_DELETE,
)
from fides.api.ops.api.v1.urn_registry import V1_URL_PREFIX
from tests.ops.api.v1.endpoints.test_connection_config_endpoints import (
    TestPatchConnections,
)

page_size = Params().size


@pytest.fixture(scope="function")
def url(system) -> str:
    return V1_URL_PREFIX + f"/system/{system.fides_key}/connection"


@pytest.fixture(scope="function")
def url_invalid_system() -> str:
    return V1_URL_PREFIX + f"/system/not-a-real-system/connection"


class TestPatchSystemConnections(TestPatchConnections):
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

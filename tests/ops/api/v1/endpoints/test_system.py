import json
from typing import Dict

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from starlette.testclient import TestClient

from fides.api.ops.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    POLICY_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    SYSTEM_DELETE,
    SYSTEM_UPDATE,
)
from fides.api.ops.api.v1.urn_registry import V1_URL_PREFIX
from fides.lib.oauth.roles import ADMIN, VIEWER
from tests.conftest import generate_role_header, generate_role_header_for_user
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


class TestSystemUpdate:

    updated_system_name = "Updated System Name"

    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + f"/system/?resource+type=system"

    @pytest.fixture(scope="function")
    def system_update_request_body(self, system) -> Dict:
        return {
            "fides_key": system.fides_key,
            "system_type": "Service",
            "data_responsibility_title": "Processor",
            "name": "Updated System Name",
            "privacy_declarations": [
                {
                    "name": "Collect data for marketing",
                    "data_categories": ["user.device.cookie_id"],
                    "data_use": "advertising",
                    "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                    "data_subjects": ["customer"],
                    "dataset_references": None,
                    "egress": None,
                    "ingress": None,
                }
            ],
        }

    def test_system_update_not_authenticated(self, api_client: TestClient, url):
        resp = api_client.put(url, headers={}, json=[])
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_system_update_no_direct_scope(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        system_update_request_body,
        db,
        system,
    ):
        auth_header = generate_auth_header(scopes=[POLICY_CREATE_OR_UPDATE])

        resp = api_client.put(url, headers=auth_header, json=system_update_request_body)
        assert resp.status_code == HTTP_403_FORBIDDEN

        db.refresh(system)
        assert system.name != self.updated_system_name

    def test_system_update_has_direct_scope(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        system_update_request_body,
        system,
        db,
    ):
        assert system.name != self.updated_system_name
        auth_header = generate_auth_header(scopes=[SYSTEM_UPDATE])

        resp = api_client.put(url, headers=auth_header, json=system_update_request_body)
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["name"] == self.updated_system_name

        db.refresh(system)
        assert system.name == self.updated_system_name

    def test_system_update_no_encompassing_role(
        self,
        api_client: TestClient,
        url,
        system_update_request_body,
        system,
        db,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[VIEWER])
        resp = api_client.put(url, headers=auth_header, json=system_update_request_body)
        assert resp.status_code == HTTP_403_FORBIDDEN

        db.refresh(system)
        assert system.name != self.updated_system_name

    def test_system_update_has_role_that_can_update_all_systems(
        self,
        api_client: TestClient,
        url,
        system_update_request_body,
        system,
        db,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[ADMIN])
        resp = api_client.put(url, headers=auth_header, json=system_update_request_body)
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["name"] == self.updated_system_name

        db.refresh(system)
        assert system.name == self.updated_system_name

    def test_system_update_as_system_manager(
        self,
        api_client: TestClient,
        url,
        system_update_request_body,
        system,
        db,
        generate_system_manager_header,
    ):
        auth_header = generate_system_manager_header([system.id])
        resp = api_client.put(url, headers=auth_header, json=system_update_request_body)
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["name"] == self.updated_system_name

        db.refresh(system)
        assert system.name == self.updated_system_name

    def test_system_update_as_system_manager_403_if_not_found(
        self,
        api_client: TestClient,
        url,
        system_update_request_body,
        system,
        db,
        generate_system_manager_header,
    ):
        auth_header = generate_system_manager_header([system.id])
        system_update_request_body["fides_key"] = "system-does-not-exist"
        resp = api_client.put(url, headers=auth_header, json=system_update_request_body)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_system_update_as_admin_404_if_not_found(
        self,
        api_client: TestClient,
        url,
        system_update_request_body,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[ADMIN])
        system_update_request_body["fides_key"] = "system-does-not-exist"
        resp = api_client.put(url, headers=auth_header, json=system_update_request_body)
        assert resp.status_code == HTTP_404_NOT_FOUND


class TestSystemDelete:
    @pytest.fixture(scope="function")
    def url(self, system) -> str:
        return V1_URL_PREFIX + f"/system/{system.fides_key}"

    def test_system_delete_not_authenticated(self, api_client: TestClient, url):
        resp = api_client.delete(url, headers={}, json=[])
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_system_delete_no_direct_scope(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_UPDATE])

        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_system_delete_has_direct_scope(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header(scopes=[SYSTEM_DELETE])

        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK

    def test_system_delete_no_encompassing_role(
        self,
        api_client: TestClient,
        url,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[VIEWER])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_system_delete_has_role_that_can_delete_systems(
        self,
        api_client: TestClient,
        url,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[ADMIN])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK

    def test_system_delete_as_system_manager(
        self,
        api_client: TestClient,
        url,
        system,
        generate_system_manager_header,
    ):
        auth_header = generate_system_manager_header([system.id])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK

    def test_admin_role_gets_404_if_system_not_found(
        self,
        api_client: TestClient,
        url,
        generate_role_header,
    ):
        auth_header = generate_role_header(roles=[ADMIN])
        resp = api_client.delete(
            V1_URL_PREFIX + f"/system/system_does_not_exist", headers=auth_header
        )
        assert resp.status_code == HTTP_404_NOT_FOUND

    def test_system_manager_gets_403_if_system_not_found(
        self, api_client: TestClient, url, system, generate_system_manager_header, db
    ):
        system.is_default = True
        db.add(system)
        db.commit()

        auth_header = generate_system_manager_header([system.id])
        resp = api_client.delete(
            V1_URL_PREFIX + f"/system/system_does_not_exist", headers=auth_header
        )
        assert resp.status_code == HTTP_403_FORBIDDEN

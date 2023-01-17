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

from fides.api.ops.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    STORAGE_DELETE,
)
from fides.api.ops.api.v1.urn_registry import CONNECTIONS, V1_URL_PREFIX
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.privacy_request import (
    PrivacyRequestStatus,
)
from fides.lib.models.client import ClientDetail
from tests.ops.api.v1.endpoints.test_connection_config_endpoints import TestPatchConnections

page_size = Params().size




class TestPatchSystemConnections(TestPatchConnections):
    @pytest.fixture(scope="function")
    def url(self, system) -> str:
        return V1_URL_PREFIX + f"/system/{system.fides_key}/connection"




# class TestGetConnections:
#     @pytest.fixture(scope="function")
#     def url(self, oauth_client: ClientDetail, policy) -> str:
#         return V1_URL_PREFIX + CONNECTIONS
#
#     def test_get_connections_not_authenticated(
#             self, api_client: TestClient, generate_auth_header, connection_config, url
#     ) -> None:
#         resp = api_client.get(url, headers={})
#         assert resp.status_code == 401
#
#     def test_get_connections_wrong_scope(
#             self, api_client: TestClient, generate_auth_header, connection_config, url
#     ) -> None:
#         auth_header = generate_auth_header(scopes=[STORAGE_DELETE])
#         resp = api_client.get(url, headers=auth_header)
#         assert resp.status_code == 403
#
#     def test_get_connection_configs(
#             self, api_client: TestClient, generate_auth_header, connection_config, url
#     ) -> None:
#         # Test get connection configs happy path
#         auth_header = generate_auth_header(scopes=[CONNECTION_READ])
#         resp = api_client.get(url, headers=auth_header)
#         assert resp.status_code == 200
#
#         response_body = json.loads(resp.text)
#         assert len(response_body["items"]) == 1
#         connection = response_body["items"][0]
#         assert set(connection.keys()) == {
#             "connection_type",
#             "access",
#             "updated_at",
#             "saas_config",
#             "name",
#             "last_test_timestamp",
#             "last_test_succeeded",
#             "key",
#             "created_at",
#             "disabled",
#             "description",
#         }
#
#         assert connection["key"] == "my_postgres_db_1"
#         assert connection["connection_type"] == "postgres"
#         assert connection["access"] == "write"
#         assert connection["updated_at"] is not None
#         assert connection["last_test_timestamp"] is None
#
#         assert response_body["total"] == 1
#         assert response_body["page"] == 1
#         assert response_body["size"] == page_size
#
#     def test_filter_connections_disabled_and_type(
#             self,
#             db,
#             connection_config,
#             disabled_connection_config,
#             read_connection_config,
#             redshift_connection_config,
#             mongo_connection_config,
#             api_client,
#             generate_auth_header,
#             url,
#     ):
#         auth_header = generate_auth_header(scopes=[CONNECTION_READ])
#
#         resp = api_client.get(url, headers=auth_header)
#         items = resp.json()["items"]
#         assert len(items) == 5
#
#         resp = api_client.get(url + "?connection_type=postgres", headers=auth_header)
#         items = resp.json()["items"]
#         assert len(items) == 3
#         assert all(
#             [con["connection_type"] == "postgres" for con in resp.json()["items"]]
#         )
#
#         resp = api_client.get(
#             url + "?connection_type=postgres&connection_type=redshift",
#             headers=auth_header,
#             )
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 4
#         assert all(
#             [
#                 con["connection_type"] in ["redshift", "postgres"]
#                 for con in resp.json()["items"]
#             ]
#         )
#
#         resp = api_client.get(
#             url + "?connection_type=postgres&disabled=false", headers=auth_header
#         )
#         assert resp.status_code == 200
#         items = resp.json()["items"]
#         assert len(items) == 2
#         assert all(
#             [con["connection_type"] in ["postgres"] for con in resp.json()["items"]]
#         )
#         assert all([con["disabled"] is False for con in resp.json()["items"]])
#
#         resp = api_client.get(
#             url + "?connection_type=postgres&disabled=True", headers=auth_header
#         )
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 1
#         assert all(
#             [con["connection_type"] in ["postgres"] for con in resp.json()["items"]]
#         )
#         assert all([con["disabled"] is True for con in resp.json()["items"]])
#
#     def test_filter_test_status(
#             self,
#             db,
#             connection_config,
#             disabled_connection_config,
#             read_connection_config,
#             redshift_connection_config,
#             mongo_connection_config,
#             api_client,
#             generate_auth_header,
#             url,
#     ):
#         mongo_connection_config.last_test_succeeded = True
#         mongo_connection_config.save(db)
#         redshift_connection_config.last_test_succeeded = False
#         redshift_connection_config.save(db)
#
#         auth_header = generate_auth_header(scopes=[CONNECTION_READ])
#         resp = api_client.get(url + "?test_status=passed", headers=auth_header)
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 1
#         assert items[0]["last_test_succeeded"] is True
#         assert items[0]["key"] == mongo_connection_config.key
#
#         resp = api_client.get(url + "?test_status=failed", headers=auth_header)
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 1
#         assert items[0]["last_test_succeeded"] is False
#         assert items[0]["key"] == redshift_connection_config.key
#
#         resp = api_client.get(url + "?test_status=untested", headers=auth_header)
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 3
#         assert [item["last_test_succeeded"] is None for item in items]
#
#     @pytest.mark.integration_saas
#     @pytest.mark.integration_stripe
#     def test_filter_system_type(
#             self,
#             db,
#             connection_config,
#             disabled_connection_config,
#             read_connection_config,
#             redshift_connection_config,
#             mongo_connection_config,
#             api_client,
#             generate_auth_header,
#             stripe_connection_config,
#             integration_manual_config,
#             url,
#     ):
#
#         auth_header = generate_auth_header(scopes=[CONNECTION_READ])
#         resp = api_client.get(url + "?system_type=saas", headers=auth_header)
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 1
#         assert items[0]["connection_type"] == "saas"
#         assert items[0]["key"] == stripe_connection_config.key
#         assert items[0]["saas_config"]["type"] == "stripe"
#
#         resp = api_client.get(url + "?system_type=database", headers=auth_header)
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 5
#
#         resp = api_client.get(url + "?system_type=manual", headers=auth_header)
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 1
#         assert items[0]["connection_type"] == "manual"
#         assert items[0]["key"] == integration_manual_config.key
#
#         # Conflicting filters
#         resp = api_client.get(
#             url + "?system_type=saas&connection_type=mongodb", headers=auth_header
#         )
#         items = resp.json()["items"]
#         assert resp.status_code == 200
#         assert len(items) == 0
#
#     def test_search_connections(
#             self,
#             db,
#             connection_config,
#             read_connection_config,
#             api_client: TestClient,
#             generate_auth_header,
#             url,
#     ):
#         auth_header = generate_auth_header(scopes=[CONNECTION_READ])
#
#         resp = api_client.get(url + "?search=primary", headers=auth_header)
#         assert resp.status_code == 200
#         assert len(resp.json()["items"]) == 1
#         assert "primary" in resp.json()["items"][0]["description"].lower()
#
#         resp = api_client.get(url + "?search=read", headers=auth_header)
#         assert resp.status_code == 200
#         assert len(resp.json()["items"]) == 1
#         assert "read" in resp.json()["items"][0]["description"].lower()
#
#         resp = api_client.get(url + "?search=nonexistent", headers=auth_header)
#         assert resp.status_code == 200
#         assert len(resp.json()["items"]) == 0
#
#         resp = api_client.get(url + "?search=postgres", headers=auth_header)
#         assert resp.status_code == 200
#         items = resp.json()["items"]
#         assert len(items) == 2
#
#         ordered = (
#             db.query(ConnectionConfig)
#             .filter(
#                 ConnectionConfig.key.in_(
#                     [read_connection_config.key, connection_config.key]
#                 )
#             )
#             .order_by(ConnectionConfig.name.asc())
#             .all()
#         )
#         assert len(ordered) == 2
#         assert ordered[0].key == items[0]["key"]
#         assert ordered[1].key == items[1]["key"]
#
#     @pytest.mark.unit_saas
#     def test_filter_connection_type(
#             self,
#             db,
#             connection_config,
#             read_connection_config,
#             api_client,
#             generate_auth_header,
#             saas_example_connection_config,
#             url,
#     ):
#         auth_header = generate_auth_header(scopes=[CONNECTION_READ])
#         resp = api_client.get(url + "?connection_type=postgres", headers=auth_header)
#         assert resp.status_code == 200
#         items = resp.json()["items"]
#         assert len(items) == 2
#
#         ordered = (
#             db.query(ConnectionConfig)
#             .filter(
#                 ConnectionConfig.key.in_(
#                     [read_connection_config.key, connection_config.key]
#                 )
#             )
#             .order_by(ConnectionConfig.name.asc())
#             .all()
#         )
#         assert len(ordered) == 2
#         assert ordered[0].key == items[0]["key"]
#         assert ordered[1].key == items[1]["key"]
#
#         auth_header = generate_auth_header(scopes=[CONNECTION_READ])
#         resp = api_client.get(url + "?connection_type=POSTGRES", headers=auth_header)
#         assert resp.status_code == 200
#         items = resp.json()["items"]
#         assert len(items) == 2
#
#         ordered = (
#             db.query(ConnectionConfig)
#             .filter(
#                 ConnectionConfig.key.in_(
#                     [read_connection_config.key, connection_config.key]
#                 )
#             )
#             .order_by(ConnectionConfig.name.asc())
#             .all()
#         )
#         assert len(ordered) == 2
#         assert ordered[0].key == items[0]["key"]
#         assert ordered[1].key == items[1]["key"]
#
#         resp = api_client.get(url + "?connection_type=custom", headers=auth_header)
#         assert resp.status_code == 200
#         items = resp.json()["items"]
#         assert len(items) == 1
#         ordered = (
#             db.query(ConnectionConfig)
#             .filter(ConnectionConfig.key == saas_example_connection_config.key)
#             .order_by(ConnectionConfig.name.asc())
#             .all()
#         )
#         assert len(ordered) == 1
#         assert ordered[0].key == items[0]["key"]
#
#         resp = api_client.get(url + "?connection_type=CUSTOM", headers=auth_header)
#         assert resp.status_code == 200
#         items = resp.json()["items"]
#         assert len(items) == 1
#         ordered = (
#             db.query(ConnectionConfig)
#             .filter(ConnectionConfig.key == saas_example_connection_config.key)
#             .order_by(ConnectionConfig.name.asc())
#             .all()
#         )
#         assert len(ordered) == 1
#         assert ordered[0].key == items[0]["key"]
#
#         resp = api_client.get(
#             url + "?connection_type=custom&connection_type=postgres",
#             headers=auth_header,
#             )
#         assert resp.status_code == 200
#         items = resp.json()["items"]
#         assert len(items) == 3
#         ordered = (
#             db.query(ConnectionConfig)
#             .filter(
#                 ConnectionConfig.key.in_(
#                     [
#                         read_connection_config.key,
#                         connection_config.key,
#                         saas_example_connection_config.key,
#                     ]
#                 )
#             )
#             .order_by(ConnectionConfig.name.asc())
#             .all()
#         )
#         assert len(ordered) == 3
#         assert ordered[0].key == items[0]["key"]

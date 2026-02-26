import pytest
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from starlette.testclient import TestClient

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.sql_models import System
from fides.common.api.scope_registry import (
    SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE,
    SYSTEM_INTEGRATION_LINK_DELETE,
    SYSTEM_INTEGRATION_LINK_READ,
)
from fides.common.api.v1.urn_registry import V1_URL_PREFIX
from fides.system_integration_link.models import SystemConnectionConfigLink
from fides.system_integration_link.repository import SystemIntegrationLinkRepository


def _url(connection_key: str) -> str:
    return f"{V1_URL_PREFIX}/connection/{connection_key}/system-links"


@pytest.fixture()
def system(db: Session):
    system = System.create(
        db=db,
        data={
            "fides_key": "route_test_system",
            "name": "Route Test System",
            "organization_fides_key": "test_organization",
            "system_type": "Service",
        },
    )
    yield system
    system.delete(db)


@pytest.fixture()
def system_b(db: Session):
    system = System.create(
        db=db,
        data={
            "fides_key": "route_test_system_b",
            "name": "Route Test System B",
            "organization_fides_key": "test_organization",
            "system_type": "Service",
        },
    )
    yield system
    system.delete(db)


@pytest.fixture()
def connection_config(db: Session):
    config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Route Test Connection",
            "key": "route_test_connection",
            "connection_type": "manual",
            "access": "read",
        },
    )
    yield config
    config.delete(db)


@pytest.fixture(autouse=True)
def cleanup_links(db: Session):
    yield
    db.query(SystemConnectionConfigLink).filter(
        SystemConnectionConfigLink.connection_config_id.in_(
            db.query(ConnectionConfig.id).filter(
                ConnectionConfig.key.like("route_test_%")
            )
        )
    ).delete(synchronize_session=False)
    db.commit()


class TestGetSystemLinks:
    def test_unauthenticated(self, api_client: TestClient, connection_config):
        resp = api_client.get(_url(connection_config.key))
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_returns_empty_list(
        self, api_client: TestClient, generate_auth_header, connection_config
    ):
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_READ])
        resp = api_client.get(_url(connection_config.key), headers=auth_header)
        assert resp.status_code == HTTP_200_OK
        assert resp.json() == []

    def test_returns_links(
        self,
        api_client: TestClient,
        generate_auth_header,
        db: Session,
        connection_config,
        system,
    ):
        repo = SystemIntegrationLinkRepository()
        repo.create_or_update_link(
            system_id=system.id,
            connection_config_id=connection_config.id,
            session=db,
        )
        db.commit()

        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_READ])
        resp = api_client.get(_url(connection_config.key), headers=auth_header)
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["system_fides_key"] == "route_test_system"
        assert data[0]["system_name"] == "Route Test System"

    def test_connection_not_found(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_READ])
        resp = api_client.get(_url("nonexistent_key"), headers=auth_header)
        assert resp.status_code == HTTP_404_NOT_FOUND


class TestSetSystemLinks:
    def test_unauthenticated(self, api_client: TestClient, connection_config):
        resp = api_client.put(
            _url(connection_config.key),
            json={"links": [{"system_fides_key": "whatever"}]},
        )
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_set_single_link(
        self,
        api_client: TestClient,
        generate_auth_header,
        connection_config,
        system,
    ):
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE])
        resp = api_client.put(
            _url(connection_config.key),
            json={"links": [{"system_fides_key": "route_test_system"}]},
            headers=auth_header,
        )
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["system_fides_key"] == "route_test_system"

    def test_set_link_overrides_existing(
        self,
        api_client: TestClient,
        generate_auth_header,
        db: Session,
        connection_config,
        system,
        system_b,
    ):
        """Setting a new system link should replace the existing one."""
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE])

        resp = api_client.put(
            _url(connection_config.key),
            json={"links": [{"system_fides_key": "route_test_system"}]},
            headers=auth_header,
        )
        assert resp.status_code == HTTP_200_OK
        assert resp.json()[0]["system_fides_key"] == "route_test_system"

        resp = api_client.put(
            _url(connection_config.key),
            json={"links": [{"system_fides_key": "route_test_system_b"}]},
            headers=auth_header,
        )
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["system_fides_key"] == "route_test_system_b"

        read_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_READ])
        resp = api_client.get(_url(connection_config.key), headers=read_header)
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["system_fides_key"] == "route_test_system_b"

    def test_clear_links_with_empty_list(
        self,
        api_client: TestClient,
        generate_auth_header,
        db: Session,
        connection_config,
        system,
    ):
        repo = SystemIntegrationLinkRepository()
        repo.create_or_update_link(
            system_id=system.id,
            connection_config_id=connection_config.id,
            session=db,
        )
        db.commit()

        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE])
        resp = api_client.put(
            _url(connection_config.key),
            json={"links": []},
            headers=auth_header,
        )
        assert resp.status_code == HTTP_200_OK
        assert resp.json() == []

    def test_system_not_found(
        self,
        api_client: TestClient,
        generate_auth_header,
        connection_config,
    ):
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE])
        resp = api_client.put(
            _url(connection_config.key),
            json={"links": [{"system_fides_key": "nonexistent_system"}]},
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND

    def test_connection_not_found(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE])
        resp = api_client.put(
            _url("nonexistent_key"),
            json={"links": [{"system_fides_key": "whatever"}]},
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND

    def test_too_many_links(
        self,
        api_client: TestClient,
        generate_auth_header,
        connection_config,
    ):
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE])
        resp = api_client.put(
            _url(connection_config.key),
            json={
                "links": [
                    {"system_fides_key": "sys_a"},
                    {"system_fides_key": "sys_b"},
                ]
            },
            headers=auth_header,
        )
        assert resp.status_code == HTTP_400_BAD_REQUEST


class TestDeleteSystemLink:
    def test_unauthenticated(self, api_client: TestClient, connection_config):
        resp = api_client.delete(
            f"{_url(connection_config.key)}/some_system",
        )
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_delete_existing_link(
        self,
        api_client: TestClient,
        generate_auth_header,
        db: Session,
        connection_config,
        system,
    ):
        repo = SystemIntegrationLinkRepository()
        repo.create_or_update_link(
            system_id=system.id,
            connection_config_id=connection_config.id,
            session=db,
        )
        db.commit()

        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_DELETE])
        resp = api_client.delete(
            f"{_url(connection_config.key)}/route_test_system",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_204_NO_CONTENT

    def test_link_not_found(
        self,
        api_client: TestClient,
        generate_auth_header,
        connection_config,
        system,
    ):
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_DELETE])
        resp = api_client.delete(
            f"{_url(connection_config.key)}/route_test_system",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND

    def test_connection_not_found(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header([SYSTEM_INTEGRATION_LINK_DELETE])
        resp = api_client.delete(
            f"{_url('nonexistent_key')}/some_system",
            headers=auth_header,
        )
        assert resp.status_code == HTTP_404_NOT_FOUND

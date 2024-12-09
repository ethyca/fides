import json
from unittest import mock

import pytest
from fastapi_pagination import Params
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from starlette.testclient import TestClient

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.privacy_request import PrivacyRequestStatus
from fides.api.models.sql_models import Dataset, System
from fides.api.schemas.policy import ActionType
from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_READ,
    SAAS_CONNECTION_INSTANTIATE,
    STORAGE_DELETE,
    SYSTEM_MANAGER_UPDATE,
)
from fides.common.api.v1.urn_registry import V1_URL_PREFIX
from tests.conftest import generate_role_header_for_user
from tests.fixtures.saas.connection_template_fixtures import instantiate_connector

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
        }
    ]


@pytest.fixture(scope="function")
def connections():
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


class TestPatchSystemConnections:
    ## Add this with the other connection config.
    ## But where is it getting the connection config from?
    @pytest.fixture(scope="function")
    def system_linked_with_connection_config(
        self, system: System, oauth2_authorization_code_connection_config, db: Session
    ):
        system.connection_configs = oauth2_authorization_code_connection_config
        db.commit()
        return system

    def test_patch_connections_valid_system(
        self, api_client: TestClient, generate_auth_header, url, payload
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        resp = api_client.patch(url, headers=auth_header, json=payload)

        assert resp.status_code == HTTP_200_OK

    def test_patch_connections_with_invalid_system(
        self, api_client: TestClient, generate_auth_header, url_invalid_system
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        resp = api_client.patch(url_invalid_system, headers=auth_header, json=[])

        assert resp.status_code == HTTP_404_NOT_FOUND
        assert (
            resp.json()["detail"]
            == "The specified system was not found. Please provide a valid system for the requested operation."
        )

    @pytest.mark.parametrize(
        "acting_user_role, expected_status_code",
        [
            ("owner_user", HTTP_200_OK),
            ("contributor_user", HTTP_200_OK),
            ("approver_user", HTTP_403_FORBIDDEN),
        ],
    )
    def test_patch_connections_role_check(
        self,
        api_client: TestClient,
        payload,
        request,
        url,
        acting_user_role: FidesUser,
        expected_status_code,
        system,
        generate_auth_header,
    ):
        acting_user_role = request.getfixturevalue(acting_user_role)
        auth_header = generate_role_header_for_user(
            acting_user_role, roles=acting_user_role.permissions.roles
        )
        resp = api_client.patch(url, headers=auth_header, json=payload)
        assert resp.status_code == expected_status_code

    @pytest.mark.parametrize(
        "acting_user_role, expected_status_code, assign_system",
        [
            ("viewer_user", HTTP_403_FORBIDDEN, False),
            ("viewer_user", HTTP_200_OK, True),
            ("viewer_and_approver_user", HTTP_403_FORBIDDEN, False),
            ("viewer_and_approver_user", HTTP_200_OK, True),
        ],
    )
    def test_patch_connections_role_check_viewer(
        self,
        api_client: TestClient,
        payload,
        request,
        acting_user_role: FidesUser,
        expected_status_code,
        assign_system,
        system,
        generate_auth_header,
        generate_system_manager_header,
    ):
        url = V1_URL_PREFIX + f"/system/{system.fides_key}/connection"
        acting_user_role = request.getfixturevalue(acting_user_role)

        if assign_system:
            assign_url = V1_URL_PREFIX + f"/user/{acting_user_role.id}/system-manager"
            system_manager_auth_header = generate_auth_header(
                scopes=[SYSTEM_MANAGER_UPDATE]
            )
            api_client.put(
                assign_url, headers=system_manager_auth_header, json=[system.fides_key]
            )
            auth_header = generate_system_manager_header([system.id])
        else:
            auth_header = generate_role_header_for_user(
                acting_user_role, roles=acting_user_role.permissions.roles
            )
        resp = api_client.patch(url, headers=auth_header, json=payload)
        assert resp.status_code == expected_status_code

    def test_patch_connection_secrets_removes_access_token(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        system_linked_with_connection_config,
    ):
        auth_header = generate_auth_header(
            scopes=[CONNECTION_READ, CONNECTION_CREATE_OR_UPDATE]
        )

        # verify the connection_config is authorized
        resp = api_client.get(url, headers=auth_header)

        assert resp.status_code == HTTP_200_OK
        assert resp.json()["items"][0]["authorized"] is True

        # patch the connection_config with new secrets (but no access_token)
        resp = api_client.patch(
            f"{url}/secrets?verify=False",
            headers=auth_header,
            json={"domain": "test_domain"},
        )

        # verify the connection_config is no longer authorized
        resp = api_client.get(url, headers=auth_header)

        assert resp.status_code == HTTP_200_OK
        assert resp.json()["items"][0]["authorized"] is False


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
            == "The specified system was not found. Please provide a valid system for the requested operation."
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
        connections,
        db: Session,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        api_client.patch(url, headers=auth_header, json=connections)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK

        response_body = json.loads(resp.text)
        assert len(response_body["items"]) == 3
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
        connection_keys = [connection["key"] for connection in connections]
        assert response_body["items"][0]["key"] in connection_keys
        assert response_body["items"][1]["key"] in connection_keys
        assert response_body["items"][2]["key"] in connection_keys

        assert response_body["total"] == 3
        assert response_body["page"] == 1
        assert response_body["size"] == page_size

    def test_get_connection_configs_masks_secrets(
        self,
        api_client: TestClient,
        generate_auth_header,
        connection_config,
        url,
        connections,
        db: Session,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        api_client.patch(url, headers=auth_header, json=connections)

        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK

        response_body = json.loads(resp.text)
        assert len(response_body["items"]) == 3
        connection_1 = response_body["items"][0]["secrets"]
        connection_2 = response_body["items"][1]["secrets"]
        connection_3 = response_body["items"][2]["secrets"]
        assert connection_1 == {
            "api_key": "**********",
            "domain": "test_mailchimp_domain",
            "username": "test_mailchimp_username",
        }

        assert connection_2 == {
            "db_schema": "test",
            "dbname": "test",
            "host": "http://localhost",
            "password": "**********",
            "port": 5432,
            "username": "test",
        }

        assert connection_3 == None

    @pytest.mark.parametrize(
        "acting_user_role, expected_status_code, assign_system",
        [
            ("viewer_user", HTTP_200_OK, False),
            ("viewer_user", HTTP_200_OK, True),
            ("viewer_and_approver_user", HTTP_200_OK, False),
            ("viewer_and_approver_user", HTTP_200_OK, True),
        ],
    )
    def test_get_connection_configs_role_viewer(
        self,
        api_client: TestClient,
        generate_auth_header,
        generate_system_manager_header,
        connection_config,
        connections,
        acting_user_role,
        expected_status_code,
        assign_system,
        system,
        request,
        db: Session,
    ) -> None:
        url = V1_URL_PREFIX + f"/system/{system.fides_key}/connection"
        patch_auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        api_client.patch(url, headers=patch_auth_header, json=connections)

        acting_user_role = request.getfixturevalue(acting_user_role)

        if assign_system:
            assign_url = V1_URL_PREFIX + f"/user/{acting_user_role.id}/system-manager"
            system_manager_auth_header = generate_auth_header(
                scopes=[SYSTEM_MANAGER_UPDATE]
            )
            api_client.put(
                assign_url, headers=system_manager_auth_header, json=[system.fides_key]
            )
            auth_header = generate_system_manager_header([system.id])
        else:
            auth_header = generate_role_header_for_user(
                acting_user_role, roles=acting_user_role.permissions.roles
            )

        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == expected_status_code

    @pytest.mark.parametrize(
        "acting_user_role, expected_status_code",
        [
            ("owner_user", HTTP_200_OK),
            ("contributor_user", HTTP_200_OK),
            ("approver_user", HTTP_403_FORBIDDEN),
        ],
    )
    def test_get_connection_configs_role(
        self,
        api_client: TestClient,
        generate_auth_header,
        connection_config,
        connections,
        acting_user_role,
        expected_status_code,
        system,
        request,
        db: Session,
    ) -> None:
        url = V1_URL_PREFIX + f"/system/{system.fides_key}/connection"
        patch_auth_header = generate_auth_header(scopes=[CONNECTION_CREATE_OR_UPDATE])
        api_client.patch(url, headers=patch_auth_header, json=connections)

        acting_user_role = request.getfixturevalue(acting_user_role)
        auth_header = generate_role_header_for_user(
            acting_user_role, roles=acting_user_role.permissions.roles
        )

        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == expected_status_code


class TestDeleteSystemConnectionConfig:
    @pytest.fixture(scope="function")
    def url(self, system) -> str:
        return V1_URL_PREFIX + f"/system/{system.fides_key}/connection"

    @pytest.fixture(scope="function")
    def system_linked_with_connection_config(
        self, system: System, connection_config, db: Session
    ):
        system.connection_configs = connection_config
        db.commit()
        return system

    def test_delete_connection_config_not_authenticated(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        # Test not authenticated

        resp = api_client.delete(url, headers={})
        assert resp.status_code == HTTP_401_UNAUTHORIZED

    def test_delete_connection_config_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header, connection_config
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_403_FORBIDDEN

    def test_delete_connection_config_does_not_exist(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_DELETE])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_404_NOT_FOUND
        assert resp.json()["detail"] == "No integration found linked to this system"

    def test_delete_connection_config(
        self,
        url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        system_linked_with_connection_config,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_DELETE])
        # the key needs to be cached before the delete
        key = system_linked_with_connection_config.connection_configs.key
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_204_NO_CONTENT
        assert db.query(ConnectionConfig).filter_by(key=key).first() is None

    @mock.patch("fides.api.util.connection_util.queue_privacy_request")
    def test_delete_manual_webhook_connection_config(
        self,
        mock_queue,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        integration_manual_webhook_config,
        access_manual_webhook,
        privacy_request_requires_input,
        system,
    ) -> None:
        """Assert both the connection config and its webhook are deleted"""
        access_manual_webhook_id = access_manual_webhook.id
        integration_manual_webhook_config_id = integration_manual_webhook_config.id
        system.connection_configs = integration_manual_webhook_config
        db.commit()
        assert (
            db.query(AccessManualWebhook).filter_by(id=access_manual_webhook_id).first()
            is not None
        )

        assert (
            db.query(ConnectionConfig)
            .filter_by(key=integration_manual_webhook_config.key)
            .first()
            is not None
        )
        url = V1_URL_PREFIX + f"/system/{system.fides_key}/connection"
        auth_header = generate_auth_header(scopes=[CONNECTION_DELETE])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_204_NO_CONTENT

        assert (
            db.query(AccessManualWebhook).filter_by(id=access_manual_webhook_id).first()
            is None
        )

        assert (
            db.query(ConnectionConfig)
            .filter_by(key=integration_manual_webhook_config_id)
            .first()
            is None
        )
        assert (
            mock_queue.called == True
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
        self, api_client: TestClient, db: Session, generate_auth_header, system
    ) -> None:
        secrets = {
            "domain": "test_hubspot_domain",
            "private_app_token": "test_hubspot_api_key",
        }
        connection_config, dataset_config = instantiate_connector(
            db,
            "hubspot",
            "secondary_hubspot_instance",
            "Hubspot ConnectionConfig description",
            secrets,
            system,
        )
        dataset = dataset_config.ctl_dataset

        auth_header = generate_auth_header(scopes=[CONNECTION_DELETE])

        url = V1_URL_PREFIX + f"/system/{connection_config.system.fides_key}/connection"
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == HTTP_204_NO_CONTENT
        assert (
            db.query(ConnectionConfig).filter_by(key=connection_config.key).first()
            is None
        )
        assert db.query(DatasetConfig).filter_by(id=dataset_config.id).first() is None
        assert db.query(Dataset).filter_by(id=dataset.id).first() is None

    @pytest.mark.parametrize(
        "acting_user_role, expected_status_code, assign_system",
        [
            ("viewer_user", HTTP_403_FORBIDDEN, False),
            ("viewer_user", HTTP_204_NO_CONTENT, True),
            ("viewer_and_approver_user", HTTP_403_FORBIDDEN, False),
            ("viewer_and_approver_user", HTTP_204_NO_CONTENT, True),
        ],
    )
    def test_delete_connection_configs_role_viewer(
        self,
        api_client: TestClient,
        generate_auth_header,
        generate_system_manager_header,
        acting_user_role,
        expected_status_code,
        assign_system,
        system_linked_with_connection_config,
        request,
        db: Session,
    ) -> None:
        url = (
            V1_URL_PREFIX
            + f"/system/{system_linked_with_connection_config.fides_key}/connection"
        )

        acting_user_role = request.getfixturevalue(acting_user_role)

        if assign_system:
            assign_url = V1_URL_PREFIX + f"/user/{acting_user_role.id}/system-manager"
            system_manager_auth_header = generate_auth_header(
                scopes=[SYSTEM_MANAGER_UPDATE]
            )
            api_client.put(
                assign_url,
                headers=system_manager_auth_header,
                json=[system_linked_with_connection_config.fides_key],
            )
            auth_header = generate_system_manager_header(
                [system_linked_with_connection_config.id]
            )
        else:
            auth_header = generate_role_header_for_user(
                acting_user_role, roles=acting_user_role.permissions.roles
            )

        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == expected_status_code

    @pytest.mark.parametrize(
        "acting_user_role, expected_status_code",
        [
            ("owner_user", HTTP_204_NO_CONTENT),
            ("contributor_user", HTTP_204_NO_CONTENT),
            ("approver_user", HTTP_403_FORBIDDEN),
        ],
    )
    def test_delete_connection_configs_role_check(
        self,
        api_client: TestClient,
        generate_auth_header,
        acting_user_role,
        expected_status_code,
        system_linked_with_connection_config,
        request,
        db: Session,
    ) -> None:
        url = (
            V1_URL_PREFIX
            + f"/system/{system_linked_with_connection_config.fides_key}/connection"
        )

        acting_user_role = request.getfixturevalue(acting_user_role)
        auth_header = generate_role_header_for_user(
            acting_user_role, roles=acting_user_role.permissions.roles
        )

        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == expected_status_code


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
        assert (
            resp.json()["detail"][0]["msg"]
            == "Value error, mailchimp_schema must be supplied all of: [domain, username, api_key]."
        )
        # extra values should be permitted, but the system should return an error if there are missing fields.

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        assert connection_config is None, "ConnectionConfig not persisted"

    def test_connection_config_key_already_exists(
        self, db, generate_auth_header, api_client, base_url, connection_config
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": connection_config.key,
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "description": "Mailchimp ConnectionConfig description",
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
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        # names don't have to be unique
        assert resp.status_code == 200

    def test_create_connection_from_template_without_supplying_connection_key(
        self, db, generate_auth_header, api_client, base_url
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        instance_key = "secondary_mailchimp_instance"
        request_body = {
            "instance_key": instance_key,
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

        assert connection_config.key == instance_key
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
            "msg": "Value error, FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: < this is an invalid key! >",
            "type": "value_error",
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
        assert connection_data["secrets"]["api_key"] == "**********"

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
        assert connection_config.system_id is not None

        assert dataset_config.connection_config_id == connection_config.id
        assert dataset_config.ctl_dataset_id is not None

        dataset_config.delete(db)
        connection_config.delete(db)
        dataset_config.ctl_dataset.delete(db=db)

    def test_instantiate_connection_from_template_ignore_enabled_actions(
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
            "enabled_actions": [ActionType.access.value],
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
        assert connection_data["secrets"]["api_key"] == "**********"
        assert connection_data["enabled_actions"] is None

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
        assert connection_config.system_id is not None
        assert connection_config.enabled_actions is None

        assert dataset_config.connection_config_id == connection_config.id
        assert dataset_config.ctl_dataset_id is not None

        dataset_config.delete(db)
        connection_config.delete(db)
        dataset_config.ctl_dataset.delete(db=db)

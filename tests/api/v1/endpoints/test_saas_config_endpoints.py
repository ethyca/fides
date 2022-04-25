import json
import pytest
from typing import Optional
from fidesops.api.v1.scope_registry import (
    SAAS_CONFIG_CREATE_OR_UPDATE,
    SAAS_CONFIG_DELETE,
    SAAS_CONFIG_READ,
)
from fidesops.api.v1.urn_registry import (
    SAAS_CONFIG,
    SAAS_CONFIG_VALIDATE,
    V1_URL_PREFIX,
)
from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from tests.api.v1.endpoints.test_dataset_endpoints import _reject_key


@pytest.mark.unit_saas
class TestValidateSaaSConfig:
    @pytest.fixture
    def validate_saas_config_url(self, saas_example_connection_config) -> str:
        path = V1_URL_PREFIX + SAAS_CONFIG_VALIDATE
        path_params = {"connection_key": saas_example_connection_config.key}
        return path.format(**path_params)

    def test_put_validate_saas_config_not_authenticated(
        self, saas_example_config, validate_saas_config_url: str, api_client
    ) -> None:
        response = api_client.put(
            validate_saas_config_url, headers={}, json=saas_example_config
        )
        assert response.status_code == 401

    def test_put_validate_dataset_wrong_scope(
        self,
        saas_example_config,
        validate_saas_config_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_CREATE_OR_UPDATE])
        response = api_client.put(
            validate_saas_config_url,
            headers=auth_header,
            json=saas_example_config,
        )
        assert response.status_code == 403

    def test_put_validate_saas_config_missing_key(
        self,
        saas_example_config,
        validate_saas_config_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        invalid_config = _reject_key(saas_example_config, "fides_key")
        response = api_client.put(
            validate_saas_config_url, headers=auth_header, json=invalid_config
        )
        assert response.status_code == 422

        details = json.loads(response.text)["detail"]
        assert ["body", "fides_key"] in [e["loc"] for e in details]

    def test_put_validate_saas_config_missing_endpoints(
        self,
        saas_example_config,
        validate_saas_config_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        invalid_config = _reject_key(saas_example_config, "endpoints")
        response = api_client.put(
            validate_saas_config_url, headers=auth_header, json=invalid_config
        )
        assert response.status_code == 422

        details = json.loads(response.text)["detail"]
        assert ["body", "endpoints"] in [e["loc"] for e in details]

    def test_put_validate_saas_config_reference_and_identity(
        self,
        saas_example_config,
        validate_saas_config_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        saas_config = saas_example_config
        param_values = saas_config["endpoints"][0]["requests"]["read"][
            "param_values"
        ][0]
        param_values["identity"] = "email"
        param_values["references"] = [
            {
                "dataset": "postgres_example_test_dataset",
                "field": "another.field",
                "direction": "from",
            }
        ]
        response = api_client.put(
            validate_saas_config_url, headers=auth_header, json=saas_config
        )
        assert response.status_code == 422
        details = json.loads(response.text)["detail"]
        assert details[0]["msg"] == "Must have exactly one of 'identity', 'references', or 'connector_param'"

    def test_put_validate_saas_config_wrong_reference_direction(
        self,
        saas_example_config,
        validate_saas_config_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        saas_config = saas_example_config
        param_values = saas_config["endpoints"][0]["requests"]["read"][
            "param_values"
        ][0]
        param_values["references"] = [
            {
                "dataset": "postgres_example_test_dataset",
                "field": "another.field",
                "direction": "to",
            }
        ]
        response = api_client.put(
            validate_saas_config_url, headers=auth_header, json=saas_config
        )
        assert response.status_code == 422
        details = json.loads(response.text)["detail"]
        assert details[0]["msg"] == "References can only have a direction of 'from', found 'to'"

@pytest.mark.unit_saas
class TestPutSaaSConfig:
    @pytest.fixture
    def saas_config_url(self, saas_example_connection_config) -> str:
        path = V1_URL_PREFIX + SAAS_CONFIG
        path_params = {"connection_key": saas_example_connection_config.key}
        return path.format(**path_params)

    def test_patch_saas_config_not_authenticated(
        self, saas_example_config, saas_config_url, api_client
    ) -> None:
        response = api_client.patch(
            saas_config_url, headers={}, json=saas_example_config
        )
        assert response.status_code == 401

    def test_patch_saas_config_wrong_scope(
        self,
        saas_example_config,
        saas_config_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        response = api_client.patch(
            saas_config_url, headers=auth_header, json=saas_example_config
        )
        assert response.status_code == 403

    def test_patch_saas_config_invalid_connection_key(
        self, saas_example_config, api_client: TestClient, generate_auth_header
    ) -> None:
        path = V1_URL_PREFIX + SAAS_CONFIG
        path_params = {"connection_key": "nonexistent_key"}
        saas_config_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_CREATE_OR_UPDATE])
        response = api_client.patch(
            saas_config_url, headers=auth_header, json=saas_example_config
        )
        assert response.status_code == 404

    def test_patch_saas_config_create(
        self,
        saas_example_connection_config_without_saas_config,
        saas_example_config,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ) -> None:
        path = V1_URL_PREFIX + SAAS_CONFIG
        path_params = {"connection_key": saas_example_connection_config_without_saas_config.key}
        saas_config_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_CREATE_OR_UPDATE])
        response = api_client.patch(
            saas_config_url, headers=auth_header, json=saas_example_config
        )
        assert response.status_code == 200

        updated_config = ConnectionConfig.get_by(
            db=db, field="key", value=saas_example_connection_config_without_saas_config.key
        )
        db.expire(updated_config)
        saas_config = updated_config.saas_config
        assert saas_config is not None

    def test_patch_saas_config_update(
        self,
        saas_example_config,
        saas_config_url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_CREATE_OR_UPDATE])
        saas_example_config["endpoints"].pop()
        response = api_client.patch(
            saas_config_url, headers=auth_header, json=saas_example_config
        )
        assert response.status_code == 200

        connection_config = ConnectionConfig.get_by(
            db=db, field="key", value=saas_example_config["fides_key"]
        )
        saas_config = connection_config.saas_config
        assert saas_config is not None
        assert len(saas_config["endpoints"]) == 6


def get_saas_config_url(connection_config: Optional[ConnectionConfig] = None) -> str:
    """Helper to construct the SAAS_CONFIG URL, substituting valid/invalid keys in the path"""
    path = V1_URL_PREFIX + SAAS_CONFIG
    connection_key = "nonexistent_key"
    if connection_config:
        connection_key = connection_config.key
    path_params = {"connection_key": connection_key}
    return path.format(**path_params)


@pytest.mark.unit_saas
class TestGetSaaSConfig:
    def test_get_saas_config_not_authenticated(
        self,
        saas_example_connection_config,
        api_client: TestClient,
    ) -> None:
        saas_config_url = get_saas_config_url(saas_example_connection_config)
        response = api_client.get(saas_config_url, headers={})
        assert response.status_code == 401

    def test_get_saas_config_wrong_scope(
        self,
        saas_example_connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        saas_config_url = get_saas_config_url(saas_example_connection_config)
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_CREATE_OR_UPDATE])
        response = api_client.get(saas_config_url, headers=auth_header)
        assert response.status_code == 403

    def test_get_saas_config_does_not_exist(
        self,
        saas_example_connection_config_without_saas_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        saas_config_url = get_saas_config_url(
            saas_example_connection_config_without_saas_config
        )
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        response = api_client.get(saas_config_url, headers=auth_header)
        assert response.status_code == 404

    def test_get_saas_config_invalid_connection_key(
        self,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        saas_config_url = get_saas_config_url(None)
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        response = api_client.get(saas_config_url, headers=auth_header)
        assert response.status_code == 404

    def test_get_saas_config(
        self,
        saas_example_connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        saas_config_url = get_saas_config_url(saas_example_connection_config)
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        response = api_client.get(saas_config_url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert (
            response_body["fides_key"]
            == saas_example_connection_config.get_saas_config().fides_key
        )
        assert len(response_body["endpoints"]) == 7


@pytest.mark.unit_saas
class TestDeleteSaaSConfig:
    def test_delete_saas_config_not_authenticated(
        self, saas_example_connection_config, api_client
    ) -> None:
        saas_config_url = get_saas_config_url(saas_example_connection_config)
        response = api_client.delete(saas_config_url, headers={})
        assert response.status_code == 401

    def test_delete_saas_config_wrong_scope(
        self,
        saas_example_connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        saas_config_url = get_saas_config_url(saas_example_connection_config)
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        response = api_client.delete(saas_config_url, headers=auth_header)
        assert response.status_code == 403

    def test_delete_saas_config_does_not_exist(
        self,
        saas_example_connection_config_without_saas_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        saas_config_url = get_saas_config_url(
            saas_example_connection_config_without_saas_config
        )
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_DELETE])
        response = api_client.delete(saas_config_url, headers=auth_header)
        assert response.status_code == 404

    def test_delete_saas_config_invalid_connection_key(
        self,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        saas_config_url = get_saas_config_url(None)
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_DELETE])
        response = api_client.delete(saas_config_url, headers=auth_header)
        assert response.status_code == 404

    def test_delete_saas_config(
        self,
        db: Session,
        saas_example_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        # Create a new connection config so we don't run into issues trying to clean up an
        # already deleted fixture
        fides_key = "saas_config_for_deletion_test"
        saas_example_config["fides_key"] = fides_key
        config_to_delete = ConnectionConfig.create(
            db=db,
            data={
                "key": fides_key,
                "name": fides_key,
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.read,
                "saas_config": saas_example_config,
            },
        )
        saas_config_url = get_saas_config_url(config_to_delete)
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_DELETE])
        response = api_client.delete(saas_config_url, headers=auth_header)
        assert response.status_code == 204

        updated_config = ConnectionConfig.get_by(db=db, field="key", value=fides_key)
        db.expire(updated_config)
        assert updated_config.saas_config is None

    def test_delete_saas_config_with_dataset_and_secrets(
        self,
        saas_example_connection_config,
        saas_example_dataset_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        saas_config_url = get_saas_config_url(saas_example_connection_config)
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_DELETE])
        response = api_client.delete(saas_config_url, headers=auth_header)
        assert response.status_code == 400

        response_body = json.loads(response.text)
        assert (
            response_body["detail"]
            == f"Must delete the dataset with fides_key '{saas_example_dataset_config.fides_key}' "
            "before deleting this SaaS config. Must clear the secrets from this connection "
            "config before deleting the SaaS config."
        )

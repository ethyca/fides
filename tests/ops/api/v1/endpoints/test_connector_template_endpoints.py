from unittest import mock
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.custom_connector_template import CustomConnectorTemplate
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    CustomConnectorTemplateLoader,
    FileConnectorTemplateLoader,
)
from fides.common.api.scope_registry import (
    CLIENT_READ,
    CONNECTOR_TEMPLATE_READ,
    CONNECTOR_TEMPLATE_REGISTER,
    SAAS_CONNECTION_INSTANTIATE,
)
from fides.common.api.v1.urn_registry import (
    CONNECTOR_TEMPLATES_CONFIG,
    CONNECTOR_TEMPLATES_DATASET,
    CONNECTOR_TEMPLATES_REGISTER,
    DELETE_CUSTOM_TEMPLATE,
    SAAS_CONNECTOR_FROM_TEMPLATE,
    V1_URL_PREFIX,
)
from tests.ops.test_helpers.saas_test_utils import create_zip_file


class TestRegisterConnectorTemplate:
    @pytest.fixture
    def register_connector_template_url(self) -> str:
        return V1_URL_PREFIX + CONNECTOR_TEMPLATES_REGISTER

    @pytest.fixture
    def complete_connector_template(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_missing_config(
        self,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_wrong_contents_config(
        self,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": "planet_express_config",
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_invalid_config(
        self,
        planet_express_invalid_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_invalid_config,
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_missing_dataset(
        self,
        planet_express_config,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_wrong_contents_dataset(
        self,
        planet_express_config,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": "planet_express_dataset",
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_invalid_dataset(
        self,
        planet_express_config,
        planet_express_invalid_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_invalid_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_no_icon(
        self,
        planet_express_config,
        planet_express_dataset,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
            }
        )

    @pytest.fixture
    def connector_template_duplicate_configs(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "1_config.yml": planet_express_config,
                "2_config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_duplicate_datasets(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "1_dataset.yml": planet_express_dataset,
                "2_dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_duplicate_icons(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "1_icon.svg": planet_express_icon,
                "2_icon.svg": planet_express_icon,
            }
        )

    def test_register_connector_template_wrong_scope(
        self,
        api_client: TestClient,
        register_connector_template_url,
        generate_auth_header,
        complete_connector_template,
    ):
        auth_header = generate_auth_header(scopes=[CLIENT_READ])
        response = api_client.post(
            register_connector_template_url,
            headers=auth_header,
            files={
                "file": (
                    "template.zip",
                    complete_connector_template,
                    "application/zip",
                )
            },
        )
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "zip_file, status_code, details",
        [
            (
                "complete_connector_template",
                200,
                {"message": "Connector template successfully registered."},
            ),
            (
                "connector_template_missing_config",
                400,
                {"detail": "Zip file does not contain a config.yml file."},
            ),
            (
                "connector_template_wrong_contents_config",
                400,
                {
                    "detail": "Config contents do not contain a 'saas_config' key at the root level. For example, check formatting, specifically indentation."
                },
            ),
            (
                "connector_template_invalid_config",
                400,
                {
                    "detail": "1 validation error for SaaSConfig\ntest_request\n  Field required [type=missing, input_value={'fides_key': '<instance_...dentity': 'email'}]}}}]}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.12/v/missing"
                },
            ),
            (
                "connector_template_missing_dataset",
                400,
                {"detail": "Zip file does not contain a dataset.yml file."},
            ),
            (
                "connector_template_wrong_contents_dataset",
                400,
                {
                    "detail": "Dataset contents do not contain a 'dataset' key at the root level. For example, check formatting, specifically indentation."
                },
            ),
            (
                "connector_template_invalid_dataset",
                400,
                {
                    "detail": "1 validation error for Dataset\ncollections.0.name\n  Field required [type=missing, input_value={'fides_meta': None, 'nam...': ['user.unique_id']}]}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.12/v/missing"
                },
            ),
            (
                "connector_template_no_icon",
                200,
                {"message": "Connector template successfully registered."},
            ),
            (
                "connector_template_duplicate_configs",
                400,
                {
                    "detail": "Multiple files ending with config.yml found, only one is allowed."
                },
            ),
            (
                "connector_template_duplicate_datasets",
                400,
                {
                    "detail": "Multiple files ending with dataset.yml found, only one is allowed."
                },
            ),
            (
                "connector_template_duplicate_icons",
                400,
                {"detail": "Multiple svg files found, only one is allowed."},
            ),
        ],
    )
    def test_register_connector_template(
        self,
        api_client: TestClient,
        register_connector_template_url,
        generate_auth_header,
        zip_file,
        status_code,
        details,
        request,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.post(
            register_connector_template_url,
            headers=auth_header,
            files={
                "file": (
                    "template.zip",
                    request.getfixturevalue(zip_file).read(),
                    "application/zip",
                )
            },
        )
        assert response.status_code == status_code
        assert response.json() == details


class TestGetConnectorTemplateConfig:
    @pytest.fixture
    def get_connector_template_config_url(self) -> str:
        return V1_URL_PREFIX + CONNECTOR_TEMPLATES_CONFIG

    @pytest.fixture
    def complete_connector_template(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    def test_get_connector_template_config_not_authenticated(
        self, get_connector_template_config_url: str, api_client
    ) -> None:
        response = api_client.get(
            get_connector_template_config_url.format(connector_template_type="stripe"),
            headers={},
        )
        assert response.status_code == 401

    def test_get_connector_template_config_wrong_scope(
        self,
        get_connector_template_config_url: str,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CLIENT_READ])
        response = api_client.get(
            get_connector_template_config_url.format(connector_template_type="stripe"),
            headers=auth_header,
        )
        assert response.status_code == 403

    def test_get_connector_template_config_not_found(
        self,
        get_connector_template_config_url: str,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_READ])
        response = api_client.get(
            get_connector_template_config_url.format(
                connector_template_type="nonexistent_connector"
            ),
            headers=auth_header,
        )
        assert response.status_code == 404
        assert (
            "No connector template found with type 'nonexistent_connector'"
            in response.json()["detail"]
        )

    def test_get_connector_template_config_file_based_success(
        self,
        get_connector_template_config_url: str,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_READ])
        response = api_client.get(
            get_connector_template_config_url.format(connector_template_type="stripe"),
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/yaml; charset=utf-8"

        # Verify the YAML content contains expected fields
        yaml_content = response.text
        assert "saas_config:" in yaml_content
        assert "type: stripe" in yaml_content
        assert "name: Stripe" in yaml_content

    def test_get_connector_template_config_custom_template_success(
        self,
        db: Session,
        get_connector_template_config_url: str,
        api_client: TestClient,
        generate_auth_header,
        complete_connector_template,
    ) -> None:
        # First register a custom connector template
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        register_url = V1_URL_PREFIX + CONNECTOR_TEMPLATES_REGISTER
        api_client.post(
            register_url,
            files={
                "file": (
                    "connector_template.zip",
                    complete_connector_template,
                    "application/zip",
                )
            },
            headers=auth_header,
        )

        # Now retrieve the config
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_READ])
        response = api_client.get(
            get_connector_template_config_url.format(
                connector_template_type="planet_express"
            ),
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/yaml; charset=utf-8"

        # Verify the YAML content contains expected fields
        yaml_content = response.text
        assert "saas_config:" in yaml_content
        assert "type: planet_express" in yaml_content
        assert "name: Planet Express" in yaml_content


class TestGetConnectorTemplateDataset:
    @pytest.fixture
    def get_connector_template_dataset_url(self) -> str:
        return V1_URL_PREFIX + CONNECTOR_TEMPLATES_DATASET

    @pytest.fixture
    def complete_connector_template(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        return create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    def test_get_connector_template_dataset_not_authenticated(
        self, get_connector_template_dataset_url: str, api_client
    ) -> None:
        response = api_client.get(
            get_connector_template_dataset_url.format(connector_template_type="stripe"),
            headers={},
        )
        assert response.status_code == 401

    def test_get_connector_template_dataset_wrong_scope(
        self,
        get_connector_template_dataset_url: str,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CLIENT_READ])
        response = api_client.get(
            get_connector_template_dataset_url.format(connector_template_type="stripe"),
            headers=auth_header,
        )
        assert response.status_code == 403

    def test_get_connector_template_dataset_not_found(
        self,
        get_connector_template_dataset_url: str,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_READ])
        response = api_client.get(
            get_connector_template_dataset_url.format(
                connector_template_type="nonexistent_connector"
            ),
            headers=auth_header,
        )
        assert response.status_code == 404
        assert (
            "No connector template found with type 'nonexistent_connector'"
            in response.json()["detail"]
        )

    def test_get_connector_template_dataset_file_based_success(
        self,
        get_connector_template_dataset_url: str,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_READ])
        response = api_client.get(
            get_connector_template_dataset_url.format(connector_template_type="stripe"),
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/yaml; charset=utf-8"

        # Verify the YAML content contains expected fields
        yaml_content = response.text
        assert "dataset:" in yaml_content
        assert "fides_key: <instance_fides_key>" in yaml_content
        assert "name: Stripe Dataset" in yaml_content

    def test_get_connector_template_dataset_custom_template_success(
        self,
        db: Session,
        get_connector_template_dataset_url: str,
        api_client: TestClient,
        generate_auth_header,
        complete_connector_template,
    ) -> None:
        # First register a custom connector template
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        register_url = V1_URL_PREFIX + CONNECTOR_TEMPLATES_REGISTER
        api_client.post(
            register_url,
            files={
                "file": (
                    "connector_template.zip",
                    complete_connector_template,
                    "application/zip",
                )
            },
            headers=auth_header,
        )

        # Now retrieve the dataset
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_READ])
        response = api_client.get(
            get_connector_template_dataset_url.format(
                connector_template_type="planet_express"
            ),
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/yaml; charset=utf-8"

        # Verify the YAML content contains expected fields
        yaml_content = response.text
        assert "dataset:" in yaml_content
        assert "fides_key: <instance_fides_key>" in yaml_content
        assert "name: Planet Express Dataset" in yaml_content


@pytest.mark.unit_saas
class TestDeleteCustomConnectorTemplate:
    @pytest.fixture(scope="function", autouse=True)
    def reset_connector_template_loaders(self):
        """
        Resets the loader singleton instances before each test
        """
        FileConnectorTemplateLoader._instance = None
        CustomConnectorTemplateLoader._instance = None

    @pytest.fixture
    def complete_connector_template(
        self,
        hubspot_yaml_config,
        hubspot_yaml_dataset,
        hubspot_yaml_icon,
    ):
        return create_zip_file(
            {
                "config.yml": hubspot_yaml_config,
                "dataset.yml": hubspot_yaml_dataset,
                "icon.svg": hubspot_yaml_icon,
            }
        )

    @pytest.fixture
    def delete_custom_connector_url(self) -> str:
        return V1_URL_PREFIX + DELETE_CUSTOM_TEMPLATE

    @pytest.fixture
    def register_connector_template_url(self) -> str:
        return V1_URL_PREFIX + CONNECTOR_TEMPLATES_REGISTER

    def test_delete_custom_connector_not_authenticated(
        self, api_client: TestClient, delete_custom_connector_url
    ) -> None:
        """Test that unauthenticated requests are rejected."""
        response = api_client.delete(
            delete_custom_connector_url.format(saas_connector_type="test_connector")
        )
        assert response.status_code == 401

    def test_delete_custom_connector_wrong_scope(
        self,
        api_client: TestClient,
        delete_custom_connector_url,
        generate_auth_header,
    ) -> None:
        """Test that requests with wrong scope are rejected."""
        auth_header = generate_auth_header(scopes=[CLIENT_READ])
        response = api_client.delete(
            delete_custom_connector_url.format(saas_connector_type="test_connector"),
            headers=auth_header,
        )
        assert response.status_code == 403

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_delete_custom_connector_not_found(
        self,
        mock_all: MagicMock,
        api_client: TestClient,
        delete_custom_connector_url,
        generate_auth_header,
    ) -> None:
        """Test that non-existent connector types return 404."""
        # Mock no custom templates exist
        mock_all.return_value = []

        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.delete(
            delete_custom_connector_url.format(
                saas_connector_type="nonexistent_connector"
            ),
            headers=auth_header,
        )
        assert response.status_code == 404
        assert "not yet available in Fides" in response.json()["detail"]

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_delete_custom_connector_not_custom_template(
        self,
        mock_all: MagicMock,
        api_client: TestClient,
        delete_custom_connector_url,
        generate_auth_header,
    ) -> None:
        """Test that non-custom templates return 400."""
        # Mock no custom templates exist (so it will use file template)
        mock_all.return_value = []

        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.delete(
            delete_custom_connector_url.format(saas_connector_type="hubspot"),
            headers=auth_header,
        )
        assert response.status_code == 400
        assert "is not a custom template" in response.json()["detail"]

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_delete_custom_connector_no_default_connector_available(
        self,
        mock_all: MagicMock,
        api_client: TestClient,
        delete_custom_connector_url,
        generate_auth_header,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ) -> None:
        """Test that custom templates without file connector fallback return 400."""
        # Mock a custom template that doesn't have a file connector fallback

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="custom_only_connector",
                name="Custom Only Connector",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
            )
        ]

        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.delete(
            delete_custom_connector_url.format(
                saas_connector_type="custom_only_connector"
            ),
            headers=auth_header,
        )
        assert response.status_code == 400
        assert (
            "does not have a Fides-provided template to fall back to"
            in response.json()["detail"]
        )

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_delete_custom_connector_file_template_not_found_after_deletion(
        self,
        mock_all: MagicMock,
        api_client: TestClient,
        delete_custom_connector_url,
        generate_auth_header,
        hubspot_yaml_config,
        hubspot_yaml_dataset,
    ) -> None:
        """Test that 404 is returned if file template is not found after delete_custom_template is called"""
        FileConnectorTemplateLoader.get_connector_templates().pop("hubspot", None)

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="hubspot",
                name="HubSpot",
                config=hubspot_yaml_config,
                dataset=hubspot_yaml_dataset,
            )
        ]
        # Mock the file connector template to be available in the custom template
        ConnectorRegistry.get_connector_template(
            "hubspot"
        ).default_connector_available = True

        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.delete(
            delete_custom_connector_url.format(saas_connector_type="hubspot"),
            headers=auth_header,
        )
        assert response.status_code == 404
        assert (
            "Fides-provided template with type 'hubspot' not found"
            in response.json()["detail"]
        )

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    @mock.patch(
        "fides.service.connection.connection_service.ConnectionService.update_existing_connection_configs_for_connector_type"
    )
    def test_delete_custom_connector_update_connection_configs_failure(
        self,
        mock_update_existing_connection_configs: MagicMock,
        mock_all: MagicMock,
        api_client: TestClient,
        delete_custom_connector_url,
        generate_auth_header,
        hubspot_yaml_config,
        hubspot_yaml_dataset,
    ) -> None:
        """Test that 500 is returned if updating connection configs fails."""
        # Mock a custom template for hubspot

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="hubspot",
                name="HubSpot",
                config=hubspot_yaml_config,
                dataset=hubspot_yaml_dataset,
            )
        ]

        mock_update_existing_connection_configs.side_effect = Exception(
            "Error updating connection configs for connector type 'hubspot'."
        )

        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.delete(
            delete_custom_connector_url.format(saas_connector_type="hubspot"),
            headers=auth_header,
        )

        assert response.status_code == 500
        assert (
            "Error updating connection configs for connector type 'hubspot'"
            in response.json()["detail"]
        )

    def test_delete_custom_connector_invalid_connector_type(
        self,
        api_client: TestClient,
        delete_custom_connector_url,
        generate_auth_header,
    ) -> None:
        """Test that invalid connector type characters are handled properly."""
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        # Use a valid connector type that doesn't exist
        encoded_connector_type = "invalid_connector_type"
        response = api_client.delete(
            delete_custom_connector_url.format(
                saas_connector_type=encoded_connector_type
            ),
            headers=auth_header,
        )
        # Should return 404 since the connector type doesn't exist
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_custom_connector_to_file_template_integration(
        self,
        api_client: TestClient,
        generate_auth_header,
        register_connector_template_url,
        delete_custom_connector_url,
        complete_connector_template,
        db,
    ):
        """
        Integration test:
        1. Register a custom connector template.
        2. Verify the custom template is active.
        3. Instantiate a connection using the custom template.
        4. Call the delete endpoint.
        5. Verify the file template is now active.
        6. Verify the connection was updated to use the file template.
        """
        connector_type = "hubspot"

        # 1. Register the custom template
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.post(
            register_connector_template_url,
            headers=auth_header,
            files={
                "file": (
                    "template.zip",
                    complete_connector_template.read(),
                    "application/zip",
                )
            },
        )
        assert response.status_code == 200
        assert (
            response.json()["message"] == "Connector template successfully registered."
        )

        # 2. Verify the custom template is active
        template = ConnectorRegistry.get_connector_template(connector_type)
        assert template is not None
        assert template.is_custom is True
        assert template.default_connector_available is True

        # 3. Instantiate a connection using the custom template
        instance_key = "test_hubspot_instance"
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": instance_key,
            "secrets": {
                "domain": "test_hubspot_domain",
                "private_app_token": "test_hubspot_token",
            },
            "name": "Test HubSpot Connector",
            "description": "Test HubSpot ConnectionConfig description",
            "key": "test_hubspot_connection_config",
        }

        # Get the base URL for instantiation
        base_url = V1_URL_PREFIX + SAAS_CONNECTOR_FROM_TEMPLATE
        resp = api_client.post(
            base_url.format(connector_template_type=connector_type),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 200

        # Verify the connection was created with the custom template
        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "test_hubspot_connection_config")
        ).first()
        assert connection_config is not None

        # Store the original SaaS config to compare later
        original_saas_config = connection_config.saas_config.copy()

        # 4. Call the delete endpoint
        delete_url = delete_custom_connector_url.format(
            saas_connector_type=connector_type
        )
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.delete(delete_url, headers=auth_header)
        assert response.status_code == 200
        assert (
            response.json()["message"]
            == "Custom connector template successfully deleted."
        )

        # 5. Verify the file template is now active
        template = ConnectorRegistry.get_connector_template(connector_type)
        assert template is not None
        assert template.is_custom is False
        assert template.default_connector_available is False

        # 6. Verify the connection was updated to use the file template
        # Refresh the connection config from the database
        db.refresh(connection_config)

        # The SaaS config should have been updated to use the file template
        # We can verify this by checking that the SaaS config has changed
        assert connection_config.saas_config != original_saas_config

        # Verify the connection still has the same basic properties
        assert connection_config.key == "test_hubspot_connection_config"
        assert connection_config.name == "Test HubSpot Connector"
        assert (
            connection_config.description == "Test HubSpot ConnectionConfig description"
        )
        assert connection_config.secrets["private_app_token"] == "test_hubspot_token"

        # Clean up
        dataset_config = DatasetConfig.filter(
            db=db, conditions=(DatasetConfig.fides_key == instance_key)
        ).first()
        if dataset_config:
            dataset_config.delete(db)
            if dataset_config.ctl_dataset:
                dataset_config.ctl_dataset.delete(db=db)
        connection_config.delete(db)

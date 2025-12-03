import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.common.api.scope_registry import (
    CLIENT_READ,
    CONNECTOR_TEMPLATE_READ,
    CONNECTOR_TEMPLATE_REGISTER,
)
from fides.common.api.v1.urn_registry import (
    CONNECTOR_TEMPLATES_CONFIG,
    CONNECTOR_TEMPLATES_DATASET,
    CONNECTOR_TEMPLATES_REGISTER,
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
                    "detail": "1 validation error for SaaSConfig\ntest_request\n  Field required [type=missing, input_value={'fides_key': '<instance_...dentity': 'email'}]}}}]}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.7/v/missing"
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
                    "detail": "1 validation error for Dataset\ncollections.0.name\n  Field required [type=missing, input_value={'fides_meta': None, 'nam...': ['user.unique_id']}]}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.7/v/missing"
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

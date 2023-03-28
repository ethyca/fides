import json
from io import BytesIO
from typing import Dict, Optional
from unittest import mock
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.ops.api.v1.scope_registry import (
    CLIENT_READ,
    CONNECTION_AUTHORIZE,
    CONNECTOR_TEMPLATE_REGISTER,
    SAAS_CONFIG_CREATE_OR_UPDATE,
    SAAS_CONFIG_DELETE,
    SAAS_CONFIG_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    AUTHORIZE,
    REGISTER_CONNECTOR_TEMPLATE,
    SAAS_CONFIG,
    SAAS_CONFIG_VALIDATE,
    V1_URL_PREFIX,
)
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.core.config import CONFIG
from tests.ops.api.v1.endpoints.test_dataset_endpoints import _reject_key


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
        param_values = saas_config["endpoints"][0]["requests"]["read"]["param_values"][
            0
        ]
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
        assert (
            details[0]["msg"]
            == "Must have exactly one of 'identity', 'references', or 'connector_param'"
        )

    def test_put_validate_saas_config_wrong_reference_direction(
        self,
        saas_example_config,
        validate_saas_config_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_READ])
        saas_config = saas_example_config
        param_values = saas_config["endpoints"][0]["requests"]["read"]["param_values"][
            0
        ]
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
        assert (
            details[0]["msg"]
            == "References can only have a direction of 'from', found 'to'"
        )


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
        path_params = {
            "connection_key": saas_example_connection_config_without_saas_config.key
        }
        saas_config_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[SAAS_CONFIG_CREATE_OR_UPDATE])
        response = api_client.patch(
            saas_config_url, headers=auth_header, json=saas_example_config
        )
        assert response.status_code == 200

        updated_config = ConnectionConfig.get_by(
            db=db,
            field="key",
            value=saas_example_connection_config_without_saas_config.key,
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
        assert len(saas_config["endpoints"]) == 11


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
        assert len(response_body["endpoints"]) == 12
        assert response_body["type"] == "custom"


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


class TestAuthorizeConnection:
    @pytest.fixture
    def authorize_url(self, oauth2_authorization_code_connection_config) -> str:
        path = V1_URL_PREFIX + AUTHORIZE
        path_params = {
            "connection_key": oauth2_authorization_code_connection_config.key
        }
        return path.format(**path_params)

    def test_client_not_authenticated(self, api_client: TestClient, authorize_url):
        response = api_client.get(authorize_url)
        assert response.status_code == 401

    def test_client_wrong_scope(
        self, api_client: TestClient, authorize_url, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([CLIENT_READ])
        response = api_client.get(authorize_url, headers=auth_header)
        assert 403 == response.status_code

    @mock.patch(
        "fides.api.ops.api.v1.endpoints.saas_config_endpoints.OAuth2AuthorizationCodeAuthenticationStrategy.get_authorization_url"
    )
    def test_get_authorize_url(
        self,
        authorization_url_mock: Mock,
        api_client: TestClient,
        authorize_url,
        generate_auth_header,
    ):
        authorization_url = "https://localhost/auth/authorize"
        authorization_url_mock.return_value = authorization_url
        auth_header = generate_auth_header([CONNECTION_AUTHORIZE])
        response = api_client.get(authorize_url, headers=auth_header)
        response.raise_for_status()
        assert response.text == f'"{authorization_url}"'


class TestRegisterConnectorTemplate:
    def create_zip_file(self, file_data: Dict[str, str]) -> BytesIO:
        """
        Create a zip file in memory with the given files.

        Args:
            files (Dict[str, str]): A mapping of filenames to their contents

        Returns:
            io.BytesIO: An in-memory zip file with the specified files.
        """
        zip_buffer = BytesIO()

        with ZipFile(zip_buffer, "w") as zip_file:
            for filename, file_content in file_data.items():
                zip_file.writestr(filename, file_content)

        # resetting the file position pointer to the beginning of the stream
        # so the tests can read the zip file from the beginning
        zip_buffer.seek(0)
        return zip_buffer

    @pytest.fixture
    def register_connector_template_url(self) -> str:
        return V1_URL_PREFIX + REGISTER_CONNECTOR_TEMPLATE

    @pytest.fixture
    def complete_connector_template(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_missing_config(
        self,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "dataset.yml": planet_express_dataset,
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_wrong_contents_config(
        self,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": "planet_express_config",
                "dataset.yml": planet_express_dataset,
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_invalid_config(
        self,
        planet_express_invalid_config,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_invalid_config,
                "dataset.yml": planet_express_dataset,
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_missing_dataset(
        self,
        planet_express_config,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_wrong_contents_dataset(
        self,
        planet_express_config,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": "planet_express_dataset",
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_invalid_dataset(
        self,
        planet_express_config,
        planet_express_invalid_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_invalid_dataset,
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_no_functions(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_no_icon(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_functions,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "functions.py": planet_express_functions,
            }
        )

    @pytest.fixture
    def connector_template_duplicate_configs(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "1_config.yml": planet_express_config,
                "2_config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_duplicate_datasets(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "1_dataset.yml": planet_express_dataset,
                "2_dataset.yml": planet_express_dataset,
                "functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_duplicate_functions(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "1_functions.py": planet_express_functions,
                "2_functions.py": planet_express_functions,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def connector_template_duplicate_icons(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ):
        return self.create_zip_file(
            {
                "config.yml": planet_express_config,
                "dataset.yml": planet_express_dataset,
                "functions.py": planet_express_functions,
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
        CONFIG.security.allow_custom_connector_functions = True
        auth_header = generate_auth_header(scopes=[CLIENT_READ])
        response = api_client.post(
            register_connector_template_url,
            headers=auth_header,
            files={"connector_template": complete_connector_template},
        )
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "zip_file, status_code, details",
        [
            ("complete_connector_template", 200, None),
            (
                "connector_template_missing_config",
                400,
                {"detail": "Zip file does not contain a config.yml file."},
            ),
            (
                "connector_template_wrong_contents_config",
                400,
                {
                    "detail": "Config contents do not contain a 'saas_config' key at the root level."
                },
            ),
            (
                "connector_template_invalid_config",
                400,
                {
                    "detail": "1 validation error for ConnectorTemplate\nconfig -> test_request\n  field required (type=value_error.missing)"
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
                    "detail": "Dataset contents do not contain a 'dataset' key at the root level."
                },
            ),
            (
                "connector_template_invalid_dataset",
                400,
                {
                    "detail": "1 validation error for ConnectorTemplate\ndataset -> collections -> 0 -> name\n  field required (type=value_error.missing)"
                },
            ),
            ("connector_template_no_functions", 200, None),
            ("connector_template_no_icon", 200, None),
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
                "connector_template_duplicate_functions",
                400,
                {"detail": "Multiple Python (.py) files found, only one is allowed."},
            ),
            (
                "connector_template_duplicate_icons",
                400,
                {"detail": "Multiple svg files found, only one is allowed."},
            ),
        ],
    )
    def test_register_connector_template_allow_custom_connector_functions(
        self,
        api_client: TestClient,
        register_connector_template_url,
        generate_auth_header,
        zip_file,
        status_code,
        details,
        request,
    ):
        CONFIG.security.allow_custom_connector_functions = True
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.post(
            register_connector_template_url,
            headers=auth_header,
            files={"connector_template": request.getfixturevalue(zip_file)},
        )
        assert response.status_code == status_code
        assert response.json() == details

    @pytest.mark.parametrize(
        "zip_file, status_code, details",
        [
            (
                "complete_connector_template",
                400,
                {
                    "detail": "The import of connector templates with custom functions is disabled by the 'security.allow_custom_connector_functions' setting."
                },
            ),
            (
                "connector_template_no_functions",
                200,
                None,
            ),
        ],
    )
    def test_register_connector_template_disallow_custom_connector_functions(
        self,
        api_client: TestClient,
        register_connector_template_url,
        generate_auth_header,
        zip_file,
        status_code,
        details,
        request,
    ):
        CONFIG.security.allow_custom_connector_functions = False
        auth_header = generate_auth_header(scopes=[CONNECTOR_TEMPLATE_REGISTER])
        response = api_client.post(
            register_connector_template_url,
            headers=auth_header,
            files={"connector_template": request.getfixturevalue(zip_file)},
        )
        assert response.status_code == status_code
        assert response.json() == details

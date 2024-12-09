import pytest
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.db.seed import get_client_id, load_default_access_policy
from fides.api.util.data_category import get_user_data_categories
from fides.common.api.scope_registry import (
    DATASET_CREATE_OR_UPDATE,
    DATASET_READ,
    DATASET_TEST,
)
from tests.ops.api.v1.endpoints.test_dataset_endpoints import get_connection_dataset_url


class TestDatasetInputs:
    def test_dataset_inputs_not_authenticated(
        self, dataset_config, connection_config, api_client
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        response = api_client.get(dataset_url + "/inputs", headers={})
        assert response.status_code == 401

    def test_dataset_inputs_wrong_scope(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.get(dataset_url + "/inputs", headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "auth_header,expected_status",
        [
            ("owner_auth_header", HTTP_200_OK),
            ("contributor_auth_header", HTTP_200_OK),
            ("viewer_and_approver_auth_header", HTTP_200_OK),
            ("viewer_auth_header", HTTP_200_OK),
            ("approver_auth_header", HTTP_403_FORBIDDEN),
        ],
    )
    def test_dataset_inputs_with_roles(
        self,
        dataset_config,
        connection_config,
        auth_header,
        expected_status,
        test_client: TestClient,
        request,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = request.getfixturevalue(auth_header)
        response = test_client.get(
            dataset_url + "/inputs",
            headers=auth_header,
        )
        assert response.status_code == expected_status

    def test_dataset_inputs_connection_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(None, None)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            dataset_url + "/inputs",
            headers=auth_header,
        )
        assert response.status_code == 404

    def test_dataset_inputs_dataset_does_not_exist(
        self,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, None)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            dataset_url + "/inputs",
            headers=auth_header,
        )
        assert response.status_code == 404

    def test_dataset_inputs(
        self,
        connection_config,
        dataset_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            dataset_url + "/inputs",
            headers=auth_header,
        )
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"email": None}


class TestDatasetReachability:
    def test_dataset_reachability_not_authenticated(
        self, dataset_config, connection_config, api_client
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        response = api_client.get(dataset_url + "/reachability", headers={})
        assert response.status_code == 401

    def test_dataset_test_wrong_scope(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.get(dataset_url + "/reachability", headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "auth_header,expected_status",
        [
            ("owner_auth_header", HTTP_200_OK),
            ("contributor_auth_header", HTTP_200_OK),
            ("viewer_and_approver_auth_header", HTTP_200_OK),
            ("viewer_auth_header", HTTP_200_OK),
            ("approver_auth_header", HTTP_403_FORBIDDEN),
        ],
    )
    def test_dataset_reachability_with_roles(
        self,
        dataset_config,
        connection_config,
        auth_header,
        expected_status,
        test_client: TestClient,
        request,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = request.getfixturevalue(auth_header)
        response = test_client.get(
            dataset_url + "/reachability",
            headers=auth_header,
        )
        assert response.status_code == expected_status

    def test_dataset_reachability_connection_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(None, None)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            dataset_url + "/reachability",
            headers=auth_header,
        )
        assert response.status_code == 404

    def test_dataset_reachability_dataset_does_not_exist(
        self,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, None)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            dataset_url + "/reachability",
            headers=auth_header,
        )
        assert response.status_code == 404

    def test_dataset_reachability(
        self,
        connection_config,
        dataset_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            dataset_url + "/reachability",
            headers=auth_header,
        )
        assert response.status_code == HTTP_200_OK
        assert set(response.json().keys()) == {"reachable", "details"}


@pytest.mark.integration_external
@pytest.mark.integration_postgres
class TestDatasetTest:
    @pytest.fixture(scope="function")
    def default_access_policy(self, db) -> None:
        load_default_access_policy(db, get_client_id(db), get_user_data_categories())

    def test_dataset_test_not_authenticated(
        self, dataset_config, connection_config, api_client
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        response = api_client.post(dataset_url + "/test", headers={})
        assert response.status_code == 401

    @pytest.mark.usefixtures("dsr_testing_tools_enabled")
    def test_dataset_test_wrong_scope(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.post(dataset_url + "/test", headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "auth_header,expected_status",
        [
            ("owner_auth_header", HTTP_200_OK),
            ("contributor_auth_header", HTTP_200_OK),
            ("viewer_and_approver_auth_header", HTTP_403_FORBIDDEN),
            ("viewer_auth_header", HTTP_403_FORBIDDEN),
            ("approver_auth_header", HTTP_403_FORBIDDEN),
        ],
    )
    @pytest.mark.usefixtures("default_access_policy", "dsr_testing_tools_enabled")
    def test_dataset_test_with_roles(
        self,
        dataset_config,
        connection_config,
        auth_header,
        expected_status,
        test_client: TestClient,
        request,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = request.getfixturevalue(auth_header)
        response = test_client.post(
            dataset_url + "/test",
            headers=auth_header,
            json={"email": "user@example.com"},
        )
        assert response.status_code == expected_status

    @pytest.mark.usefixtures("dsr_testing_tools_enabled")
    def test_dataset_test_connection_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(None, None)
        auth_header = generate_auth_header(scopes=[DATASET_TEST])
        response = api_client.post(
            dataset_url + "/test",
            headers=auth_header,
            json={"email": "user@example.com"},
        )
        assert response.status_code == 404

    @pytest.mark.usefixtures("dsr_testing_tools_enabled")
    def test_dataset_test_dataset_does_not_exist(
        self,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, None)
        auth_header = generate_auth_header(scopes=[DATASET_TEST])
        response = api_client.post(
            dataset_url + "/test",
            headers=auth_header,
            json={"email": "user@example.com"},
        )
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "payload, expected_response",
        [
            ("user@example.com", "Inputs must be JSON formatted"),
            ({}, "No inputs provided"),
            ({"loyalty_id": None}, 'Input "loyalty_id" cannot be empty'),
            (
                {"email": "user"},
                '"email" value is not a valid email address: An email address must have an @-sign.',
            ),
        ],
    )
    @pytest.mark.usefixtures("default_access_policy", "dsr_testing_tools_enabled")
    def test_dataset_test_invalid_payloads(
        self,
        connection_config,
        dataset_config,
        api_client: TestClient,
        generate_auth_header,
        payload,
        expected_response,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_TEST])
        response = api_client.post(
            dataset_url + "/test",
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == expected_response

    @pytest.mark.usefixtures(
        "default_access_policy", "postgres_integration_db", "dsr_testing_tools_enabled"
    )
    def test_dataset_test(
        self,
        connection_config,
        dataset_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_TEST])
        response = api_client.post(
            dataset_url + "/test",
            headers=auth_header,
            json={"email": "jane@example.com"},
        )
        assert response.status_code == HTTP_200_OK
        assert "privacy_request_id" in response.json().keys()

    @pytest.mark.usefixtures(
        "default_access_policy", "postgres_integration_db", "dsr_testing_tools_disabled"
    )
    def test_dataset_test_disabled(
        self,
        connection_config,
        dataset_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_TEST])
        response = api_client.post(
            dataset_url + "/test",
            headers=auth_header,
            json={"email": "jane@example.com"},
        )
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "DSR testing tools are not enabled."

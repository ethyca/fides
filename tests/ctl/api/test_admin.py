# pylint: disable=missing-docstring, redefined-outer-name
import pytest
from starlette.testclient import TestClient

from fides.api.util.endpoint_utils import API_PREFIX
from fides.config import FidesConfig


def test_db_reset_dev_mode_enabled(
    test_config: FidesConfig,
    test_client: TestClient,
) -> None:
    assert test_config.dev_mode
    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/admin/db/reset/",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {"message": "Fides database action performed successfully: reset"}
    }


def test_db_reset_dev_mode_disabled(
    test_config: FidesConfig,
    test_config_dev_mode_disabled: FidesConfig,  # temporarily switches off config.dev_mode
    test_client: TestClient,
) -> None:
    error_message = (
        "Resetting the application database outside of dev_mode is not supported."
    )
    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/admin/db/reset/",
        headers=test_config.user.auth_header,
    )

    assert response.status_code == 501
    assert response.json()["detail"] == error_message

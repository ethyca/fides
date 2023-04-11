# pylint: disable=missing-docstring, redefined-outer-name
import pytest
from starlette.testclient import TestClient

from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.utils import errors
from fides.core.config import FidesConfig


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
    assert response.json() == {"data": {"message": "fides database reset"}}


def test_db_reset_dev_mode_disabled(
    test_config: FidesConfig,
    test_config_dev_mode_disabled: FidesConfig,  # temporarily switches off config.dev_mode
    test_client: TestClient,
) -> None:
    with pytest.raises(
        errors.FunctionalityNotConfigured,
        match="unable to reset fides database outside of dev_mode.",
    ):
        test_client.post(
            test_config.cli.server_url + API_PREFIX + "/admin/db/reset/",
            headers=test_config.user.auth_header,
        )

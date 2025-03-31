import pytest
from starlette.testclient import TestClient

from fides.api.util.endpoint_utils import API_PREFIX
from fides.config import CONFIG, FidesConfig


class TestDBResetEndpoints:
    async def test_db_reset_dev_mode_enabled(
        self, test_config: FidesConfig, async_api_client: TestClient, root_auth_header
    ) -> None:
        assert CONFIG.dev_mode
        response = await async_api_client.post(
            test_config.cli.server_url + API_PREFIX + "/admin/db/reset/",
            headers=root_auth_header,
        )
        assert response.status_code == 200
        assert response.json() == {
            "data": {"message": "Fides database action performed successfully: reset"}
        }

    @pytest.mark.usefixtures("test_config_dev_mode_disabled")
    async def test_db_reset_dev_mode_disabled(
        self, test_config: FidesConfig, async_api_client: TestClient, root_auth_header
    ) -> None:
        assert not CONFIG.dev_mode
        response = await async_api_client.post(
            test_config.cli.server_url + API_PREFIX + "/admin/db/reset/",
            headers=root_auth_header,
        )

        assert response.status_code == 501
        assert (
            response.json()["detail"]
            == "Resetting the application database outside of dev_mode is not supported."
        )

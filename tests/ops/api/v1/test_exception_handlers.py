import pytest

from fides.api.ops.api.v1.scope_registry import CLIENT_CREATE
from fides.api.ops.api.v1.urn_registry import HEALTH, PRIVACY_REQUESTS, V1_URL_PREFIX


@pytest.fixture
def mock_config_db_disabled(config):
    db_enabled = config.database.enabled
    config.database.enabled = False
    yield
    config.database.enabled = db_enabled


@pytest.fixture
def mock_config_redis_disabled(config):
    redis_enabled = config.redis.enabled
    config.redis.enabled = False
    yield
    config.redis.enabled = redis_enabled


class TestExceptionHandlers:
    @pytest.mark.usefixtures("mock_config_redis_disabled")
    @pytest.mark.parametrize("auth_header", [[CLIENT_CREATE]], indirect=True)
    def test_redis_disabled(self, auth_header, api_client):
        # Privacy requests endpoint should not work
        request_body = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "identity": {"email": "customer-1@example.com"},
                "policy_key": "my_separate_policy",
            }
        ]
        expected_response = {
            "message": "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        }
        response = api_client.post(
            V1_URL_PREFIX + PRIVACY_REQUESTS, headers=auth_header, json=request_body
        )
        response_body = response.json()
        assert 500 == response.status_code
        assert expected_response == response_body

        # health endpoint should still work
        expected_response = "no cache configured"
        response = api_client.get(HEALTH)
        response_body = response.json()
        assert 200 == response.status_code
        assert expected_response == response_body["cache"]

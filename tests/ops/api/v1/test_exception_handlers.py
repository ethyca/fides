import json

import pytest
from starlette.testclient import TestClient

from fides.common.api.scope_registry import CLIENT_CREATE
from fides.common.api.v1.urn_registry import HEALTH, PRIVACY_REQUESTS, V1_URL_PREFIX
from fides.config import CONFIG


@pytest.fixture
def mock_config_db_disabled():
    db_enabled = CONFIG.database.enabled
    CONFIG.database.enabled = False
    yield
    CONFIG.database.enabled = db_enabled


@pytest.fixture
def mock_config_redis_disabled():
    redis_enabled = CONFIG.redis.enabled
    CONFIG.redis.enabled = False
    yield
    CONFIG.redis.enabled = redis_enabled


class TestExceptionHandlers:
    @pytest.mark.usefixtures("mock_config_redis_disabled")
    def test_redis_disabled(self, api_client: TestClient, generate_auth_header, policy):
        auth_header = generate_auth_header([CLIENT_CREATE])
        # Privacy requests endpoint should not work
        request_body = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "identity": {"email": "customer-1@example.com"},
                "policy_key": policy.key,
            }
        ]
        expected_response = {
            "message": "Application Redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a Redis cache."
        }
        response = api_client.post(
            V1_URL_PREFIX + PRIVACY_REQUESTS, headers=auth_header, json=request_body
        )
        response_body = json.loads(response.text)
        assert 500 == response.status_code
        assert expected_response == response_body

        # health endpoint should still work
        expected_response = "no cache configured"
        response = api_client.get(HEALTH)
        response_body = json.loads(response.text)
        assert 200 == response.status_code
        assert expected_response == response_body["cache"]

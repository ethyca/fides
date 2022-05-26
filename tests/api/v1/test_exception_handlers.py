import json

import pytest
from starlette.testclient import TestClient

from fidesops.api.v1.scope_registry import CLIENT_CREATE
from fidesops.api.v1.urn_registry import CLIENT, HEALTH, PRIVACY_REQUESTS, V1_URL_PREFIX
from fidesops.core import config


@pytest.fixture
def mock_config_db_disabled():
    db_enabled = config.config.database.ENABLED
    config.config.database.ENABLED = False
    yield
    config.config.database.ENABLED = db_enabled


@pytest.fixture
def mock_config_redis_disabled():
    redis_enabled = config.config.redis.ENABLED
    config.config.redis.ENABLED = False
    yield
    config.config.redis.ENABLED = redis_enabled


class TestExceptionHandlers:
    @pytest.mark.usefixtures("mock_config_db_disabled")
    def test_db_disabled(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header([CLIENT_CREATE])
        # oauth endpoint should not work
        expected_response = {
            "message": "Application database required, but it is currently disabled! Please update your application configuration to enable integration with an application database."
        }
        response = api_client.post(V1_URL_PREFIX + CLIENT, headers=auth_header)
        response_body = json.loads(response.text)
        assert 500 == response.status_code
        assert expected_response == response_body

        # health endpoint should still work
        expected_response = {"healthy": True}
        response = api_client.get(HEALTH)
        response_body = json.loads(response.text)
        assert 200 == response.status_code
        assert expected_response == response_body

    @pytest.mark.usefixtures("mock_config_redis_disabled")
    def test_redis_disabled(self, api_client: TestClient, generate_auth_header):
        auth_header = generate_auth_header([CLIENT_CREATE])
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
        response_body = json.loads(response.text)
        assert 500 == response.status_code
        assert expected_response == response_body

        # health endpoint should still work
        expected_response = {"healthy": True}
        response = api_client.get(HEALTH)
        response_body = json.loads(response.text)
        assert 200 == response.status_code
        assert expected_response == response_body

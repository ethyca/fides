import pytest
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from fides.common.api.v1.urn_registry import PURPOSES, V1_URL_PREFIX


class TestGetPurposes:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PURPOSES

    def test_get_purposes_unauthenticated(self, url, api_client):
        response = api_client.get(url)
        assert response.status_code == HTTP_401_UNAUTHORIZED

    def test_get_purposes(self, url, api_client, generate_auth_header):
        auth_header = generate_auth_header([])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == HTTP_200_OK

        data = response.json()
        assert "purposes" in data
        assert "special_purposes" in data
        assert len(data["purposes"]) == 11
        assert len(data["special_purposes"]) == 2

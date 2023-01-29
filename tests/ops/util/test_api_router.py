import pytest
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from fides.api.ops.api.v1.scope_registry import PRIVACY_REQUEST_READ
from fides.api.ops.api.v1.urn_registry import PRIVACY_REQUESTS, V1_URL_PREFIX


class TestApiRouter:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    @pytest.mark.parametrize("auth_header", [[PRIVACY_REQUEST_READ]], indirect=True)
    def test_no_trailing_slash(self, auth_header, api_client, url) -> None:
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK

    @pytest.mark.parametrize("auth_header", [[PRIVACY_REQUEST_READ]], indirect=True)
    def test_trailing_slash(self, auth_header, api_client, url) -> None:
        resp = api_client.get(f"{url}/", headers=auth_header)
        assert resp.status_code == HTTP_200_OK

    @pytest.mark.parametrize(
        "route",
        [
            "/route/does/not/exist",
            "/route/does/not/exist/",
            f"{V1_URL_PREFIX}/route/does/not/exist",
            f"{V1_URL_PREFIX}/route/does/not/exist/",
        ],
    )
    @pytest.mark.parametrize("auth_header", [[PRIVACY_REQUEST_READ]], indirect=True)
    def test_non_existent_route_404(self, auth_header, route, api_client, url) -> None:
        resp = api_client.get(f"{url}{route}", headers=auth_header)
        assert resp.status_code == HTTP_404_NOT_FOUND

from unittest import mock
from unittest.mock import Mock

import pytest
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from starlette.testclient import TestClient

from fides.api.models.client import ClientDetail
from fides.common.api.scope_registry import PRIVACY_REQUEST_READ
from fides.common.api.v1.urn_registry import PRIVACY_REQUESTS, V1_URL_PREFIX


class TestApiRouter:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    def test_no_trailing_slash(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == HTTP_200_OK

    def test_trailing_slash(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        resp = api_client.get(f"{url}/", headers=auth_header)
        assert resp.status_code == HTTP_200_OK

    def test_non_existent_route_404(
        self, api_client: TestClient, generate_auth_header, url
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        resp = api_client.get(f"{url}/route/does/not/exist", headers=auth_header)
        assert resp.status_code == HTTP_404_NOT_FOUND

        resp_2 = api_client.get(f"{url}/route/does/not/exist/", headers=auth_header)
        assert resp_2.status_code == HTTP_404_NOT_FOUND

        resp_3 = api_client.get(
            f"{V1_URL_PREFIX}/route/does/not/exist", headers=auth_header
        )
        assert resp_3.status_code == HTTP_404_NOT_FOUND

        resp_4 = api_client.get(
            f"{V1_URL_PREFIX}/route/does/not/exist/", headers=auth_header
        )
        assert resp_4.status_code == HTTP_404_NOT_FOUND

    @mock.patch("fides.api.main.get_admin_index_as_response")
    def test_malicious_url(
        self,
        mock_admin_index_response: Mock,
        api_client: TestClient,
        url,
    ) -> None:
        """
        Assert that malicious URLs that attempt path traversal attacks
        are NOT treated as legitimate URLs, and instead the basic "admin" index
        response is returned.
        """

        # admin index response changes depending on environment.
        # we mock the value here to give ourselves a consistent response to evaluate against.
        # what we want to ensure is that the admin index response is what gets returned,
        # indicating that the attempted path traversal does not occur.
        mock_admin_index_response.return_value = "<h1>Privacy is a Human Right!</h1>"

        malicious_paths = [
            "../../../../../../../../../etc/passwd",
            "..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2fetc/passwd",
            "%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
            "..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f/etc/passwd",
            ".../...//.../...//.../...//.../...//.../...//.../...//.../...//.../...//.../...//etc/passwd",
            "...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2fetc/passwd",
            "%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//etc/passwd",
            "%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2fetc/passwd",
        ]
        for path in malicious_paths:
            resp = api_client.get(f"{url}/{path}")
            assert resp.status_code == 200
            assert resp.text == "<h1>Privacy is a Human Right!</h1>"

    def test_nextjs_catch_all_segments_urls(
        self,
        api_client: TestClient,
        url,
    ) -> None:
        """
        Assert that NextJS Catch-all Segments aren't blocked by our sanitise_url_path.
        """

        non_malicious_paths = [
            "/_next/static/chunks/pages/dataset/[datasetId]/[collectionName]/[...subfieldNames]-6596c3d4607847d0.js",
            "/_next/static/chunks/pages/dataset/[datasetId]/[...collectionName]/6596c3d4607847d0.js",
            "/_next/static/chunks/pages/dataset/[...datasetId]/[collectionName]/6596c3d4607847d0.js",
        ]
        for path in non_malicious_paths:
            resp = api_client.get(f"{url}/{path}")
            assert resp.status_code == 404
            assert resp.text == '{"detail":"Item not found"}'

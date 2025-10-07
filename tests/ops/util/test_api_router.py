from unittest import mock
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from starlette.testclient import TestClient

from fides.api.common_exceptions import MalisciousUrlException
from fides.api.main import sanitise_url_path
from fides.api.models.client import ClientDetail
from fides.api.util.api_router import APIRouter
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

    @pytest.mark.parametrize(
        "path, should_be_malicious",
        (
            (
                "/_next/static/chunks/pages/dataset/[datasetId]/[collectionName]/[...subfieldNames]-6596c3d4607847d0.js",
                False,
            ),
            (
                "/_next/static/chunks/pages/dataset/[datasetId]/[...collectionName]/6596c3d4607847d0.js",
                False,
            ),
            (
                "/_next/static/chunks/pages/dataset/[...datasetId]/[collectionName]/6596c3d4607847d0.js",
                False,
            ),
            (
                "[datasetName]/[collectionName]/[...subFields]-js/../../../../etc/passwd",
                True,
            ),
            (
                "/_next/static/chunks/pages/dataset/[datasetId]/[collectionName]/[[...subfieldNames]]-6596c3d4607847d0.js",
                False,
            ),
            (
                "/_next/static/chunks/pages/dataset/[datasetId]/[[...collectionName]]/6596c3d4607847d0.js",
                False,
            ),
            (
                "/_next/static/chunks/pages/dataset/[[...datasetId]]/[collectionName]/6596c3d4607847d0.js",
                False,
            ),
            (
                "[datasetName]/[collectionName]/[[...subFields]]-js/../../../../etc/passwd",
                True,
            ),
            ("../../../../../../../../../etc/passwd", True),
            ("..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2f..%2fetc/passwd", True),
            (
                "%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
                True,
            ),
            (
                "%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
                True,
            ),
            (
                "..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f..%c0%2f/etc/passwd",
                True,
            ),
            (
                ".../...//.../...//.../...//.../...//.../...//.../...//.../...//.../...//.../...//etc/passwd",
                True,
            ),
            (
                "...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2f...%2f...%2f%2fetc/passwd",
                True,
            ),
            (
                "%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//%2e%2e%2e/%2e%2e%2e//etc/passwd",
                True,
            ),
            (
                "%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2f%2e%2e%2e%2f%2e%2e%2e%2f%2fetc/passwd",
                True,
            ),
        ),
    )
    def test_sanitise_url_path(self, path, should_be_malicious):
        if should_be_malicious:
            with pytest.raises(MalisciousUrlException):
                sanitise_url_path(path)

        else:
            assert sanitise_url_path(path) == path

    def test_add_api_route_with_trailing_slash(self) -> None:
        """
        Test that routes registered via add_api_route() work with and without trailing slashes.
        This is important for routes that don't use decorators (like the filters endpoints).
        """
        # Create a test app with our custom APIRouter
        app = FastAPI()
        router = APIRouter(prefix="/test")

        # Define a simple endpoint
        async def test_endpoint() -> dict[str, str]:
            return {"message": "success"}

        # Register it using add_api_route (not a decorator)
        router.add_api_route(
            path="/endpoint",
            endpoint=test_endpoint,
            methods=["GET"],
        )

        app.include_router(router)
        test_client = TestClient(app)

        # Test without trailing slash
        resp_without_slash = test_client.get("/test/endpoint")
        assert resp_without_slash.status_code == HTTP_200_OK
        assert resp_without_slash.json() == {"message": "success"}

        # Test with trailing slash
        resp_with_slash = test_client.get("/test/endpoint/")
        assert resp_with_slash.status_code == HTTP_200_OK
        assert resp_with_slash.json() == {"message": "success"}

        # Verify both return the same response
        assert resp_without_slash.json() == resp_with_slash.json()

    def test_add_api_route_with_query_params_and_trailing_slash(self) -> None:
        """
        Test that routes with query parameters work correctly with trailing slashes.
        This specifically tests the filters endpoint use case.
        """
        # Create a test app with our custom APIRouter
        app = FastAPI()
        router = APIRouter(prefix="/api")

        # Define an endpoint that accepts query parameters
        async def filter_endpoint(filter_id: str | None = None) -> dict[str, str | None]:
            return {"filter_id": filter_id}

        # Register it using add_api_route with dependencies (like filters.py does)
        router.add_api_route(
            path="/filters",
            endpoint=filter_endpoint,
            methods=["GET"],
        )

        app.include_router(router)
        test_client = TestClient(app)

        # Test without trailing slash and with query params
        resp1 = test_client.get("/api/filters?filter_id=test123")
        assert resp1.status_code == HTTP_200_OK
        assert resp1.json() == {"filter_id": "test123"}

        # Test with trailing slash and with query params
        resp2 = test_client.get("/api/filters/?filter_id=test123")
        assert resp2.status_code == HTTP_200_OK
        assert resp2.json() == {"filter_id": "test123"}

        # Verify both return the same response
        assert resp1.json() == resp2.json()

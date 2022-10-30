from starlette.testclient import TestClient

import fides
from fides.api.ops.api.v1.urn_registry import HEALTH


def test_health(api_client: TestClient) -> None:
    response = api_client.get(HEALTH)
    json = response.json()
    expected_response = {
        "cache": "healthy",
        "webserver": "healthy",
        "database": "healthy",
        "version": str(fides.__version__),
    }
    assert json == expected_response

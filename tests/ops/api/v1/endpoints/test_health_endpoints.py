from fidesops.ops.api.v1.urn_registry import HEALTH
from starlette.testclient import TestClient


def test_health(api_client: TestClient) -> None:
    response = api_client.get(HEALTH)
    assert response.json() == {
        "webserver": "healthy",
        "database": "healthy",
        "cache": "healthy",
    }

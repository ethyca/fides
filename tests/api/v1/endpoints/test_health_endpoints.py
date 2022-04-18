from starlette.testclient import TestClient

from fidesops.api.v1.urn_registry import HEALTH


def test_health(api_client: TestClient) -> None:
    response = api_client.get(HEALTH)
    assert response.json() == {"healthy": True}

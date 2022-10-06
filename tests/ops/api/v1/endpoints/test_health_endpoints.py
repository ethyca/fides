from starlette.testclient import TestClient

import fides
from fides.api.ops.api.v1.urn_registry import HEALTH


def test_health(api_client: TestClient) -> None:
    response = api_client.get(HEALTH)
    json = response.json()
    assert json["webserver"] == "healthy"
    assert json["database"] == "healthy"
    assert json["cache"] == "healthy"
    assert json["version"] == str(fides.__version__)

from starlette.testclient import TestClient


class CustomTestException(BaseException):
    """Mock Non-HTTP Exception"""

    pass


def test_read_autogenerated_docs(api_client: TestClient):
    """Test to ensure automatically generated docs build properly"""
    response = api_client.get(f"/openapi.json")
    assert response.status_code == 200

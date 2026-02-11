"""
Conftest for common/cache tests. Overrides session-scoped fixtures so the
real FastAPI app, DB, and Celery worker are not started when running only these tests.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture(scope="session")
def test_client():
    """Minimal test client mock so app/DB are not started for cache-only test runs."""
    client = MagicMock()
    response = MagicMock()
    response.status_code = 200
    client.get = MagicMock(return_value=response)
    client.post = MagicMock(return_value=response)
    client.put = MagicMock(return_value=response)
    client.patch = MagicMock(return_value=response)
    client.delete = MagicMock(return_value=response)
    yield client


@pytest.fixture(scope="session", autouse=True)
def app():
    """Mock app fixture so FastAPI doesn't start."""
    yield MagicMock()


@pytest.fixture(autouse=True, scope="session")
def celery_use_virtual_worker():
    """No-op so we don't start a real Celery worker (and pull in DB) for cache tests."""
    yield None

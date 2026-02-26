"""
Conftest for common/cache tests. Overrides session-scoped fixtures so the
real FastAPI app, DB, and Celery worker are not started when running only these tests.
"""

from unittest.mock import MagicMock

import pytest


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


@pytest.fixture(scope="session")
def api_client():
    """Minimal API client mock so app/DB are not started for cache-only test runs."""
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


@pytest.fixture(scope="session")
def config():
    """Mock config so we don't pull in real config."""
    from fides.config import get_config

    config = get_config()
    config.test_mode = True
    yield config


@pytest.fixture(scope="session")
def db(api_client, config):
    """Override db fixture to prevent database connection."""
    yield MagicMock()


@pytest.fixture(scope="session")
async def async_session():
    """Override async_session fixture to prevent database connection."""
    yield MagicMock()


@pytest.fixture(scope="function", autouse=True)
async def clear_db_tables(db, async_session):
    """Override clear_db_tables to no-op for cache-only tests."""
    yield
    # No cleanup needed for MockRedis tests


@pytest.fixture(autouse=True, scope="session")
def celery_use_virtual_worker():
    """No-op so we don't start a real Celery worker (and pull in DB) for cache tests."""
    yield None

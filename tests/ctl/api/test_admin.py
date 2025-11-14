# pylint: disable=missing-docstring, redefined-outer-name
import pytest
from starlette.testclient import TestClient

from fides.api.models.application_config import ApplicationConfig
from fides.api.util.endpoint_utils import API_PREFIX
from fides.config import FidesConfig


@pytest.fixture(scope="function")
def memory_watchdog_enabled(db):
    """Fixture to enable memory watchdog for tests."""
    ApplicationConfig.create_or_update(
        db,
        data={"api_set": {"execution": {"memory_watchdog_enabled": True}}},
    )
    yield
    ApplicationConfig.create_or_update(
        db,
        data={"api_set": {"execution": {"memory_watchdog_enabled": False}}},
    )


@pytest.fixture(scope="function")
def memory_watchdog_disabled(db):
    """Fixture to explicitly disable memory watchdog for tests."""
    ApplicationConfig.create_or_update(
        db,
        data={"api_set": {"execution": {"memory_watchdog_enabled": False}}},
    )
    yield
    # Reset is handled by default behavior (memory_watchdog_enabled defaults to False)


def test_db_reset_dev_mode_enabled(
    test_config: FidesConfig,
    test_client: TestClient,
) -> None:
    assert test_config.dev_mode
    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/admin/db/reset/",
        headers=test_config.user.auth_header,
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {"message": "Fides database action performed successfully: reset"}
    }


def test_db_reset_dev_mode_disabled(
    test_config: FidesConfig,
    test_config_dev_mode_disabled: FidesConfig,  # temporarily switches off config.dev_mode
    test_client: TestClient,
) -> None:
    error_message = (
        "Resetting the application database outside of dev_mode is not supported."
    )
    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/admin/db/reset/",
        headers=test_config.user.auth_header,
    )

    assert response.status_code == 501
    assert response.json()["detail"] == error_message


def test_heap_dump_when_disabled(
    test_config: FidesConfig,
    test_client: TestClient,
) -> None:
    """Test that heap dump returns 405 when memory_watchdog_enabled is False (default)."""
    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/admin/heap_dump/",
        headers=test_config.user.auth_header,
    )

    assert response.status_code == 405
    assert response.json()["detail"] == (
        "Heap dump functionality is not enabled. "
        "Set memory_watchdog_enabled to true in application configuration."
    )


@pytest.mark.usefixtures("memory_watchdog_disabled")
def test_heap_dump_explicitly_disabled(
    test_config: FidesConfig,
    test_client: TestClient,
) -> None:
    """Test that heap dump returns 405 when memory_watchdog_enabled is explicitly set to False."""
    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/admin/heap_dump/",
        headers=test_config.user.auth_header,
    )

    assert response.status_code == 405
    assert response.json()["detail"] == (
        "Heap dump functionality is not enabled. "
        "Set memory_watchdog_enabled to true in application configuration."
    )


@pytest.mark.usefixtures("memory_watchdog_enabled")
def test_heap_dump_logs_heap_stats(
    test_config: FidesConfig,
    test_client: TestClient,
    loguru_caplog,
) -> None:
    """Test that heap dump endpoint logs heap statistics."""
    response = test_client.post(
        test_config.cli.server_url + API_PREFIX + "/admin/heap_dump/",
        headers=test_config.user.auth_header,
    )

    assert response.status_code == 200

    # Verify that the heap dump was logged
    log_output = loguru_caplog.text

    # Check for the info message that heap dump was triggered
    assert "Manual heap dump triggered via API" in log_output

    # Check for key sections of the heap dump in logs
    assert "MEMORY DUMP" in log_output
    assert "PROCESS MEMORY STATS" in log_output
    assert "OBJECT TYPE COUNTS (Top 10)" in log_output
    assert "GARBAGE COLLECTOR STATS" in log_output

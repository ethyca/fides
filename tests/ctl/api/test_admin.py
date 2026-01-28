# pylint: disable=missing-docstring, redefined-outer-name
from unittest.mock import patch

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
        test_config.cli.server_url + API_PREFIX + "/admin/heap-dump/",
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
        test_config.cli.server_url + API_PREFIX + "/admin/heap-dump/",
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
        test_config.cli.server_url + API_PREFIX + "/admin/heap-dump/",
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


class TestBackfillEndpoints:
    """Tests for the /admin/backfill endpoint."""

    def test_starts_background_task(
        self,
        test_config: FidesConfig,
        test_client: TestClient,
    ) -> None:
        """Test that backfill endpoint returns 202 and correct message."""
        with patch(
            "fides.api.api.v1.endpoints.admin.acquire_backfill_lock",
            return_value=True,
        ), patch(
            "fides.api.api.v1.endpoints.admin.run_backfill_manually",
        ):
            response = test_client.post(
                test_config.cli.server_url + API_PREFIX + "/admin/backfill",
                headers=test_config.user.auth_header,
            )

        assert response.status_code == 202
        data = response.json()["data"]
        assert "Backfill started in background" in data["message"]
        assert "GET /api/v1/admin/backfill" in data["message"]
        assert "server logs" in data["message"]
        assert data["config"]["batch_size"] == 5000
        assert data["config"]["batch_delay_seconds"] == 1.0

    def test_conflict_when_running(
        self,
        test_config: FidesConfig,
        test_client: TestClient,
    ) -> None:
        """Test that backfill endpoint returns 409 when backfill already running."""
        with patch(
            "fides.api.api.v1.endpoints.admin.acquire_backfill_lock",
            return_value=False,
        ):
            response = test_client.post(
                test_config.cli.server_url + API_PREFIX + "/admin/backfill",
                headers=test_config.user.auth_header,
            )

        assert response.status_code == 409
        assert "already running" in response.json()["detail"]

    @pytest.mark.parametrize(
        "payload,expected_status",
        [
            # Valid custom parameters
            ({"batch_size": 1000, "batch_delay_seconds": 2.0}, 202),
            # batch_size too small
            ({"batch_size": 50}, 422),
            # batch_size too large
            ({"batch_size": 100000}, 422),
            # batch_delay_seconds too small
            ({"batch_delay_seconds": 0.05}, 422),
            # batch_delay_seconds too large
            ({"batch_delay_seconds": 15.0}, 422),
        ],
    )
    def test_request_parameters(
        self,
        test_config: FidesConfig,
        test_client: TestClient,
        payload: dict,
        expected_status: int,
    ) -> None:
        """Test that backfill endpoint validates request parameters."""
        with patch(
            "fides.api.api.v1.endpoints.admin.acquire_backfill_lock",
            return_value=True,
        ), patch(
            "fides.api.api.v1.endpoints.admin.run_backfill_manually",
        ):
            response = test_client.post(
                test_config.cli.server_url + API_PREFIX + "/admin/backfill",
                headers=test_config.user.auth_header,
                json=payload,
            )

        assert response.status_code == expected_status
        if expected_status == 202:
            data = response.json()["data"]
            assert data["config"]["batch_size"] == payload.get("batch_size", 5000)
            assert data["config"]["batch_delay_seconds"] == payload.get(
                "batch_delay_seconds", 1.0
            )

    @pytest.mark.parametrize(
        "is_running,pending_count",
        [
            (True, 50000),  # Backfill running with pending items
            (False, 0),  # Backfill complete
            (False, 100000),  # Pending items but not running
        ],
        ids=[
            "running_with_pending",
            "complete",
            "pending_but_not_running",
        ],
    )
    def test_get_status(
        self,
        test_config: FidesConfig,
        test_client: TestClient,
        is_running: bool,
        pending_count: int,
    ) -> None:
        """Test that GET backfill returns correct status."""
        with patch(
            "fides.api.api.v1.endpoints.admin.is_backfill_running",
            return_value=is_running,
        ), patch(
            "fides.api.api.v1.endpoints.admin.get_pending_is_leaf_count",
            return_value=pending_count,
        ):
            response = test_client.get(
                test_config.cli.server_url + API_PREFIX + "/admin/backfill",
                headers=test_config.user.auth_header,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is is_running
        assert data["pending_count"]["is_leaf"] == pending_count

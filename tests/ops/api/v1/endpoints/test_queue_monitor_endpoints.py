"""Tests for the Queue Monitor endpoint.

Covers:
- Task 1.3 — Property 1: SQS Mode Indicator Accuracy
- Task 1.4 — Property 2: Queue Statistics Completeness and Attribute Mapping
- Task 1.5 — Property 3: Per-Queue Error Isolation
- Task 2.3 — Unit tests for the queue monitor endpoint
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import Response
from hypothesis import given, settings
from hypothesis import strategies as st

from fides.api.schemas.queue_monitor import QueueMonitorResponse
from fides.api.tasks.broker import get_all_celery_queue_names
from fides.api.v1.endpoints.queue_monitor_endpoints import get_queue_monitor
from fides.common.urn_registry import V1_URL_PREFIX

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(use_sqs_queue: bool = True) -> SimpleNamespace:
    """Build a minimal config object matching the shape expected by queue_stats.py."""
    return SimpleNamespace(
        queue=SimpleNamespace(
            use_sqs_queue=use_sqs_queue,
            sqs_url="http://elasticmq:9324",
            aws_region="us-east-1",
            aws_access_key_id="x",
            aws_secret_access_key="x",
            sqs_queue_name_prefix="fides-",
        ),
    )


def _mock_sqs_client(responses: dict[str, dict[str, int] | Exception]) -> MagicMock:
    """Build a mock SQS client that returns configured attributes per queue URL."""
    client = MagicMock()

    def _get_queue_attributes(QueueUrl: str, **kwargs):  # noqa: N803
        for queue_name, value in responses.items():
            if queue_name in QueueUrl:
                if isinstance(value, Exception):
                    raise value
                return {
                    "Attributes": {
                        "ApproximateNumberOfMessages": str(value.get("available", 0)),
                        "ApproximateNumberOfMessagesDelayed": str(
                            value.get("delayed", 0)
                        ),
                        "ApproximateNumberOfMessagesNotVisible": str(
                            value.get("in_flight", 0)
                        ),
                    }
                }
        raise Exception(f"Queue not found: {QueueUrl}")

    client.get_queue_attributes = MagicMock(side_effect=_get_queue_attributes)
    return client


# ===========================================================================
# Task 1.3 — Property 1: SQS Mode Indicator Accuracy
# ===========================================================================


class TestSqsModeIndicatorAccuracy:
    """Property 1: For any value of use_sqs_queue, sqs_enabled in response
    matches the config exactly.

    Validates: Requirements 2.1, 2.2
    """

    @given(sqs_enabled=st.booleans())
    @settings(max_examples=100)
    def test_sqs_mode_indicator_accuracy(self, sqs_enabled: bool) -> None:
        config = _make_config(use_sqs_queue=sqs_enabled)

        with (
            patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config),
            patch("fides.api.tasks.broker.get_sqs_client") as mock_build,
        ):
            mock_build.return_value = MagicMock()
            response = get_queue_monitor()

        assert response.sqs_enabled == sqs_enabled
        if not sqs_enabled:
            assert response.queues == []


# ===========================================================================
# Task 1.4 — Property 2: Queue Statistics Completeness and Attribute Mapping
# ===========================================================================


class TestQueueStatsCompletenessAndMapping:
    """Property 2: For any queue names and SQS attribute values, response
    includes exactly one QueueStats entry per queue with correct field mapping.

    Validates: Requirements 1.2, 1.3
    """

    @given(
        queue_names=st.lists(
            st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=10,
            unique=True,
        ),
        available=st.integers(min_value=0, max_value=100_000),
        delayed=st.integers(min_value=0, max_value=100_000),
        in_flight=st.integers(min_value=0, max_value=100_000),
    )
    @settings(max_examples=100)
    def test_queue_stats_completeness_and_mapping(
        self,
        queue_names: list[str],
        available: int,
        delayed: int,
        in_flight: int,
    ) -> None:
        config = _make_config(use_sqs_queue=True)
        responses = {
            name: {"available": available, "delayed": delayed, "in_flight": in_flight}
            for name in queue_names
        }
        mock_client = _mock_sqs_client(responses)

        with (
            patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config),
            patch("fides.api.tasks.broker.get_sqs_client", return_value=mock_client),
            patch(
                "fides.api.v1.endpoints.queue_monitor_endpoints.get_all_celery_queue_names",
                return_value=queue_names,
            ),
        ):
            response = get_queue_monitor()

        assert response.sqs_enabled is True
        assert len(response.queues) == len(queue_names)

        name_to_stats = {q.queue_name: q for q in response.queues}
        assert set(name_to_stats.keys()) == set(queue_names)

        for name in queue_names:
            stats = name_to_stats[name]
            assert stats.available == available
            assert stats.delayed == delayed
            assert stats.in_flight == in_flight


# ===========================================================================
# Task 1.5 — Property 3: Per-Queue Error Isolation
# ===========================================================================


class TestPerQueueErrorIsolation:
    """Property 3: For any set of queues with a failing subset, failed queues
    return zeros, successful queues return valid data, and HTTP status is 200.

    Validates: Requirements 1.4
    """

    @given(
        queue_names=st.lists(
            st.text(min_size=1, max_size=50),
            min_size=2,
            max_size=10,
            unique=True,
        ),
        failing_indices=st.lists(st.integers(min_value=0), min_size=1),
    )
    @settings(max_examples=100)
    def test_per_queue_error_isolation(
        self,
        queue_names: list[str],
        failing_indices: list[int],
    ) -> None:
        config = _make_config(use_sqs_queue=True)
        responses: dict[str, dict[str, int] | Exception] = {}
        failing_set = {queue_names[i % len(queue_names)] for i in failing_indices}

        for name in queue_names:
            if name in failing_set:
                responses[name] = ClientError(
                    {"Error": {"Code": "AWS.SimpleQueueService.NonExistentQueue"}},
                    "GetQueueAttributes",
                )
            else:
                responses[name] = {
                    "available": 10,
                    "delayed": 5,
                    "in_flight": 2,
                }

        mock_client = _mock_sqs_client(responses)

        with (
            patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config),
            patch("fides.api.tasks.broker.get_sqs_client", return_value=mock_client),
            patch(
                "fides.api.v1.endpoints.queue_monitor_endpoints.get_all_celery_queue_names",
                return_value=queue_names,
            ),
        ):
            response = get_queue_monitor()

        assert response.sqs_enabled is True
        assert len(response.queues) == len(queue_names)

        name_to_stats = {q.queue_name: q for q in response.queues}
        for name in queue_names:
            stats = name_to_stats[name]
            if name in failing_set:
                assert stats.available == 0
                assert stats.delayed == 0
                assert stats.in_flight == 0
            else:
                assert stats.available == 10
                assert stats.delayed == 5
                assert stats.in_flight == 2


# ===========================================================================
# Task 2.3 — Unit tests for the queue monitor endpoint
# ===========================================================================


class TestQueueMonitorEndpoint:
    """Unit tests for the queue monitor endpoint behaviour."""

    def test_sqs_disabled_returns_empty(self) -> None:
        """SQS disabled → sqs_enabled=False and empty queues list."""
        config = _make_config(use_sqs_queue=False)

        with patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config):
            response = get_queue_monitor()

        assert response.sqs_enabled is False
        assert response.queues == []

    def test_sqs_enabled_with_valid_credentials(self) -> None:
        """SQS enabled with valid credentials → all queues with three counts."""
        queue_names = ["fides", "fidesops.messaging"]
        config = _make_config(use_sqs_queue=True)
        responses = {
            "fides": {"available": 3, "delayed": 1, "in_flight": 0},
            "fidesops.messaging": {"available": 0, "delayed": 0, "in_flight": 5},
        }
        mock_client = _mock_sqs_client(responses)

        with (
            patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config),
            patch("fides.api.tasks.broker.get_sqs_client", return_value=mock_client),
            patch(
                "fides.api.v1.endpoints.queue_monitor_endpoints.get_all_celery_queue_names",
                return_value=queue_names,
            ),
        ):
            response = get_queue_monitor()

        assert response.sqs_enabled is True
        assert len(response.queues) == 2

        name_to_stats = {q.queue_name: q for q in response.queues}
        assert name_to_stats["fides"].available == 3
        assert name_to_stats["fides"].delayed == 1
        assert name_to_stats["fides"].in_flight == 0
        assert name_to_stats["fidesops.messaging"].available == 0
        assert name_to_stats["fidesops.messaging"].delayed == 0
        assert name_to_stats["fidesops.messaging"].in_flight == 5

    def test_sqs_auth_error_returns_503(self) -> None:
        """SQS auth error → HTTP 503 with empty body."""
        config = _make_config(use_sqs_queue=True)
        mock_client = MagicMock()
        mock_client.get_queue_attributes = MagicMock(side_effect=NoCredentialsError())

        with (
            patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config),
            patch("fides.api.tasks.broker.get_sqs_client", return_value=mock_client),
            patch(
                "fides.api.v1.endpoints.queue_monitor_endpoints.get_all_celery_queue_names",
                return_value=["fides"],
            ),
        ):
            response = get_queue_monitor()

        assert isinstance(response, Response)
        assert response.status_code == 503

    def test_single_queue_non_auth_failure_returns_zeros(self) -> None:
        """Single queue non-auth failure → zeros for that queue, valid for others."""
        queue_names = ["fides", "fidesops.messaging"]
        config = _make_config(use_sqs_queue=True)
        responses = {
            "fides": ClientError(
                {"Error": {"Code": "AWS.SimpleQueueService.NonExistentQueue"}},
                "GetQueueAttributes",
            ),
            "fidesops.messaging": {"available": 7, "delayed": 2, "in_flight": 1},
        }
        mock_client = _mock_sqs_client(responses)

        with (
            patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config),
            patch("fides.api.tasks.broker.get_sqs_client", return_value=mock_client),
            patch(
                "fides.api.v1.endpoints.queue_monitor_endpoints.get_all_celery_queue_names",
                return_value=queue_names,
            ),
        ):
            response = get_queue_monitor()

        assert response.sqs_enabled is True
        name_to_stats = {q.queue_name: q for q in response.queues}
        assert name_to_stats["fides"].available == 0
        assert name_to_stats["fides"].delayed == 0
        assert name_to_stats["fides"].in_flight == 0
        assert name_to_stats["fidesops.messaging"].available == 7
        assert name_to_stats["fidesops.messaging"].delayed == 2
        assert name_to_stats["fidesops.messaging"].in_flight == 1

    def test_all_queues_zero_counts_still_present(self) -> None:
        """All queues with zero counts are still present in the response."""
        queue_names = ["fides", "fidesops.messaging"]
        config = _make_config(use_sqs_queue=True)
        responses = {
            name: {"available": 0, "delayed": 0, "in_flight": 0} for name in queue_names
        }
        mock_client = _mock_sqs_client(responses)

        with (
            patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config),
            patch("fides.api.tasks.broker.get_sqs_client", return_value=mock_client),
            patch(
                "fides.api.v1.endpoints.queue_monitor_endpoints.get_all_celery_queue_names",
                return_value=queue_names,
            ),
        ):
            response = get_queue_monitor()

        assert response.sqs_enabled is True
        assert len(response.queues) == 2
        for q in response.queues:
            assert q.available == 0
            assert q.delayed == 0
            assert q.in_flight == 0

    def test_queue_name_format_is_logical_name(self) -> None:
        """Response contains logical Celery queue names, not SQS URLs."""
        queue_names = ["fides", "fidesops.messaging"]
        config = _make_config(use_sqs_queue=True)
        responses = {
            name: {"available": 1, "delayed": 0, "in_flight": 0} for name in queue_names
        }
        mock_client = _mock_sqs_client(responses)

        with (
            patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config),
            patch("fides.api.tasks.broker.get_sqs_client", return_value=mock_client),
            patch(
                "fides.api.v1.endpoints.queue_monitor_endpoints.get_all_celery_queue_names",
                return_value=queue_names,
            ),
        ):
            response = get_queue_monitor()

        names = {q.queue_name for q in response.queues}
        assert names == set(queue_names)
        for q in response.queues:
            assert not q.queue_name.startswith("http")
            assert "sqs" not in q.queue_name.lower()


# ===========================================================================
# Integration-style tests via api_client
# ===========================================================================


class TestQueueMonitorEndpointHTTP:
    """HTTP-level tests for the queue monitor endpoint."""

    @pytest.fixture(scope="function")
    def url(self) -> str:
        return f"{V1_URL_PREFIX}/queue-monitor"

    def test_any_authenticated_user_returns_200_when_sqs_disabled(
        self,
        url,
        generate_auth_header,
        api_client,
    ) -> None:
        config = _make_config(use_sqs_queue=False)
        auth_header = generate_auth_header(scopes=[])

        with patch("fides.api.v1.endpoints.queue_monitor_endpoints.CONFIG", config):
            response = api_client.get(url, headers=auth_header)

        assert response.status_code == 200
        data = response.json()
        assert data["sqs_enabled"] is False
        assert data["queues"] == []

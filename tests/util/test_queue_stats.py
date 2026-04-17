"""Tests for the QueueStatsProvider (``src/fides/api/util/queue_stats.py``).

Covers:
- Task 5.1 — Property 5: Queue Count Non-Negativity
- Task 5.2 — Property 10: Queue Stats Completeness
- Task 5.3 — Unit tests for SQSQueueStatsProvider
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st

from fides.api.tasks.broker import get_all_celery_queue_names
from fides.api.util.queue_stats import (
    RedisQueueStatsProvider,
    SQSQueueStatsProvider,
    get_queue_stats_provider,
)


# ---------------------------------------------------------------------------
# Helpers — lightweight config stubs
# ---------------------------------------------------------------------------


def _make_config(
    use_sqs_queue: bool = True,
    sqs_url: str | None = "http://elasticmq:9324",
    aws_region: str = "us-east-1",
    aws_access_key_id: str | None = "x",
    aws_secret_access_key: str | None = "x",
    sqs_queue_name_prefix: str = "fides-",
) -> SimpleNamespace:
    """Build a minimal config object matching the shape expected by queue_stats.py."""
    return SimpleNamespace(
        queue=SimpleNamespace(
            use_sqs_queue=use_sqs_queue,
            sqs_url=sqs_url,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            sqs_queue_name_prefix=sqs_queue_name_prefix,
        ),
    )


def _mock_sqs_client(responses: dict[str, int | Exception]) -> MagicMock:
    """Build a mock SQS client that returns configured counts per queue URL.

    ``responses`` maps queue names to either an int count or an Exception to raise.
    """
    client = MagicMock()

    def _get_queue_attributes(QueueUrl: str, **kwargs):  # noqa: N803
        # Extract the Celery queue name from the URL (last segment after prefix).
        for queue_name, value in responses.items():
            if queue_name in QueueUrl:
                if isinstance(value, Exception):
                    raise value
                return {
                    "Attributes": {
                        "ApproximateNumberOfMessages": str(value),
                    }
                }
        # Default: queue not found
        raise Exception(f"Queue not found: {QueueUrl}")

    client.get_queue_attributes = MagicMock(side_effect=_get_queue_attributes)
    return client


# ===========================================================================
# Task 5.1 — Property 5: Queue Count Non-Negativity
# ===========================================================================


class TestQueueCountNonNegativityProperty:
    """Property 5: For any mocked SQS or Redis response (including error
    responses), ``get_queue_counts()`` returns a ``Dict[str, int]`` where
    every value is ``>= 0``.

    Validates: Requirements 4.6
    """

    @given(
        counts=st.fixed_dictionaries(
            {
                name: st.integers(min_value=0, max_value=100_000)
                for name in get_all_celery_queue_names()
            }
        ),
    )
    @settings(max_examples=50)
    def test_sqs_counts_are_non_negative(self, counts: dict[str, int]) -> None:
        """SQS provider always returns non-negative counts."""
        config = _make_config()
        mock_client = _mock_sqs_client(counts)

        provider = SQSQueueStatsProvider.__new__(SQSQueueStatsProvider)
        provider._config = config
        provider._sqs_client = mock_client

        result = provider.get_queue_counts()
        for queue_name, count in result.items():
            assert isinstance(count, int)
            assert count >= 0, f"Queue {queue_name!r} has negative count: {count}"

    @given(
        counts=st.fixed_dictionaries(
            {
                name: st.integers(min_value=0, max_value=100_000)
                for name in get_all_celery_queue_names()
            }
        ),
    )
    @settings(max_examples=50)
    def test_redis_counts_are_non_negative(self, counts: dict[str, int]) -> None:
        """Redis provider always returns non-negative counts."""
        mock_redis = MagicMock()
        mock_redis.llen = MagicMock(side_effect=lambda q: counts.get(q, 0))

        provider = RedisQueueStatsProvider(mock_redis)
        result = provider.get_queue_counts()
        for queue_name, count in result.items():
            assert isinstance(count, int)
            assert count >= 0, f"Queue {queue_name!r} has negative count: {count}"

    def test_sqs_error_responses_return_zero(self) -> None:
        """When SQS returns an error for a queue, count defaults to 0 (non-negative)."""
        all_queues = get_all_celery_queue_names()
        responses: dict[str, int | Exception] = {
            name: Exception("simulated error") for name in all_queues
        }
        config = _make_config()
        mock_client = _mock_sqs_client(responses)

        provider = SQSQueueStatsProvider.__new__(SQSQueueStatsProvider)
        provider._config = config
        provider._sqs_client = mock_client

        result = provider.get_queue_counts()
        for queue_name, count in result.items():
            assert count >= 0

    def test_redis_error_responses_return_zero(self) -> None:
        """When Redis raises for a queue, count defaults to 0 (non-negative)."""
        mock_redis = MagicMock()
        mock_redis.llen = MagicMock(side_effect=Exception("connection lost"))

        provider = RedisQueueStatsProvider(mock_redis)
        result = provider.get_queue_counts()
        for queue_name, count in result.items():
            assert count >= 0


# ===========================================================================
# Task 5.2 — Property 10: Queue Stats Completeness
# ===========================================================================


class TestQueueStatsCompletenessProperty:
    """Property 10: For any set of known Celery queue names,
    ``get_queue_counts()`` returns a dict with exactly one entry per queue
    name, regardless of which queues succeed or fail.

    Validates: Requirements 4.4
    """

    @given(
        failing_queues=st.lists(
            st.sampled_from(get_all_celery_queue_names()),
            unique=True,
        ),
    )
    @settings(max_examples=50)
    def test_sqs_completeness_with_partial_failures(
        self, failing_queues: list[str]
    ) -> None:
        """SQS provider returns an entry for every queue even when some fail."""
        all_queues = get_all_celery_queue_names()
        responses: dict[str, int | Exception] = {}
        for name in all_queues:
            if name in failing_queues:
                responses[name] = Exception("simulated error")
            else:
                responses[name] = 42

        config = _make_config()
        mock_client = _mock_sqs_client(responses)

        provider = SQSQueueStatsProvider.__new__(SQSQueueStatsProvider)
        provider._config = config
        provider._sqs_client = mock_client

        result = provider.get_queue_counts()
        assert set(result.keys()) == set(all_queues), (
            f"Missing queues: {set(all_queues) - set(result.keys())}"
        )

    @given(
        failing_queues=st.lists(
            st.sampled_from(get_all_celery_queue_names()),
            unique=True,
        ),
    )
    @settings(max_examples=50)
    def test_redis_completeness_with_partial_failures(
        self, failing_queues: list[str]
    ) -> None:
        """Redis provider returns an entry for every queue even when some fail."""
        all_queues = get_all_celery_queue_names()

        def _llen(queue_name: str) -> int:
            if queue_name in failing_queues:
                raise Exception("simulated error")
            return 10

        mock_redis = MagicMock()
        mock_redis.llen = MagicMock(side_effect=_llen)

        provider = RedisQueueStatsProvider(mock_redis)
        result = provider.get_queue_counts()
        assert set(result.keys()) == set(all_queues), (
            f"Missing queues: {set(all_queues) - set(result.keys())}"
        )


# ===========================================================================
# Task 5.3 — Unit tests for SQSQueueStatsProvider
# ===========================================================================


class TestSQSQueueStatsProvider:
    """Unit tests for ``SQSQueueStatsProvider``."""

    def test_get_queue_attributes_called_with_correct_attribute_names(self) -> None:
        """``get_queue_attributes`` is called with ``ApproximateNumberOfMessages``."""
        all_queues = get_all_celery_queue_names()
        config = _make_config()
        mock_client = MagicMock()
        mock_client.get_queue_attributes = MagicMock(
            return_value={
                "Attributes": {"ApproximateNumberOfMessages": "5"},
            }
        )

        provider = SQSQueueStatsProvider.__new__(SQSQueueStatsProvider)
        provider._config = config
        provider._sqs_client = mock_client

        provider.get_queue_counts()

        assert mock_client.get_queue_attributes.call_count == len(all_queues)
        for call in mock_client.get_queue_attributes.call_args_list:
            assert call.kwargs["AttributeNames"] == [
                "ApproximateNumberOfMessages"
            ]

    def test_per_queue_error_returns_zero_and_logs_warning(self) -> None:
        """When a single queue fails, its count is 0 and a warning is logged.

        Requirement 4.5, 8.1
        """
        all_queues = get_all_celery_queue_names()
        failing_queue = all_queues[0]

        responses: dict[str, int | Exception] = {
            name: 10 for name in all_queues
        }
        responses[failing_queue] = Exception("queue does not exist")

        config = _make_config()
        mock_client = _mock_sqs_client(responses)

        provider = SQSQueueStatsProvider.__new__(SQSQueueStatsProvider)
        provider._config = config
        provider._sqs_client = mock_client

        with patch("fides.api.util.queue_stats.logger") as mock_logger:
            result = provider.get_queue_counts()

        # Failing queue returns 0
        assert result[failing_queue] == 0

        # Other queues return the expected count
        for name in all_queues[1:]:
            assert result[name] == 10

        # Warning was logged
        mock_logger.warning.assert_called()

    def test_auth_failure_returns_empty_dict_and_logs_critical(self) -> None:
        """When AWS auth fails, return ``{}`` and log critical.

        Requirement 8.2
        """
        from botocore.exceptions import NoCredentialsError

        config = _make_config()
        mock_client = MagicMock()
        mock_client.get_queue_attributes = MagicMock(
            side_effect=NoCredentialsError()
        )

        provider = SQSQueueStatsProvider.__new__(SQSQueueStatsProvider)
        provider._config = config
        provider._sqs_client = mock_client

        with patch("fides.api.util.queue_stats.logger") as mock_logger:
            result = provider.get_queue_counts()

        assert result == {}
        mock_logger.critical.assert_called()

    def test_successful_counts_returned(self) -> None:
        """Happy path: all queues return valid counts."""
        all_queues = get_all_celery_queue_names()
        responses = {name: idx * 3 for idx, name in enumerate(all_queues)}

        config = _make_config()
        mock_client = _mock_sqs_client(responses)

        provider = SQSQueueStatsProvider.__new__(SQSQueueStatsProvider)
        provider._config = config
        provider._sqs_client = mock_client

        result = provider.get_queue_counts()
        for name, expected in responses.items():
            assert result[name] == expected


class TestGetQueueStatsProviderFactory:
    """Unit tests for the ``get_queue_stats_provider`` factory."""

    def test_returns_sqs_provider_when_flag_enabled(self) -> None:
        config = _make_config(use_sqs_queue=True)
        with patch(
            "fides.api.tasks.broker.get_sqs_client"
        ) as mock_build:
            mock_build.return_value = MagicMock()
            provider = get_queue_stats_provider(config)
        assert isinstance(provider, SQSQueueStatsProvider)

    def test_returns_redis_provider_when_flag_disabled(self) -> None:
        config = _make_config(use_sqs_queue=False)
        # ``get_queue_stats_provider`` does a local import of ``get_cache``
        # from ``fides.api.util.cache``; patch at the source module so the
        # local import resolves to the mock.
        with patch("fides.api.util.cache.get_cache") as mock_get_cache:
            mock_get_cache.return_value = MagicMock()
            provider = get_queue_stats_provider(config)
        assert isinstance(provider, RedisQueueStatsProvider)


# ===========================================================================
# Task 6.1 — Unit tests for updated ``cache.get_queue_counts`` delegation
# ===========================================================================


class TestCacheGetQueueCountsDelegation:
    """Unit tests asserting ``cache.get_queue_counts`` delegates to the correct
    ``QueueStatsProvider`` based on the ``use_sqs_queue`` feature flag.

    Validates: Requirements 4.2
    """

    def test_delegates_to_sqs_provider_when_flag_enabled(self) -> None:
        """``get_queue_counts`` uses ``SQSQueueStatsProvider`` when
        ``use_sqs_queue=True``.
        """
        from fides.api.util import cache as cache_module

        expected = {"fides.dsr": 7, "fidesops.messaging": 0}
        sqs_provider = MagicMock(spec=SQSQueueStatsProvider)
        sqs_provider.get_queue_counts = MagicMock(return_value=expected)

        sqs_config = _make_config(use_sqs_queue=True)

        with patch.object(cache_module, "CONFIG", sqs_config), patch(
            "fides.api.util.queue_stats.get_queue_stats_provider",
            return_value=sqs_provider,
        ) as mock_factory:
            result = cache_module.get_queue_counts()

        mock_factory.assert_called_once_with(sqs_config)
        sqs_provider.get_queue_counts.assert_called_once_with()
        assert result == expected

    def test_delegates_to_redis_provider_when_flag_disabled(self) -> None:
        """``get_queue_counts`` uses ``RedisQueueStatsProvider`` when
        ``use_sqs_queue=False``.
        """
        from fides.api.util import cache as cache_module

        expected = {name: 3 for name in get_all_celery_queue_names()}
        redis_provider = MagicMock(spec=RedisQueueStatsProvider)
        redis_provider.get_queue_counts = MagicMock(return_value=expected)

        redis_config = _make_config(use_sqs_queue=False)

        with patch.object(cache_module, "CONFIG", redis_config), patch(
            "fides.api.util.queue_stats.get_queue_stats_provider",
            return_value=redis_provider,
        ) as mock_factory:
            result = cache_module.get_queue_counts()

        mock_factory.assert_called_once_with(redis_config)
        redis_provider.get_queue_counts.assert_called_once_with()
        assert result == expected

    def test_factory_selects_sqs_provider_when_flag_enabled(self) -> None:
        """End-to-end: with the real factory, ``get_queue_counts`` dispatches
        through ``SQSQueueStatsProvider`` when ``use_sqs_queue=True``.
        """
        from fides.api.util import cache as cache_module

        sqs_config = _make_config(use_sqs_queue=True)

        with patch.object(cache_module, "CONFIG", sqs_config), patch(
            "fides.api.tasks.broker.get_sqs_client"
        ) as mock_build_sqs, patch(
            "fides.api.util.queue_stats.SQSQueueStatsProvider.get_queue_counts"
        ) as mock_sqs_counts, patch(
            "fides.api.util.queue_stats.RedisQueueStatsProvider.get_queue_counts"
        ) as mock_redis_counts:
            mock_build_sqs.return_value = MagicMock()
            mock_sqs_counts.return_value = {"fides.dsr": 1}
            mock_redis_counts.return_value = {"fides.dsr": 999}

            result = cache_module.get_queue_counts()

        assert result == {"fides.dsr": 1}
        mock_sqs_counts.assert_called_once_with()
        mock_redis_counts.assert_not_called()

    def test_factory_selects_redis_provider_when_flag_disabled(self) -> None:
        """End-to-end: with the real factory, ``get_queue_counts`` dispatches
        through ``RedisQueueStatsProvider`` when ``use_sqs_queue=False``.
        """
        from fides.api.util import cache as cache_module

        redis_config = _make_config(use_sqs_queue=False)

        # ``queue_stats.get_queue_stats_provider`` does a local import of
        # ``get_cache`` from ``fides.api.util.cache``; patch it at the source
        # module so the local import resolves to the mock.
        with patch.object(cache_module, "CONFIG", redis_config), patch(
            "fides.api.util.cache.get_cache"
        ) as mock_get_cache, patch(
            "fides.api.util.queue_stats.RedisQueueStatsProvider.get_queue_counts"
        ) as mock_redis_counts, patch(
            "fides.api.util.queue_stats.SQSQueueStatsProvider.get_queue_counts"
        ) as mock_sqs_counts:
            mock_get_cache.return_value = MagicMock()
            mock_redis_counts.return_value = {"fides.dsr": 4}
            mock_sqs_counts.return_value = {"fides.dsr": 999}

            result = cache_module.get_queue_counts()

        assert result == {"fides.dsr": 4}
        mock_redis_counts.assert_called_once_with()
        mock_sqs_counts.assert_not_called()

    def test_returns_empty_dict_and_logs_critical_on_unexpected_error(
        self,
    ) -> None:
        """If the provider factory raises, ``get_queue_counts`` returns ``{}``
        and logs at critical level — matching the legacy behaviour preserved
        from the Redis-only implementation.
        """
        from fides.api.util import cache as cache_module

        with patch.object(cache_module, "CONFIG", _make_config()), patch(
            "fides.api.util.queue_stats.get_queue_stats_provider",
            side_effect=RuntimeError("provider blew up"),
        ), patch.object(cache_module, "logger") as mock_logger:
            result = cache_module.get_queue_counts()

        assert result == {}
        mock_logger.critical.assert_called()

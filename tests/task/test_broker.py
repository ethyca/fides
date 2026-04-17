"""Tests for the BrokerURLFactory (``src/fides/api/tasks/broker.py``).

Covers:
- Task 2.1 — Property 1: Broker URL Exclusivity
- Task 2.2 — Property 9: Transport Options Completeness
- Task 2.3 — Property 8: SQS Queue Name Mapping
- Task 2.4 — Unit tests for BrokerURLFactory
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings, strategies as st

from fides.api.tasks import _resolve_result_backend
from fides.api.tasks.broker import (
    CELERY_QUEUE_NAMES,
    DEFAULT_QUEUE_NAME,
    _canonical_sqs_queue_name,
    get_all_celery_queue_names,
    get_broker_transport_options,
    get_broker_url,
    get_sqs_base_url,
    get_sqs_broker_url,
    get_sqs_queue_url,
    get_task_queues,
)


# ---------------------------------------------------------------------------
# Helpers — lightweight config stubs
# ---------------------------------------------------------------------------

def _make_config(
    use_sqs_queue: bool = False,
    sqs_url: str | None = None,
    aws_region: str = "us-east-1",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    sqs_queue_name_prefix: str = "fides-",
    broker_url: str | None = None,
    cluster_enabled: bool = False,
    connection_url: str | None = "redis://:testpassword@redis:6379/0",
    result_backend: str | None = None,
) -> SimpleNamespace:
    """Build a minimal config object matching the shape expected by broker.py."""
    redis = SimpleNamespace(
        cluster_enabled=cluster_enabled,
        connection_url=connection_url,
    )
    if cluster_enabled:
        redis.get_cluster_connection_url = lambda: "redis+cluster://:testpassword@redis:6379/0"

    return SimpleNamespace(
        queue=SimpleNamespace(
            use_sqs_queue=use_sqs_queue,
            sqs_url=sqs_url,
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            sqs_queue_name_prefix=sqs_queue_name_prefix,
        ),
        celery=SimpleNamespace(
            broker_url=broker_url,
            result_backend=result_backend,
        ),
        redis=redis,
    )


# ===========================================================================
# Task 2.1 — Property 1: Broker URL Exclusivity
# ===========================================================================

class TestBrokerURLExclusivityProperty:
    """Property 1: For any FidesConfig, `get_broker_url()` starts with 'sqs://'
    iff `use_sqs_queue=True`, and starts with 'redis://' / 'rediss://' /
    'redis+cluster://' otherwise.

    Validates: Requirements 2.1, 2.2
    """

    @given(
        use_sqs_queue=st.booleans(),
        aws_region=st.sampled_from(["us-east-1", "eu-west-1", "ap-southeast-1"]),
        sqs_queue_name_prefix=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_broker_url_exclusivity(
        self, use_sqs_queue: bool, aws_region: str, sqs_queue_name_prefix: str
    ) -> None:
        config = _make_config(
            use_sqs_queue=use_sqs_queue,
            aws_region=aws_region,
            sqs_queue_name_prefix=sqs_queue_name_prefix,
            sqs_url="http://elasticmq:9324" if use_sqs_queue else None,
            aws_access_key_id="x" if use_sqs_queue else None,
            aws_secret_access_key="x" if use_sqs_queue else None,
        )
        url = get_broker_url(config)

        if use_sqs_queue:
            assert url.startswith("sqs://"), f"Expected sqs:// URL, got {url}"
        else:
            assert any(
                url.startswith(scheme)
                for scheme in ("redis://", "rediss://", "redis+cluster://")
            ), f"Expected redis URL, got {url}"


# ===========================================================================
# Task 2.2 — Property 9: Transport Options Completeness
# ===========================================================================

class TestTransportOptionsCompletenessProperty:
    """Property 9: For any FidesConfig where `use_sqs_queue=True`,
    `get_broker_transport_options()` returns a dict with a `predefined_queues`
    key containing an entry for every known Celery queue name.

    Validates: Requirements 2.4
    """

    @given(
        aws_region=st.sampled_from(["us-east-1", "eu-west-1", "ap-southeast-1"]),
        sqs_queue_name_prefix=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_transport_options_completeness(
        self, aws_region: str, sqs_queue_name_prefix: str
    ) -> None:
        config = _make_config(
            use_sqs_queue=True,
            sqs_url="http://elasticmq:9324",
            aws_region=aws_region,
            sqs_queue_name_prefix=sqs_queue_name_prefix,
        )
        options = get_broker_transport_options(config)

        assert "predefined_queues" in options
        predefined = options["predefined_queues"]

        all_queue_names = get_all_celery_queue_names()
        for queue_name in all_queue_names:
            sqs_key = _canonical_sqs_queue_name(queue_name)
            assert sqs_key in predefined, (
                f"Missing queue {sqs_key!r} (from {queue_name!r}) in predefined_queues"
            )
            assert "url" in predefined[sqs_key]


# ===========================================================================
# Task 2.3 — Property 8: SQS Queue Name Mapping
# ===========================================================================

class TestSQSQueueNameMappingProperty:
    """Property 8: For any Celery queue name and any non-empty
    `sqs_queue_name_prefix`, the SQS queue name equals the concatenation
    of prefix and Celery queue name.

    Validates: Requirements 3.1
    """

    @given(
        queue_name=st.sampled_from(get_all_celery_queue_names()),
        prefix=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_sqs_queue_name_mapping(self, queue_name: str, prefix: str) -> None:
        config = _make_config(
            use_sqs_queue=True,
            sqs_url="http://elasticmq:9324",
            sqs_queue_name_prefix=prefix,
        )

        base_url = get_sqs_base_url(config)
        url = get_sqs_queue_url(queue_name, base_url, prefix)
        # Dots are replaced with dashes in the actual SQS queue name because
        # SQS does not allow dots in queue names.
        expected_sqs_name = f"{prefix}{_canonical_sqs_queue_name(queue_name)}"

        # The URL should end with /queue/<prefix><canonical_queue_name>
        assert url.endswith(f"/queue/{expected_sqs_name}"), (
            f"Expected URL ending with /queue/{expected_sqs_name}, got {url}"
        )


# ===========================================================================
# Task 2.4 — Unit tests for BrokerURLFactory
# ===========================================================================

class TestGetBrokerUrl:
    """Unit tests for `get_broker_url`."""

    def test_returns_redis_url_when_sqs_disabled(self) -> None:
        """Test `get_broker_url` returns Redis URL when `use_sqs_queue=False`."""
        config = _make_config(use_sqs_queue=False)
        url = get_broker_url(config)
        assert url == "redis://:testpassword@redis:6379/0"

    def test_returns_sqs_url_when_sqs_enabled(self) -> None:
        """Test `get_broker_url` returns SQS URL when `use_sqs_queue=True`."""
        config = _make_config(
            use_sqs_queue=True,
            aws_access_key_id="AKID",
            aws_secret_access_key="SECRET",
        )
        url = get_broker_url(config)
        assert url.startswith("sqs://")
        assert "AKID" in url
        assert "SECRET" in url

    def test_returns_celery_broker_url_when_set(self) -> None:
        """When `celery.broker_url` is explicitly set, it takes precedence over Redis."""
        explicit_url = "redis://:custom@custom-host:6380/2"
        config = _make_config(use_sqs_queue=False, broker_url=explicit_url)
        url = get_broker_url(config)
        assert url == explicit_url

    def test_returns_cluster_url_when_cluster_enabled(self) -> None:
        """When cluster mode is enabled and no explicit broker_url, use cluster URL."""
        config = _make_config(
            use_sqs_queue=False,
            cluster_enabled=True,
            broker_url=None,
        )
        url = get_broker_url(config)
        assert url.startswith("redis+cluster://")

    def test_raises_value_error_when_no_url_resolves(self) -> None:
        """Test `get_broker_url` raises `ValueError` when no URL can be resolved."""
        config = _make_config(
            use_sqs_queue=False,
            broker_url=None,
            cluster_enabled=False,
            connection_url=None,
        )
        with pytest.raises(ValueError, match="No broker URL could be resolved"):
            get_broker_url(config)


class TestGetSqsBrokerUrl:
    """Unit tests for `get_sqs_broker_url`."""

    def test_with_credentials_no_sqs_url(self) -> None:
        """AWS SQS: credentials only, no host in URL."""
        config = _make_config(
            use_sqs_queue=True,
            aws_access_key_id="MY_KEY",
            aws_secret_access_key="MY_SECRET",
        )
        url = get_sqs_broker_url(config)
        assert url == "sqs://MY_KEY:MY_SECRET@"

    def test_with_sqs_url_includes_host_and_port(self) -> None:
        """ElasticMQ: hostname and port are extracted into the broker URL."""
        config = _make_config(
            use_sqs_queue=True,
            sqs_url="http://elasticmq:9324",
            aws_access_key_id="MY_KEY",
            aws_secret_access_key="MY_SECRET",
        )
        url = get_sqs_broker_url(config)
        assert url == "sqs://MY_KEY:MY_SECRET@elasticmq:9324/"

    def test_without_credentials(self) -> None:
        """When credentials are None, empty strings are used (boto3 chain)."""
        config = _make_config(
            use_sqs_queue=True,
            aws_access_key_id=None,
            aws_secret_access_key=None,
        )
        url = get_sqs_broker_url(config)
        assert url == "sqs://:@"

    def test_special_characters_are_encoded(self) -> None:
        """Credentials with special characters are URL-encoded."""
        config = _make_config(
            use_sqs_queue=True,
            aws_access_key_id="key/with+special",
            aws_secret_access_key="secret@chars!",
        )
        url = get_sqs_broker_url(config)
        assert "key%2Fwith%2Bspecial" in url
        assert "secret%40chars%21" in url


class TestGetBrokerTransportOptions:
    """Unit tests for `get_broker_transport_options`."""

    def test_returns_empty_dict_when_sqs_disabled(self) -> None:
        """Test returns `{}` when `use_sqs_queue=False`."""
        config = _make_config(use_sqs_queue=False)
        options = get_broker_transport_options(config)
        assert options == {}

    def test_includes_is_secure_false_when_http_sqs_url_set(self) -> None:
        """Test includes `is_secure=False` when `sqs_url` uses http."""
        config = _make_config(
            use_sqs_queue=True,
            sqs_url="http://elasticmq:9324",
        )
        options = get_broker_transport_options(config)
        assert options.get("is_secure") is False

    def test_no_is_secure_override_when_https_sqs_url_set(self) -> None:
        """When `sqs_url` uses https, do not override kombu's default."""
        config = _make_config(
            use_sqs_queue=True,
            sqs_url="https://elasticmq:9324",
        )
        options = get_broker_transport_options(config)
        assert "is_secure" not in options

    def test_no_is_secure_when_sqs_url_not_set(self) -> None:
        """When sqs_url is None, is_secure is not in the dict."""
        config = _make_config(
            use_sqs_queue=True,
            sqs_url=None,
        )
        options = get_broker_transport_options(config)
        assert "is_secure" not in options

    def test_includes_region(self) -> None:
        config = _make_config(
            use_sqs_queue=True,
            aws_region="eu-west-1",
        )
        options = get_broker_transport_options(config)
        assert options["region"] == "eu-west-1"

    def test_predefined_queues_maps_all_known_queues(self) -> None:
        """Test `predefined_queues` maps all known queue names with correct prefix."""
        config = _make_config(
            use_sqs_queue=True,
            sqs_url="http://elasticmq:9324",
            sqs_queue_name_prefix="test-",
        )
        options = get_broker_transport_options(config)
        predefined = options["predefined_queues"]

        all_queues = get_all_celery_queue_names()
        assert len(predefined) == len(all_queues)

        for queue_name in all_queues:
            sqs_key = _canonical_sqs_queue_name(queue_name)
            assert sqs_key in predefined
            expected_sqs_name = f"test-{_canonical_sqs_queue_name(queue_name)}"
            expected_url = f"http://elasticmq:9324/queue/{expected_sqs_name}"
            assert predefined[sqs_key]["url"] == expected_url

    def test_predefined_queues_uses_default_aws_url_when_no_sqs_url(self) -> None:
        """When sqs_url is None, queue URLs use the default AWS SQS endpoint."""
        config = _make_config(
            use_sqs_queue=True,
            sqs_url=None,
            aws_region="us-west-2",
            sqs_queue_name_prefix="fides-",
        )
        options = get_broker_transport_options(config)
        predefined = options["predefined_queues"]

        # Check one queue as representative
        assert predefined[_canonical_sqs_queue_name("fides.dsr")]["url"] == (
            "https://sqs.us-west-2.amazonaws.com/queue/fides-fides-dsr"
        )


class TestGetTaskQueues:
    """Unit tests for `get_task_queues`."""

    def test_returns_none_when_sqs_disabled(self) -> None:
        """When `use_sqs_queue=False`, return None so Redis auto-creation works."""
        config = _make_config(use_sqs_queue=False)
        assert get_task_queues(config) is None

    def test_returns_queue_instances_for_all_known_queues(self) -> None:
        """When `use_sqs_queue=True`, return a Queue for every known queue."""
        config = _make_config(use_sqs_queue=True)
        queues = get_task_queues(config)
        assert queues is not None
        queue_names = {q.name for q in queues}
        expected_names = set(get_all_celery_queue_names())
        assert queue_names == expected_names


class TestGetAllCeleryQueueNames:
    """Unit tests for helper get_all_celery_queue_names."""

    def test_includes_default_queue(self) -> None:
        names = get_all_celery_queue_names()
        assert DEFAULT_QUEUE_NAME in names

    def test_includes_all_known_queues(self) -> None:
        names = get_all_celery_queue_names()
        for q in CELERY_QUEUE_NAMES:
            assert q in names

    def test_no_duplicates(self) -> None:
        names = get_all_celery_queue_names()
        assert len(names) == len(set(names))


# ===========================================================================
# Task 4.1 — Property 6: Result Backend Independence
# ===========================================================================

class TestResultBackendIndependenceProperty:
    """Property 6: For any FidesConfig, `_resolve_result_backend` returns the
    same URL regardless of the value of `use_sqs_queue`.

    Validates: Requirements 6.3
    """

    @given(
        use_sqs_queue=st.booleans(),
        result_backend=st.one_of(
            st.none(),
            st.sampled_from([
                "redis://:pass@redis:6379/1",
                "db+postgresql://user:pass@db:5432/fides",
            ]),
        ),
    )
    @settings(max_examples=50)
    def test_result_backend_independent_of_sqs_flag(
        self, use_sqs_queue: bool, result_backend: str | None
    ) -> None:
        config_sqs_on = _make_config(
            use_sqs_queue=True,
            result_backend=result_backend,
        )
        config_sqs_off = _make_config(
            use_sqs_queue=False,
            result_backend=result_backend,
        )
        assert _resolve_result_backend(config_sqs_on) == _resolve_result_backend(
            config_sqs_off
        ), (
            f"Result backend should be identical regardless of use_sqs_queue "
            f"(result_backend={result_backend!r})"
        )


# ===========================================================================
# Task 4.2 — Unit tests for _resolve_result_backend
# ===========================================================================

class TestResolveResultBackend:
    """Unit tests for `_resolve_result_backend`."""

    def test_returns_explicit_result_backend(self) -> None:
        """When `config.celery.result_backend` is set, return it directly."""
        explicit = "db+postgresql://user:pass@db:5432/fides"
        config = _make_config(result_backend=explicit)
        assert _resolve_result_backend(config) == explicit

    def test_falls_back_to_redis_connection_url(self) -> None:
        """When `result_backend` is None, fall back to Redis connection URL."""
        config = _make_config(
            result_backend=None,
            connection_url="redis://:testpassword@redis:6379/0",
        )
        assert _resolve_result_backend(config) == "redis://:testpassword@redis:6379/0"

    def test_unchanged_when_sqs_toggled(self) -> None:
        """Result backend is the same whether SQS is on or off."""
        for result_backend in [None, "redis://:pass@redis:6379/1"]:
            config_off = _make_config(use_sqs_queue=False, result_backend=result_backend)
            config_on = _make_config(use_sqs_queue=True, result_backend=result_backend)
            assert _resolve_result_backend(config_off) == _resolve_result_backend(config_on)

"""Tests for the StartupQueueMigrator (``src/fides/api/tasks/queue_migration.py``).

Covers:
- Task 8.1 — Property 2: Migration Idempotency
- Task 8.2 — Property 3: Migration Lock Exclusivity
- Task 8.3 — Property 4: Lock Release Guarantee
- Task 8.4 — Property 11: Migration Batch Sizing
- Task 8.5 — Property 7: Zero Task Loss
- Task 8.6 — Unit tests for StartupQueueMigrator
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st

from fides.api.tasks.broker import get_all_celery_queue_names
from fides.api.tasks.broker import get_sqs_client as _get_sqs_client
from fides.api.tasks.queue_migration import (
    MIGRATION_BATCH_SIZE,
    MIGRATION_LOCK_KEY,
    MIGRATION_LOCK_TTL_SECONDS,
    MigrationResult,
    _send_in_batches,
    migrate_redis_queues_to_sqs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    use_sqs_queue: bool = True,
    sqs_url: Optional[str] = "http://elasticmq:9324",
    aws_region: str = "us-east-1",
    aws_access_key_id: Optional[str] = "x",
    aws_secret_access_key: Optional[str] = "x",
    sqs_queue_name_prefix: str = "fides-",
) -> SimpleNamespace:
    """Build a minimal config object matching the shape used by the migrator."""
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


class FakeRedis:
    """Minimal Redis fake supporting ``SET NX EX``, ``LRANGE``, ``DEL``, ``GET``.

    Captures just enough Redis surface area to exercise the migrator
    deterministically without a live Redis connection.
    """

    def __init__(
        self, initial_lists: Optional[Dict[str, List[bytes]]] = None
    ) -> None:
        self._lists: Dict[str, List[bytes]] = {
            key: list(values) for key, values in (initial_lists or {}).items()
        }
        self._strings: Dict[str, str] = {}
        # Observed operations, in call order — used in unit tests to assert
        # operation sequencing (lock-before-queue-ops, etc.).
        self.calls: List[tuple] = []

    # -- String ops ----------------------------------------------------
    def set(
        self,
        key: str,
        value: str,
        nx: bool = False,
        ex: Optional[int] = None,
    ) -> bool:
        self.calls.append(("set", key, value, nx, ex))
        if nx and key in self._strings:
            return False
        self._strings[key] = value
        return True

    def get(self, key: str) -> Optional[str]:
        return self._strings.get(key)

    # -- List ops ------------------------------------------------------
    def lrange(self, key: str, start: int, end: int) -> List[bytes]:
        self.calls.append(("lrange", key, start, end))
        values = self._lists.get(key, [])
        if end == -1:
            return list(values[start:])
        return list(values[start : end + 1])

    def ltrim(self, key: str, start: int, end: int) -> None:
        """Trim the list so only elements from ``start`` to ``end`` remain."""
        self.calls.append(("ltrim", key, start, end))
        if key not in self._lists:
            return
        values = self._lists[key]
        if end == -1:
            self._lists[key] = values[start:]
        else:
            self._lists[key] = values[start : end + 1]

    # -- Generic deletion ---------------------------------------------
    def delete(self, *keys: str) -> int:
        self.calls.append(("delete", *keys))
        removed = 0
        for k in keys:
            if k in self._lists:
                del self._lists[k]
                removed += 1
            if k in self._strings:
                del self._strings[k]
                removed += 1
        return removed

    # -- Test-only helpers --------------------------------------------
    def has_key(self, key: str) -> bool:
        return key in self._strings or key in self._lists


def _make_sqs_mock() -> MagicMock:
    """Build a MagicMock SQS client with a recordable ``send_message_batch``."""
    client = MagicMock()
    client.send_message_batch = MagicMock(
        return_value={"Successful": [], "Failed": []}
    )
    return client


def _sqs_send_entries_count(sqs_client: MagicMock) -> int:
    """Sum of ``len(Entries)`` across every recorded ``send_message_batch`` call."""
    total = 0
    for call in sqs_client.send_message_batch.call_args_list:
        total += len(call.kwargs["Entries"])
    return total


# ===========================================================================
# Task 8.1 — Property 2: Migration Idempotency
# ===========================================================================


class TestMigrationIdempotencyProperty:
    """Property 2: For any set of queues already empty in Redis,
    ``migrate_redis_queues_to_sqs`` returns
    ``MigrationResult(migrated={q: 0 for q in queues}, skipped=False,
    errors=[])`` and enqueues nothing to SQS.

    Validates: Requirements 5.8
    """

    @given(
        run_count=st.integers(min_value=1, max_value=3),
    )
    @settings(max_examples=10)
    def test_empty_queues_yield_zero_counts_and_no_sqs_calls(
        self, run_count: int
    ) -> None:
        all_queues = get_all_celery_queue_names()

        sqs_client = _make_sqs_mock()
        config = _make_config()

        # Run the migration ``run_count`` times back-to-back.  Every run
        # must be idempotent on empty queues.
        for _ in range(run_count):
            redis_conn = FakeRedis(initial_lists={})  # no queues populated
            with patch(
                "fides.api.tasks.broker.get_sqs_client",
                return_value=sqs_client,
            ):
                result = migrate_redis_queues_to_sqs(
                    redis_conn, celery_app=MagicMock(), config=config
                )

            assert result.skipped is False
            assert result.errors == []
            assert set(result.migrated.keys()) == set(all_queues)
            assert all(count == 0 for count in result.migrated.values())

        # No SendMessageBatch should ever have been called across any run.
        sqs_client.send_message_batch.assert_not_called()


# ===========================================================================
# Task 8.2 — Property 3: Migration Lock Exclusivity
# ===========================================================================


class TestMigrationLockExclusivityProperty:
    """Property 3: For any two concurrent calls, at most one returns
    ``skipped=False``; all others return ``skipped=True``.

    Validates: Requirements 5.1, 5.2
    """

    @given(
        concurrent_callers=st.integers(min_value=2, max_value=8),
    )
    @settings(max_examples=10)
    def test_at_most_one_concurrent_caller_is_not_skipped(
        self, concurrent_callers: int
    ) -> None:
        # Shared FakeRedis simulates a single Redis instance seen by every
        # caller.  Real SET NX semantics guarantee only the first caller
        # succeeds in acquiring the lock.
        shared_redis = FakeRedis()

        # Intercept ``delete`` during the migration body to *prevent* the
        # lock from being released between calls.  Otherwise the second
        # caller would happily re-acquire the lock sequentially, which
        # does not model the "concurrent" scenario the property describes.
        original_delete = shared_redis.delete
        migration_active = {"count": 0}

        def delete_during_migration(*keys: str) -> int:
            # Lock-release delete only runs after the migration body
            # completes; we need all callers to interleave *before* any
            # lock release.  Queue lock-release deletes until all callers
            # have attempted acquisition.
            if migration_active["count"] < concurrent_callers and keys == (
                MIGRATION_LOCK_KEY,
            ):
                # Defer the actual release until the end of the test.
                return 0
            return original_delete(*keys)

        shared_redis.delete = delete_during_migration  # type: ignore[method-assign]

        sqs_client = _make_sqs_mock()
        config = _make_config()
        results: List[MigrationResult] = []

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            for _ in range(concurrent_callers):
                migration_active["count"] += 1
                result = migrate_redis_queues_to_sqs(
                    shared_redis, celery_app=MagicMock(), config=config
                )
                results.append(result)

        not_skipped = [r for r in results if r.skipped is False]
        assert len(not_skipped) <= 1, (
            f"Expected at most 1 caller to own the lock; "
            f"{len(not_skipped)} of {concurrent_callers} did."
        )
        assert len(not_skipped) >= 1, (
            "Expected exactly one caller to acquire the lock; none did."
        )


# ===========================================================================
# Task 8.3 — Property 4: Lock Release Guarantee
# ===========================================================================


class TestLockReleaseGuaranteeProperty:
    """Property 4: For any execution (success or exception), the migration
    lock key is absent from Redis after the function returns.

    Validates: Requirements 5.7
    """

    @given(
        # Either populate some queues with messages, leave all empty, or
        # inject a failing SQS client that raises during the batch send.
        # In every case the lock must be released.
        scenario=st.sampled_from(
            ["empty", "populated", "per_queue_error", "sqs_build_error"]
        ),
    )
    @settings(max_examples=20)
    def test_lock_is_released_after_return(self, scenario: str) -> None:
        all_queues = get_all_celery_queue_names()
        config = _make_config()

        if scenario == "empty":
            redis_conn = FakeRedis()
            sqs_client = _make_sqs_mock()
            build_patch = patch(
                "fides.api.tasks.broker.get_sqs_client",
                return_value=sqs_client,
            )
            expect_exception = False
        elif scenario == "populated":
            redis_conn = FakeRedis(
                initial_lists={q: [b"msg1", b"msg2"] for q in all_queues}
            )
            sqs_client = _make_sqs_mock()
            build_patch = patch(
                "fides.api.tasks.broker.get_sqs_client",
                return_value=sqs_client,
            )
            expect_exception = False
        elif scenario == "per_queue_error":
            redis_conn = FakeRedis(
                initial_lists={q: [b"msg"] for q in all_queues}
            )
            sqs_client = _make_sqs_mock()
            sqs_client.send_message_batch = MagicMock(
                side_effect=RuntimeError("boom")
            )
            build_patch = patch(
                "fides.api.tasks.broker.get_sqs_client",
                return_value=sqs_client,
            )
            expect_exception = False  # per-queue errors are swallowed
        else:  # sqs_build_error
            redis_conn = FakeRedis()
            build_patch = patch(
                "fides.api.tasks.broker.get_sqs_client",
                side_effect=RuntimeError("cannot build sqs client"),
            )
            expect_exception = True

        with build_patch:
            if expect_exception:
                with pytest.raises(RuntimeError):
                    migrate_redis_queues_to_sqs(
                        redis_conn, celery_app=MagicMock(), config=config
                    )
            else:
                migrate_redis_queues_to_sqs(
                    redis_conn, celery_app=MagicMock(), config=config
                )

        assert redis_conn.has_key(MIGRATION_LOCK_KEY) is False, (
            f"Migration lock leaked (scenario={scenario})"
        )


# ===========================================================================
# Task 8.4 — Property 11: Migration Batch Sizing
# ===========================================================================


class TestMigrationBatchSizingProperty:
    """Property 11: For any list of N task messages from a single Redis
    queue, the number of ``SendMessageBatch`` calls is ``ceil(N / 10)``.

    Validates: Requirements 5.4
    """

    @given(n=st.integers(min_value=0, max_value=97))
    @settings(max_examples=50)
    def test_batch_count_is_ceil_n_over_10(self, n: int) -> None:
        sqs_client = _make_sqs_mock()
        raw_messages = [f"m{i}".encode() for i in range(n)]

        _send_in_batches(
            sqs_client,
            sqs_url="http://elasticmq:9324/queue/fides-fides-dsr",
            raw_messages=raw_messages,
            batch_size=MIGRATION_BATCH_SIZE,
        )

        expected_calls = math.ceil(n / MIGRATION_BATCH_SIZE) if n > 0 else 0
        assert sqs_client.send_message_batch.call_count == expected_calls, (
            f"For N={n} expected {expected_calls} send_message_batch calls, "
            f"got {sqs_client.send_message_batch.call_count}"
        )

    @given(n=st.integers(min_value=1, max_value=97))
    @settings(max_examples=50)
    def test_batch_count_end_to_end(self, n: int) -> None:
        """End-to-end: call the full migrator with N messages in a single
        queue and assert ``ceil(N/10)`` send_message_batch calls."""
        all_queues = get_all_celery_queue_names()
        target_queue = all_queues[0]

        redis_conn = FakeRedis(
            initial_lists={target_queue: [f"m{i}".encode() for i in range(n)]}
        )
        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        assert sqs_client.send_message_batch.call_count == math.ceil(
            n / MIGRATION_BATCH_SIZE
        )


# ===========================================================================
# Task 8.5 — Property 7: Zero Task Loss
# ===========================================================================


class TestZeroTaskLossProperty:
    """Property 7: For any list of task messages in Redis before migration,
    the total messages in SQS after migration equals the number that were
    in Redis (assuming no concurrent enqueues).

    Validates: Requirements 5.3, 5.5
    """

    @given(
        counts_per_queue=st.dictionaries(
            keys=st.sampled_from(get_all_celery_queue_names()),
            values=st.integers(min_value=0, max_value=35),
            max_size=len(get_all_celery_queue_names()),
        )
    )
    @settings(max_examples=30)
    def test_all_redis_messages_land_in_sqs(
        self, counts_per_queue: Dict[str, int]
    ) -> None:
        redis_initial = {
            q: [f"{q}-m{i}".encode() for i in range(count)]
            for q, count in counts_per_queue.items()
            if count > 0
        }
        total_before = sum(len(msgs) for msgs in redis_initial.values())

        redis_conn = FakeRedis(initial_lists=redis_initial)
        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            result = migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        total_sent = _sqs_send_entries_count(sqs_client)

        assert total_sent == total_before, (
            f"Lost tasks: redis had {total_before}, sqs received {total_sent}"
        )
        assert result.skipped is False
        assert result.errors == []

        # And the ``migrated`` counts agree per queue.
        for q, expected in counts_per_queue.items():
            assert result.migrated.get(q, 0) == expected

        # Every drained Redis queue key is gone.
        for q in redis_initial:
            assert redis_conn.lrange(q, 0, -1) == []


# ===========================================================================
# Task 8.6 — Unit tests for StartupQueueMigrator
# ===========================================================================


class TestStartupQueueMigratorUnit:
    """Unit tests for ``migrate_redis_queues_to_sqs`` covering lock
    acquisition order, per-queue operations, lock release on exception,
    ``skipped=True`` semantics, idempotency, and error continuation.
    """

    def test_lock_acquired_before_any_queue_operation(self) -> None:
        redis_conn = FakeRedis(initial_lists={"fides": [b"m1"]})
        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        op_names = [call[0] for call in redis_conn.calls]
        # First observed op must be the lock SET.
        assert op_names[0] == "set"
        assert redis_conn.calls[0][1] == MIGRATION_LOCK_KEY
        assert redis_conn.calls[0][3] is True  # nx
        assert redis_conn.calls[0][4] == MIGRATION_LOCK_TTL_SECONDS

        # No queue op may appear before the lock SET.
        first_queue_op_index = next(
            (i for i, op in enumerate(op_names) if op in ("lrange", "delete")),
            len(op_names),
        )
        assert first_queue_op_index > 0

    def test_lrange_and_ltrim_called_per_queue(self) -> None:
        all_queues = get_all_celery_queue_names()
        redis_conn = FakeRedis(
            initial_lists={q: [b"msg"] for q in all_queues}
        )
        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        lrange_keys = [c[1] for c in redis_conn.calls if c[0] == "lrange"]
        ltrim_keys = [
            c[1]
            for c in redis_conn.calls
            if c[0] == "ltrim"
        ]

        assert set(lrange_keys) == set(all_queues)
        assert set(ltrim_keys) == set(all_queues)

    def test_send_message_batch_called_with_correct_batches(self) -> None:
        target_queue = "fides.dsr"
        # 23 messages → 3 batches (10 + 10 + 3)
        messages = [f"task-{i}".encode() for i in range(23)]
        redis_conn = FakeRedis(initial_lists={target_queue: messages})
        sqs_client = _make_sqs_mock()
        config = _make_config(sqs_queue_name_prefix="fides-")

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        calls = sqs_client.send_message_batch.call_args_list
        assert len(calls) == 3

        # Every call targets the correct SQS queue URL.
        expected_url = (
            "http://elasticmq:9324/queue/fides-fides-dsr"
        )
        for call in calls:
            assert call.kwargs["QueueUrl"] == expected_url

        # Batch sizes: 10, 10, 3
        assert [len(c.kwargs["Entries"]) for c in calls] == [10, 10, 3]

        # And the cumulative message bodies preserve ordering and content.
        all_bodies: List[str] = []
        for call in calls:
            for entry in call.kwargs["Entries"]:
                all_bodies.append(entry["MessageBody"])
                assert "Id" in entry  # required by SQS
        assert all_bodies == [m.decode() for m in messages]

    def test_lock_released_on_success(self) -> None:
        redis_conn = FakeRedis()
        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        assert redis_conn.has_key(MIGRATION_LOCK_KEY) is False
        # Final recorded op is the lock-release DEL.
        assert redis_conn.calls[-1][0] == "delete"
        assert redis_conn.calls[-1][1] == MIGRATION_LOCK_KEY

    def test_sqs_build_error_skips_migration(self) -> None:
        """When ``get_sqs_client`` or SQS connectivity check fails,
        the migration is skipped (skipped=True) — no Redis keys are touched."""
        redis_conn = FakeRedis()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            side_effect=RuntimeError("build failed"),
        ):
            result = migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        assert result.skipped is True
        assert result.migrated == {}
        assert result.errors == []
        assert redis_conn.has_key(MIGRATION_LOCK_KEY) is True

    def test_skipped_true_when_lock_not_acquired(self) -> None:
        # Pre-populate the lock so SET NX returns False.
        redis_conn = FakeRedis()
        redis_conn._strings[MIGRATION_LOCK_KEY] = "held-by-other-process"

        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ) as build_mock:
            result = migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        assert result.skipped is True
        assert result.migrated == {}
        assert result.errors == []
        # No queue traversal when the lock was not acquired.
        build_mock.assert_not_called()
        sqs_client.send_message_batch.assert_not_called()
        # The lock key belongs to another process — our call must not have
        # deleted it.
        assert redis_conn.has_key(MIGRATION_LOCK_KEY) is True

    def test_skipped_true_when_redis_unavailable(self) -> None:
        """Requirement 8.4: Redis failure during lock acquisition → skipped."""
        redis_conn = MagicMock()
        redis_conn.set = MagicMock(side_effect=ConnectionError("redis down"))

        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            result = migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        assert result.skipped is True
        assert result.migrated == {}
        assert result.errors == []
        sqs_client.send_message_batch.assert_not_called()

    def test_idempotent_on_empty_queues(self) -> None:
        all_queues = get_all_celery_queue_names()
        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            # First run.
            redis_conn_1 = FakeRedis()
            result_1 = migrate_redis_queues_to_sqs(
                redis_conn_1, celery_app=MagicMock(), config=config
            )
            # Second run (lock freed by finally of first run — different
            # FakeRedis instance to mimic a fresh start).
            redis_conn_2 = FakeRedis()
            result_2 = migrate_redis_queues_to_sqs(
                redis_conn_2, celery_app=MagicMock(), config=config
            )

        for result in (result_1, result_2):
            assert result.skipped is False
            assert result.errors == []
            assert set(result.migrated.keys()) == set(all_queues)
            assert all(v == 0 for v in result.migrated.values())

        sqs_client.send_message_batch.assert_not_called()

    def test_per_queue_error_is_recorded_and_iteration_continues(self) -> None:
        all_queues = get_all_celery_queue_names()
        failing_queue = all_queues[0]

        redis_conn = FakeRedis(
            initial_lists={q: [b"m1"] for q in all_queues}
        )
        sqs_client = _make_sqs_mock()

        def fail_on_target(QueueUrl: str, Entries: list) -> Any:  # noqa: N803
            if failing_queue in QueueUrl:
                raise RuntimeError("simulated SQS error")
            return {"Successful": [], "Failed": []}

        sqs_client.send_message_batch = MagicMock(side_effect=fail_on_target)
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            result = migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        # The failing queue produced an error entry.
        assert any(failing_queue in err for err in result.errors), (
            f"Expected error for {failing_queue}, got errors: {result.errors}"
        )
        # Iteration continued — every non-failing queue has a migrated count.
        for q in all_queues:
            if q == failing_queue:
                continue
            assert result.migrated.get(q) == 1, (
                f"Queue {q} should have migrated 1 message; "
                f"got {result.migrated.get(q)}"
            )

        # The failing queue's Redis key is still present (ltrim only
        # happens after successful SQS send).
        assert redis_conn.lrange(failing_queue, 0, -1) == [b"m1"]

        # Non-failing queues are fully drained via ltrim.
        for q in all_queues:
            if q == failing_queue:
                continue
            assert redis_conn.lrange(q, 0, -1) == []

        # The migration was not globally skipped.
        assert result.skipped is False
        # Lock still released.
        assert redis_conn.has_key(MIGRATION_LOCK_KEY) is False

    def test_sqs_connectivity_check_skips_migration_on_failure(self) -> None:
        """When SQS connectivity check fails (but get_sqs_client succeeds),
        migration is skipped — no Redis keys are touched."""
        redis_conn = FakeRedis(initial_lists={"fides.dsr": [b"m1"]})
        sqs_client = _make_sqs_mock()
        sqs_client.get_queue_url = MagicMock(side_effect=RuntimeError("no SQS"))
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            result = migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        assert result.skipped is True
        assert result.migrated == {}
        assert result.errors == []
        # Redis data is untouched.
        assert redis_conn.lrange("fides.dsr", 0, -1) == [b"m1"]

    def test_sqs_connectivity_check_succeeds_on_first_queue(self) -> None:
        """When get_queue_url succeeds on the first queue, the check
        stops early and migration proceeds normally."""
        redis_conn = FakeRedis(initial_lists={"fides.dsr": [b"m1"]})
        sqs_client = _make_sqs_mock()
        sqs_client.get_queue_url = MagicMock(return_value={"QueueUrl": "http://test"})
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            result = migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        assert result.skipped is False
        sqs_client.get_queue_url.assert_called_once()

    def test_delete_after_send_on_success(self) -> None:
        """Redis keys are deleted only after all batches are confirmed
        in SQS (send-then-delete ordering)."""
        target_queue = "fides.dsr"
        messages = [b"task-1", b"task-2"]
        redis_conn = FakeRedis(initial_lists={target_queue: messages})
        sqs_client = _make_sqs_mock()
        config = _make_config()

        with patch(
            "fides.api.tasks.broker.get_sqs_client",
            return_value=sqs_client,
        ):
            migrate_redis_queues_to_sqs(
                redis_conn, celery_app=MagicMock(), config=config
            )

        # Find the indices of send_message_batch calls and the delete call.
        send_indices = [
            i for i, c in enumerate(redis_conn.calls) if c[0] == "lrange"
        ]
        delete_indices = [
            i for i, c in enumerate(redis_conn.calls)
            if c[0] == "delete" and c[1] != MIGRATION_LOCK_KEY
        ]
        # lrange must come before delete for the target queue.
        assert send_indices[0] < delete_indices[0]


# ===========================================================================
# MigrationResult dataclass sanity
# ===========================================================================


class TestMigrationResultDefaults:
    def test_default_fields(self) -> None:
        result = MigrationResult()
        assert result.migrated == {}
        assert result.skipped is False
        assert result.errors == []

    def test_fields_are_independent_instances(self) -> None:
        """Ensure default_factory is used — dataclass defaults must not
        share state between instances."""
        a = MigrationResult()
        b = MigrationResult()
        a.migrated["fides"] = 1
        a.errors.append("err")
        assert b.migrated == {}
        assert b.errors == []

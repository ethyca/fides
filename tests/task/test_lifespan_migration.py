"""Tests for the lifespan startup hook integration (``run_sqs_migration``).

Covers:
- Task 9.1 — Lifespan startup hook calls ``migrate_redis_queues_to_sqs``
  when ``use_sqs_queue=True`` and skips it when ``False``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fides.api.app_setup import run_sqs_migration
from fides.api.tasks.queue_migration import MigrationResult

# ---------------------------------------------------------------------------
# Task 9.1 — Lifespan startup hook calls the migrator conditionally
# ---------------------------------------------------------------------------


class TestRunSqsMigration:
    """``run_sqs_migration`` is the lifespan entry-point for Task 9.

    It must invoke ``migrate_redis_queues_to_sqs`` iff the feature flag is
    enabled so that the Redis broker path is entirely untouched when
    ``use_sqs_queue=False``.
    """

    def test_calls_migrator_when_use_sqs_queue_true(self) -> None:
        """When the flag is on, the migrator runs with the Redis cache and
        celery app wired through."""
        fake_redis = MagicMock(name="fake_redis")

        with (
            patch("fides.api.app_setup.CONFIG") as mock_config,
            patch(
                "fides.api.app_setup.get_cache", return_value=fake_redis
            ) as mock_get_cache,
            patch(
                "fides.api.tasks.queue_migration.migrate_redis_queues_to_sqs",
                return_value=MigrationResult(migrated={}, skipped=False, errors=[]),
            ) as mock_migrate,
        ):
            mock_config.queue.use_sqs_queue = True
            run_sqs_migration()

        mock_get_cache.assert_called_once()
        mock_migrate.assert_called_once()
        # redis_conn is the first positional argument
        redis_arg = mock_migrate.call_args.args[0]
        assert redis_arg is fake_redis

    def test_does_not_call_migrator_when_use_sqs_queue_false(self) -> None:
        """When the flag is off, the migrator (and even ``get_cache``) must
        not be touched — the Redis broker path is unchanged."""
        with (
            patch("fides.api.app_setup.CONFIG") as mock_config,
            patch("fides.api.app_setup.get_cache") as mock_get_cache,
            patch(
                "fides.api.tasks.queue_migration.migrate_redis_queues_to_sqs"
            ) as mock_migrate,
        ):
            mock_config.queue.use_sqs_queue = False
            run_sqs_migration()

        mock_migrate.assert_not_called()
        mock_get_cache.assert_not_called()

    def test_skipped_result_logs_info_without_error(self) -> None:
        """A ``skipped=True`` MigrationResult is a normal outcome (another
        process is migrating) and must not surface as a warning."""
        with (
            patch("fides.api.app_setup.CONFIG") as mock_config,
            patch("fides.api.app_setup.get_cache", return_value=MagicMock()),
            patch(
                "fides.api.tasks.queue_migration.migrate_redis_queues_to_sqs",
                return_value=MigrationResult(migrated={}, skipped=True, errors=[]),
            ) as mock_migrate,
        ):
            mock_config.queue.use_sqs_queue = True
            # Should not raise even when the migrator reports skipped.
            run_sqs_migration()

        mock_migrate.assert_called_once()

    def test_redis_unavailable_skips_without_raising(self) -> None:
        """Requirement 8.4 — if Redis is unavailable at startup in SQS mode
        the helper logs and returns without calling the migrator."""
        from fides.api.common_exceptions import RedisConnectionError

        with (
            patch("fides.api.app_setup.CONFIG") as mock_config,
            patch(
                "fides.api.app_setup.get_cache",
                side_effect=RedisConnectionError("redis down"),
            ),
            patch(
                "fides.api.tasks.queue_migration.migrate_redis_queues_to_sqs"
            ) as mock_migrate,
        ):
            mock_config.queue.use_sqs_queue = True
            # Must not re-raise; startup continues even when Redis is down.
            run_sqs_migration()

        mock_migrate.assert_not_called()

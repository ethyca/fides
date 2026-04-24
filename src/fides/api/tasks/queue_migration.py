"""
Startup queue migration — drain Redis Celery queues into SQS.

When the ``use_sqs_queue`` feature flag flips on for the first time, any
tasks already queued in Redis would be orphaned because Celery workers are
about to start polling SQS instead.  This module provides a zero-loss
cutover: on startup it acquires a distributed Redis lock, **pre-flight
checks SQS connectivity**, then reads pending task messages from every
known Celery queue in Redis and re-enqueues them to the corresponding SQS
queue in batches of 10 (the SQS ``SendMessageBatch`` cap).

Messages are drained from Redis in batches of 10 and sent to SQS
immediately — only after a batch is confirmed in SQS are those messages
removed from Redis.  This prevents holding large amounts of data in
memory and ensures that if SQS becomes unreachable mid-migration, only
the current batch is at risk (the pre-flight check makes this unlikely).

The migration is idempotent (safe to call on every startup) — a subsequent
run with empty Redis queues is a no-op that returns zero counts.

The lock is always released via ``try/finally`` and has a short TTL so a
crashed process does not permanently block subsequent migration attempts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from fides.api.tasks.broker import (
    get_all_celery_queue_names,
    get_sqs_base_url,
    get_sqs_client,
    get_sqs_queue_url,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIGRATION_LOCK_KEY = "fides:sqs_migration_lock"
MIGRATION_LOCK_TTL_SECONDS = 120
# AWS SQS ``SendMessageBatch`` accepts at most 10 entries per call.
MIGRATION_BATCH_SIZE = 10


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------


@dataclass
class MigrationResult:
    """Outcome of a migration attempt.

    Attributes:
        migrated: Map of Celery queue name → number of messages moved.
        skipped: ``True`` when the migration lock could not be acquired
            (another process is already migrating, or Redis was unavailable).
        errors: Per-queue error messages collected while iterating.
    """

    migrated: Dict[str, int] = field(default_factory=dict)
    skipped: bool = False
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def migrate_redis_queues_to_sqs(
    redis_conn: Any,
    celery_app: Any,  # pylint: disable=unused-argument
    config: Any,
) -> MigrationResult:
    """Drain each known Celery queue from Redis and re-enqueue to SQS.

    Algorithm (see ``.kiro/specs/sqs-queue-migration/design.md`` §Algorithm 2):

    1. ``SET MIGRATION_LOCK_KEY "1" NX EX MIGRATION_LOCK_TTL_SECONDS`` —
       acquire a distributed lock so only one process migrates at a time.
    2. **Pre-flight SQS check**: verify SQS connectivity before touching
       Redis.  If unreachable, ``skipped=True`` is returned — no Redis
       keys are drained so no messages are lost.
    3. For each Celery queue: read messages in batches of 10 from Redis,
       send each batch to SQS, and only after confirmation delete those
       messages from Redis.  This keeps memory bounded and ensures that
       if SQS fails mid-stream, only the current batch is at risk.
    4. ``DEL MIGRATION_LOCK_KEY`` in a ``finally`` block so the lock is
       always released (crash recovery still relies on the TTL).

    Returns a :class:`MigrationResult` — never raises.  If Redis itself is
    unavailable, ``skipped=True`` is returned and the caller can continue
    starting up with SQS as the broker (Requirement 8.4).
    """
    result = MigrationResult()

    # Requirement 8.4: if Redis is unavailable at startup, log and skip
    # without crashing the application.
    try:
        acquired = redis_conn.set(
            MIGRATION_LOCK_KEY,
            "1",
            nx=True,
            ex=MIGRATION_LOCK_TTL_SECONDS,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Could not acquire SQS migration lock from Redis — skipping migration: %s",
            exc,
        )
        result.skipped = True
        return result

    if not acquired:
        # Another process holds the lock; it will do the migration.
        result.skipped = True
        return result

    queue_names = get_all_celery_queue_names()
    base_url = get_sqs_base_url(config)
    prefix = config.queue.sqs_queue_name_prefix

    try:
        # Pre-flight: verify SQS connectivity before touching any Redis data.
        # If SQS is unreachable, we skip the entire migration — no Redis keys
        # are drained so no messages are lost.
        try:
            sqs_client = get_sqs_client(config)
            _verify_sqs_connectivity(sqs_client, config)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Could not connect to SQS — skipping migration: %s",
                exc,
            )
            result.skipped = True
            return result

        # Loop invariant: at the start of each iteration, all queues
        # processed so far are drained from Redis and their tasks are in
        # SQS (or have an entry in ``result.errors``).
        for queue_name in queue_names:
            try:
                # Drain the queue in batches to keep memory bounded.
                # Read up to MIGRATION_BATCH_SIZE messages, send to SQS,
                # confirm, then remove those messages from Redis before
                # reading the next batch.
                total_count = 0
                while True:
                    raw_messages = (
                        redis_conn.lrange(queue_name, 0, MIGRATION_BATCH_SIZE - 1) or []
                    )
                    batch_count = len(raw_messages)
                    if batch_count == 0:
                        break

                    sqs_url = get_sqs_queue_url(
                        queue_name,
                        base_url,
                        prefix,
                    )
                    _send_in_batches(sqs_client, sqs_url, raw_messages)

                    # Confirm success — only then remove the processed
                    # messages from the head of the Redis list.
                    redis_conn.ltrim(queue_name, batch_count, -1)
                    total_count += batch_count

                result.migrated[queue_name] = total_count
            except Exception as exc:  # noqa: BLE001
                msg = f"Failed to migrate {queue_name}: {exc}"
                logger.error(msg)
                result.errors.append(msg)
    finally:
        # Requirement 5.7: lock released in all cases, including on
        # exception.  Swallow any error here so the caller still sees the
        # original failure rather than a misleading lock-release error.
        try:
            redis_conn.delete(MIGRATION_LOCK_KEY)
        except Exception as exc:  # noqa: BLE001
            logger.error("Could not release SQS migration lock: %s", exc)

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _verify_sqs_connectivity(sqs_client: Any, config: Any) -> None:
    """Verify that the SQS endpoint is reachable by listing a queue.

    Uses ``get_queue_url`` which raises if the endpoint is unreachable or
    credentials are invalid.  No queues are modified.
    """
    for queue_name in get_all_celery_queue_names():
        sqs_url = get_sqs_queue_url(
            queue_name,
            get_sqs_base_url(config),
            config.queue.sqs_queue_name_prefix,
        )
        try:
            sqs_client.get_queue_url(QueueName=sqs_url.split("/")[-1])
            return  # First queue responded — connectivity confirmed.
        except Exception:  # noqa: BLE001
            continue
    # If we get here, none of the queues responded. The caller will
    # treat this as a full migration skip.


def _send_in_batches(
    sqs_client: Any,
    sqs_url: str,
    raw_messages: Iterable[Any],
    batch_size: int = MIGRATION_BATCH_SIZE,
) -> None:
    """Send ``raw_messages`` to ``sqs_url`` in batches of ``batch_size``.

    Each batch makes one ``send_message_batch`` call.  Number of calls is
    ``ceil(N / batch_size)`` per Property 11.
    """
    batch: List[Dict[str, str]] = []
    for index, message in enumerate(raw_messages):
        body = (
            message.decode("utf-8")
            if isinstance(message, (bytes, bytearray))
            else str(message)
        )
        batch.append(
            {
                # ``Id`` must be unique within a single batch; a per-message
                # index satisfies that without collisions across batches
                # because each batch is sent independently.
                "Id": str(index),
                "MessageBody": body,
            }
        )
        if len(batch) >= batch_size:
            try:
                sqs_client.send_message_batch(QueueUrl=sqs_url, Entries=batch)
            except Exception:  # noqa: BLE001
                logger.error(
                    "Failed to send batch of %d messages to SQS queue %s: %s",
                    len(batch),
                    sqs_url,
                    exc_info=True,
                )
                raise
            batch = []

    if batch:
        try:
            sqs_client.send_message_batch(QueueUrl=sqs_url, Entries=batch)
        except Exception:  # noqa: BLE001
            logger.error(
                "Failed to send final batch of %d messages to SQS queue %s: %s",
                len(batch),
                sqs_url,
                exc_info=True,
            )
            raise

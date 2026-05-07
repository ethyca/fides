"""Periodic DSR cache sweeper: clears Redis cache keys for terminal privacy requests.

Eligible rows are selected from Postgres by terminal status and staleness on
``updated_at``. For each id we re-read ``status`` immediately before clearing to
avoid races with status transitions, then call ``get_dsr_cache_store(id).clear()``
(same effect as ``PrivacyRequest.clear_cached_values``).

The Celery entrypoint gates on resolved ``execution.dsr_cache_sweeper.enabled``
(application preference, default off). Server tuning lives under
``execution.dsr_cache_sweeper`` (see ``DsrCacheSweeperSettings``).
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import FrozenSet

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import (
    ACTIVE_REQUEST_STATUSES,
    PrivacyRequestStatus,
)
from fides.api.util.cache import get_dsr_cache_store
from fides.config import CONFIG


@dataclass(frozen=True)
class DsrCacheSweeperResult:
    rows_scanned: int
    redis_clear_attempts: int
    rows_skipped_status_mismatch: int
    redis_errors: int
    keys_deleted_estimate: int
    duration_seconds: float
    dry_run: bool


def build_dsr_cache_sweeper_statuses(
    *,
    include_denied_and_duplicate: bool,
    include_error: bool,
) -> FrozenSet[PrivacyRequestStatus]:
    """Statuses whose Redis DSR cache may be cleared by the sweeper.

    Always excludes :data:`ACTIVE_REQUEST_STATUSES` by construction (those are
    never added to the allowlist).
    """
    statuses: set[PrivacyRequestStatus] = {
        PrivacyRequestStatus.complete,
        PrivacyRequestStatus.canceled,
    }
    if include_denied_and_duplicate:
        statuses.update(
            {
                PrivacyRequestStatus.denied,
                PrivacyRequestStatus.duplicate,
            }
        )
    if include_error:
        statuses.add(PrivacyRequestStatus.error)

    overlap = statuses & ACTIVE_REQUEST_STATUSES
    if overlap:
        raise RuntimeError(
            "DSR cache sweeper status allowlist overlaps ACTIVE_REQUEST_STATUSES: "
            f"{overlap}"
        )
    return frozenset(statuses)


def run_dsr_cache_sweeper(
    db: Session,
) -> DsrCacheSweeperResult:
    """Scan Postgres for stale terminal privacy requests and clear Redis DSR cache."""
    tc = CONFIG.execution.dsr_cache_sweeper
    terminal_statuses = build_dsr_cache_sweeper_statuses(
        include_denied_and_duplicate=tc.include_denied_and_duplicate,
        include_error=tc.include_error,
    )
    staleness_minutes = tc.staleness_minutes
    batch_size = max(1, int(tc.batch_size))
    batch_sleep = float(tc.batch_sleep_seconds)
    dry_run = tc.dry_run
    dry_run_probe = tc.dry_run_probe_redis

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=staleness_minutes)

    rows_scanned = 0
    redis_clear_attempts = 0
    rows_skipped_status_mismatch = 0
    redis_errors = 0
    keys_deleted_estimate = 0

    last_id = ""
    started = time.perf_counter()

    while True:
        batch_rows = (
            db.query(PrivacyRequest.id, PrivacyRequest.status)
            .filter(
                PrivacyRequest.deleted_at.is_(None),
                PrivacyRequest.status.in_(list(terminal_statuses)),
                PrivacyRequest.updated_at < cutoff,
                PrivacyRequest.id > last_id,
            )
            .order_by(PrivacyRequest.id)
            .limit(batch_size)
            .all()
        )
        if not batch_rows:
            break

        for pr_id, initial_status in batch_rows:
            rows_scanned += 1

            current = (
                db.query(PrivacyRequest.status)
                .filter(PrivacyRequest.id == pr_id)
                .scalar()
            )
            if current is None or current not in terminal_statuses:
                rows_skipped_status_mismatch += 1
                logger.debug(
                    "Skipping DSR cache sweeper for privacy_request_id={}: "
                    "status no longer eligible (batch had {}, current={})",
                    pr_id,
                    initial_status.value,
                    getattr(current, "value", current),
                )
                continue

            store = get_dsr_cache_store(str(pr_id))
            keys_before = 0
            if dry_run and dry_run_probe:
                try:
                    keys_before = len(store.get_all_keys())
                except Exception as exc:  # noqa: BLE001
                    redis_errors += 1
                    logger.warning(
                        "Redis probe failed for privacy_request_id={} status={}: {}",
                        pr_id,
                        current.value,
                        exc,
                    )
                    continue
            elif not dry_run:
                try:
                    keys_before = len(store.get_all_keys())
                except Exception as exc:  # noqa: BLE001
                    redis_errors += 1
                    logger.warning(
                        "Redis key listing failed before clear for privacy_request_id={} "
                        "status={}: {}",
                        pr_id,
                        current.value,
                        exc,
                    )
                    continue

            if dry_run:
                logger.info(
                    "Dry-run DSR cache sweeper privacy_request_id={} status={} "
                    "cutoff_age_minutes={} keys_visible={}",
                    pr_id,
                    current.value,
                    staleness_minutes,
                    keys_before if dry_run_probe else "skipped_probe",
                )
                redis_clear_attempts += 1
                keys_deleted_estimate += keys_before
                continue

            try:
                store.clear()
                redis_clear_attempts += 1
                keys_deleted_estimate += keys_before
                logger.info(
                    "Cleared Redis DSR cache privacy_request_id={} status={} "
                    "staleness_minutes={} keys_removed_estimate={}",
                    pr_id,
                    current.value,
                    staleness_minutes,
                    keys_before,
                )
            except Exception as exc:  # noqa: BLE001
                redis_errors += 1
                logger.warning(
                    "Redis clear failed for privacy_request_id={} status={}: {}",
                    pr_id,
                    current.value,
                    exc,
                )

        last_id = batch_rows[-1][0]

        if batch_sleep > 0:
            jitter = random.uniform(0.0, batch_sleep)
            time.sleep(batch_sleep + jitter)

    duration = time.perf_counter() - started
    logger.info(
        "DSR cache sweeper finished dry_run={} rows_scanned={} "
        "redis_clear_attempts={} skipped_status_mismatch={} redis_errors={} "
        "keys_deleted_estimate={} duration_s={:.3f}",
        dry_run,
        rows_scanned,
        redis_clear_attempts,
        rows_skipped_status_mismatch,
        redis_errors,
        keys_deleted_estimate,
        duration,
    )
    return DsrCacheSweeperResult(
        rows_scanned=rows_scanned,
        redis_clear_attempts=redis_clear_attempts,
        rows_skipped_status_mismatch=rows_skipped_status_mismatch,
        redis_errors=redis_errors,
        keys_deleted_estimate=keys_deleted_estimate,
        duration_seconds=duration,
        dry_run=dry_run,
    )

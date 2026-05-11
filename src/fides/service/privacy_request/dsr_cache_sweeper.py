"""Periodic DSR cache sweeper: clears Redis cache keys for terminal privacy requests.

Eligible rows are selected from Postgres by terminal status and staleness on
``updated_at``, including soft-deleted requests (``deleted_at`` set). Rows
returned by the paginated query are treated as eligible without a second
per-row status read.

**Single-pass mode (default):** eligible string IDs are staged in a Redis set
with a TTL, the keyspace is scanned once in bounded chunks, and keys matching
known DSR shapes for staged IDs are UNLINKed in batches. The staging set is removed with Redis DEL on success; TTL covers crashed workers.

**Legacy mode:** ``single_pass_redis_sweep=false`` restores per-id
``get_dsr_cache_store(id).clear()`` (two wide SCANs per id).

The Celery entrypoint gates on resolved ``execution.dsr_cache_sweeper.enabled``.
Tuning lives under ``execution.dsr_cache_sweeper`` (``DsrCacheSweeperSettings``).
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, FrozenSet, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import (
    ACTIVE_REQUEST_STATUSES,
    PrivacyRequestStatus,
)
from fides.api.util.cache import get_dsr_cache_store, get_redis_cache_manager
from fides.common.cache.dsr_store import (
    candidate_privacy_request_ids_for_sweep,
    decode_dsr_redis_key,
    redis_key_is_dsr_cache_key_for_id,
)
from fides.config import CONFIG


@dataclass(frozen=True)
class DsrCacheSweeperResult:
    """Summary of one sweeper run."""

    rows_scanned: int
    eligible_dsr_count: int
    redis_keys_scanned: int
    dsr_ids_seen_in_redis: int
    redis_keys_deleted: int
    redis_delete_errors: int
    redis_errors: int  # legacy clear failures + single-pass batch failures (aggregated)
    duration_seconds: float
    maintenance_set_deleted: bool

    @property
    def redis_clear_attempts(self) -> int:
        """Back-compat alias for ``redis_keys_deleted``."""
        return self.redis_keys_deleted


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


def _run_dsr_cache_sweeper_legacy(
    db: Session,
    *,
    terminal_statuses: FrozenSet[PrivacyRequestStatus],
    staleness_minutes: int,
    batch_size: int,
    batch_sleep: float,
) -> DsrCacheSweeperResult:
    """Previous behavior: per-id ``clear()`` with two SCANs each."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=staleness_minutes)

    rows_scanned = 0
    redis_errors = 0
    redis_keys_deleted = 0
    last_id = ""
    db_phase_started = time.perf_counter()
    db_page_index = 0

    while True:
        page_started = time.perf_counter()
        cleared_before_page = redis_keys_deleted
        batch_rows = (
            db.query(PrivacyRequest.id, PrivacyRequest.status)
            .filter(
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

        for pr_id, status in batch_rows:
            rows_scanned += 1

            store = get_dsr_cache_store(str(pr_id))
            try:
                store.clear()
                redis_keys_deleted += 1
                logger.info(
                    "Cleared Redis DSR cache privacy_request_id={} status={} "
                    "staleness_minutes={}",
                    pr_id,
                    status.value,
                    staleness_minutes,
                )
            except Exception as exc:  # noqa: BLE001
                redis_errors += 1
                logger.warning(
                    "Redis clear failed for privacy_request_id={} status={}: {}",
                    pr_id,
                    status.value,
                    exc,
                )

        last_id = batch_rows[-1][0]
        page_duration_s = time.perf_counter() - page_started
        clears_in_page = redis_keys_deleted - cleared_before_page
        logger.info(
            "DSR cache sweeper DB page (legacy) page_index={} rows_in_page={} "
            "redis_clear_attempts_in_page={} page_duration_s={:.3f} "
            "cumulative_rows_scanned={} cumulative_redis_clears={}",
            db_page_index,
            len(batch_rows),
            clears_in_page,
            page_duration_s,
            rows_scanned,
            redis_keys_deleted,
        )
        db_page_index += 1

        if batch_sleep > 0:
            jitter = random.uniform(0.0, batch_sleep)
            time.sleep(batch_sleep + jitter)

    logger.info(
        "DSR cache sweeper DB phase complete (legacy) pages={} rows_scanned={} "
        "redis_clears={} db_phase_duration_s={:.3f}",
        db_page_index,
        rows_scanned,
        redis_keys_deleted,
        time.perf_counter() - db_phase_started,
    )

    return DsrCacheSweeperResult(
        rows_scanned=rows_scanned,
        eligible_dsr_count=redis_keys_deleted,  # best-effort legacy: one clear per eligible row
        redis_keys_scanned=0,
        dsr_ids_seen_in_redis=redis_keys_deleted,
        redis_keys_deleted=redis_keys_deleted,
        redis_delete_errors=0,
        redis_errors=redis_errors,
        duration_seconds=0.0,
        maintenance_set_deleted=True,
    )


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

    started = time.perf_counter()

    if not tc.single_pass_redis_sweep:
        res = _run_dsr_cache_sweeper_legacy(
            db,
            terminal_statuses=terminal_statuses,
            staleness_minutes=staleness_minutes,
            batch_size=batch_size,
            batch_sleep=batch_sleep,
        )
        duration = time.perf_counter() - started
        logger.info(
            "DSR cache sweeper (legacy) finished rows_scanned={} "
            "redis_keys_deleted={} redis_errors={} "
            "duration_s={:.3f}",
            res.rows_scanned,
            res.redis_keys_deleted,
            res.redis_errors,
            duration,
        )
        return DsrCacheSweeperResult(
            rows_scanned=res.rows_scanned,
            eligible_dsr_count=res.eligible_dsr_count,
            redis_keys_scanned=0,
            dsr_ids_seen_in_redis=res.dsr_ids_seen_in_redis,
            redis_keys_deleted=res.redis_keys_deleted,
            redis_delete_errors=0,
            redis_errors=res.redis_errors,
            duration_seconds=duration,
            maintenance_set_deleted=True,
        )

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=staleness_minutes)

    set_key = tc.maintenance_set_key
    ttl = int(tc.maintenance_set_ttl_seconds)
    scan_count = int(tc.redis_scan_count)
    del_batch = max(1, int(tc.redis_delete_batch_size))

    manager = get_redis_cache_manager()
    redis = manager._redis
    redis.delete(set_key)
    staging_expire_applied = False
    total_staged_members = 0
    staging_first_sadd_s: Optional[float] = None
    staging_last_sadd_end_s: Optional[float] = None

    rows_scanned = 0
    last_id = ""
    db_phase_started = time.perf_counter()
    db_page_index = 0

    while True:
        page_started = time.perf_counter()
        batch_rows = (
            db.query(PrivacyRequest.id, PrivacyRequest.status)
            .filter(
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

        page_eligible = [str(pr_id).lower() for pr_id, _ in batch_rows]
        rows_scanned += len(batch_rows)

        last_id = batch_rows[-1][0]
        page_duration_s = time.perf_counter() - page_started
        eligible_added_in_page = len(page_eligible)

        if page_eligible:
            sadd_started = time.perf_counter()
            if staging_first_sadd_s is None:
                staging_first_sadd_s = sadd_started
            redis.sadd_members_chunked(set_key, page_eligible)
            if not staging_expire_applied:
                redis.expire(set_key, ttl)
                staging_expire_applied = True
            sadd_duration_s = time.perf_counter() - sadd_started
            staging_last_sadd_end_s = time.perf_counter()
            total_staged_members += len(page_eligible)
            set_member_count = int(redis.scard(set_key))
            logger.info(
                "DSR cache sweeper Redis staging SADD batch page_index={} members_added={} "
                "sadd_duration_s={:.3f} set_member_count={} ttl_seconds={} ttl_applied={}",
                db_page_index,
                len(page_eligible),
                sadd_duration_s,
                set_member_count,
                ttl,
                staging_expire_applied,
            )

        logger.info(
            "DSR cache sweeper DB page (single-pass staging) page_index={} rows_in_page={} "
            "eligible_added_in_page={} page_duration_s={:.3f} cumulative_rows_scanned={} "
            "cumulative_staged_members={}",
            db_page_index,
            len(batch_rows),
            eligible_added_in_page,
            page_duration_s,
            rows_scanned,
            total_staged_members,
        )
        db_page_index += 1

        if batch_sleep > 0:
            jitter = random.uniform(0.0, batch_sleep)
            time.sleep(batch_sleep + jitter)

    db_phase_duration_s = time.perf_counter() - db_phase_started
    eligible_dsr_count = int(redis.scard(set_key))
    staging_duration_s = (
        (staging_last_sadd_end_s - staging_first_sadd_s)
        if staging_first_sadd_s is not None and staging_last_sadd_end_s is not None
        else 0.0
    )
    logger.info(
        "DSR cache sweeper DB phase complete (single-pass staging) pages={} "
        "eligible_dsr_count={} rows_scanned={} "
        "db_phase_duration_s={:.3f} redis_staging_stream_s={:.3f}",
        db_page_index,
        eligible_dsr_count,
        rows_scanned,
        db_phase_duration_s,
        staging_duration_s,
    )
    redis_keys_scanned = 0
    dsr_ids_touched: set[str] = set()
    redis_keys_deleted = 0
    redis_delete_errors = 0
    redis_errors = 0
    maintenance_set_deleted = False

    duration = time.perf_counter() - started

    if eligible_dsr_count == 0:
        logger.info(
            "DSR cache sweeper finished eligible_dsr_count=0 rows_scanned={} "
            "redis_keys_scanned=0 redis_keys_deleted=0 "
            "duration_s={:.3f} db_phase_duration_s={:.3f} maintenance_set_deleted=n/a",
            rows_scanned,
            duration,
            db_phase_duration_s,
        )
        return DsrCacheSweeperResult(
            rows_scanned=rows_scanned,
            eligible_dsr_count=0,
            redis_keys_scanned=0,
            dsr_ids_seen_in_redis=0,
            redis_keys_deleted=0,
            redis_delete_errors=0,
            redis_errors=0,
            duration_seconds=duration,
            maintenance_set_deleted=True,
        )

    scan_phase_duration_s = 0.0
    sweep_started = time.perf_counter()
    try:
        logger.info(
            "DSR cache sweeper starting Redis SCAN set_key={} eligible_dsr_count={} "
            "staging_duration_s={:.3f} ttl_seconds={} redis_scan_count={}",
            set_key,
            eligible_dsr_count,
            staging_duration_s,
            ttl,
            scan_count,
        )

        pending_delete: list[str] = []

        def flush_pending() -> None:
            nonlocal redis_keys_deleted, redis_delete_errors, redis_errors
            if not pending_delete:
                return
            chunk = pending_delete[:]
            pending_delete.clear()
            deleted, err = redis.unlink_many(chunk)
            redis_keys_deleted += deleted
            if err:
                redis_delete_errors += err
                redis_errors += err

        scan_started = time.perf_counter()
        scan_chunk_index = 0
        for key_batch in redis.iter_scan_batches(count=scan_count):
            chunk_started = time.perf_counter()
            keys_in_chunk = len(key_batch)

            keyed: list[tuple[str, list[str]]] = []
            for raw_key in key_batch:
                redis_keys_scanned += 1
                key_str = decode_dsr_redis_key(raw_key)
                candidates = candidate_privacy_request_ids_for_sweep(key_str)
                if candidates:
                    keyed.append((key_str, sorted(candidates)))

            present_rows: list[Any] = []
            if keyed:
                try:
                    pipe = redis.pipeline(transaction=False)
                    for _key_str, cand_list in keyed:
                        pipe.smismember(set_key, *cand_list)
                    present_rows = pipe.execute()
                    if len(present_rows) != len(keyed):
                        raise ValueError(
                            "SMISMEMBER pipeline length mismatch: "
                            f"expected {len(keyed)}, got {len(present_rows)}"
                        )
                except Exception:  # noqa: BLE001
                    present_rows = []
                    for _key_str, cand_list in keyed:
                        try:
                            present_rows.append(redis.smismember(set_key, *cand_list))
                        except Exception:  # noqa: BLE001
                            redis_errors += 1
                            present_rows.append(None)

            for (key_str, cand_list), present in zip(keyed, present_rows):
                if present is None:
                    continue
                if isinstance(present, Exception):
                    redis_errors += 1
                    continue
                delete_this_key = False
                matched_id: Optional[str] = None
                for uid, is_member in zip(cand_list, present):
                    if not is_member:
                        continue
                    if redis_key_is_dsr_cache_key_for_id(key_str, uid):
                        delete_this_key = True
                        matched_id = uid
                        break
                if delete_this_key and matched_id is not None:
                    dsr_ids_touched.add(matched_id)
                    pending_delete.append(key_str)
                    if len(pending_delete) >= del_batch:
                        flush_pending()

            chunk_duration_s = time.perf_counter() - chunk_started
            logger.info(
                "DSR cache sweeper Redis SCAN chunk chunk_index={} keys_in_chunk={} "
                "chunk_duration_s={:.3f} cumulative_keys_scanned={} pending_delete_queue={} "
                "redis_keys_deleted_so_far={}",
                scan_chunk_index,
                keys_in_chunk,
                chunk_duration_s,
                redis_keys_scanned,
                len(pending_delete),
                redis_keys_deleted,
            )
            scan_chunk_index += 1

        flush_pending()
        scan_phase_duration_s = time.perf_counter() - scan_started
        logger.info(
            "DSR cache sweeper Redis SCAN phase complete scan_chunks={} "
            "redis_keys_scanned={} redis_keys_deleted={} dsr_ids_seen_in_redis={} "
            "scan_phase_duration_s={:.3f}",
            scan_chunk_index,
            redis_keys_scanned,
            redis_keys_deleted,
            len(dsr_ids_touched),
            scan_phase_duration_s,
        )

        redis.delete(set_key)
        maintenance_set_deleted = True
    except Exception as exc:  # noqa: BLE001
        redis_errors += 1
        logger.warning(
            "DSR cache sweeper single-pass error (maintenance set TTL will expire): {}",
            exc,
        )
    finally:
        sweep_duration = time.perf_counter() - sweep_started
        total_duration = time.perf_counter() - started

    logger.info(
        "DSR cache sweeper finished eligible_dsr_count={} rows_scanned={} "
        "redis_keys_scanned={} dsr_ids_seen_in_redis={} "
        "redis_keys_deleted={} redis_delete_errors={} redis_errors={} "
        "duration_s={:.3f} sweep_s={:.3f} db_phase_duration_s={:.3f} "
        "redis_staging_duration_s={:.3f} redis_scan_phase_duration_s={:.3f} "
        "maintenance_set_deleted={}",
        eligible_dsr_count,
        rows_scanned,
        redis_keys_scanned,
        len(dsr_ids_touched),
        redis_keys_deleted,
        redis_delete_errors,
        redis_errors,
        total_duration,
        sweep_duration,
        db_phase_duration_s,
        staging_duration_s,
        scan_phase_duration_s,
        maintenance_set_deleted,
    )

    return DsrCacheSweeperResult(
        rows_scanned=rows_scanned,
        eligible_dsr_count=eligible_dsr_count,
        redis_keys_scanned=redis_keys_scanned,
        dsr_ids_seen_in_redis=len(dsr_ids_touched),
        redis_keys_deleted=redis_keys_deleted,
        redis_delete_errors=redis_delete_errors,
        redis_errors=redis_errors,
        duration_seconds=total_duration,
        maintenance_set_deleted=maintenance_set_deleted,
    )

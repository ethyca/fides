"""One-shot migration of legacy DSR Redis keys into Postgres ``DSRStore`` columns."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.db.session import get_db_session
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.util.cache import (
    get_async_task_tracking_cache_key,
    get_cache,
    get_encryption_cache_key,
    get_privacy_request_retry_cache_key,
)
from fides.config import get_config
from lethe.migration.redis_reader import (
    discover_privacy_request_ids,
    load_drp_attrs_from_redis,
    read_string,
)
from lethe.state import DSRStore


@dataclass
class DsrRedisMigrationResult:
    """Summary of a ``migrate-dsr-redis`` run."""

    privacy_request_ids: int
    updated: int
    skipped: int
    missing_row: int
    errors: List[str]


@dataclass
class _LegacySnapshot:
    encryption_key: Optional[str] = None
    drp_attrs: Optional[dict] = None
    celery_task_id: Optional[str] = None
    retry_count: Optional[int] = None


def _read_legacy_snapshot(redis: object, pr_id: str) -> _LegacySnapshot:
    snap = _LegacySnapshot()
    enc_key = get_encryption_cache_key(pr_id, encryption_attr="key")
    snap.encryption_key = read_string(redis, enc_key)
    dsr_enc = read_string(redis, f"dsr:{pr_id}:encryption:key")
    if dsr_enc:
        snap.encryption_key = dsr_enc

    snap.celery_task_id = read_string(redis, get_async_task_tracking_cache_key(pr_id))
    raw_retry = read_string(redis, get_privacy_request_retry_cache_key(pr_id))
    if raw_retry is not None:
        try:
            snap.retry_count = int(raw_retry)
        except ValueError:
            snap.retry_count = None

    drp = load_drp_attrs_from_redis(redis, pr_id)
    if drp:
        snap.drp_attrs = drp
    return snap


def _snapshot_empty(snap: _LegacySnapshot) -> bool:
    return (
        not snap.encryption_key
        and not snap.drp_attrs
        and not snap.celery_task_id
        and snap.retry_count is None
    )


def _apply_snapshot(
    db: Session,
    pr_id: str,
    snap: _LegacySnapshot,
    *,
    force: bool,
    dry_run: bool,
) -> bool:
    store = DSRStore(db, pr_id)
    pr = db.get(PrivacyRequest, pr_id)
    assert pr is not None
    changed = False

    if snap.encryption_key and (force or not pr.encryption_key):
        if dry_run:
            logger.info("[dry-run] Would set encryption key for {}", pr_id)
        else:
            store.write_encryption("key", snap.encryption_key, expire_seconds=86400)
        changed = True

    if snap.drp_attrs and (force or not pr.drp_request_body):
        if dry_run:
            logger.info("[dry-run] Would merge DRP attrs for {}: keys={}", pr_id, snap.drp_attrs.keys())
        else:
            store.merge_drp_request_body(snap.drp_attrs, expire_seconds=86400)
        changed = True

    if snap.celery_task_id and (force or not pr.celery_task_id):
        if dry_run:
            logger.info("[dry-run] Would set celery_task_id for {}", pr_id)
        else:
            store.write_async_execution(snap.celery_task_id, expire_seconds=86400)
        changed = True

    if snap.retry_count is not None and (force or not pr.requeue_retry_count):
        if dry_run:
            logger.info("[dry-run] Would set retry count for {}", pr_id)
        else:
            store.write_retry_count(str(snap.retry_count), expire_seconds=86400)
        changed = True

    return changed


def migrate_dsr_redis_to_postgres(
    *,
    dry_run: bool = False,
    force: bool = False,
    limit: Optional[int] = None,
) -> DsrRedisMigrationResult:
    """
    Copy legacy DSR Redis values onto ``PrivacyRequest`` rows via ``DSRStore``.

    Only fills empty columns unless ``force`` is True (then overwrites from Redis
    when a Redis value exists). Identity and masking-secret keys are not migrated
    here (identities live in relational tables; masking secrets may remain in Redis).
    """
    config = get_config()
    redis_wrapper = get_cache()
    redis = redis_wrapper._client  # noqa: SLF001 — SCAN on underlying client

    ids = sorted(discover_privacy_request_ids(redis))
    if limit is not None:
        ids = ids[: max(0, limit)]

    errors: List[str] = []
    updated = 0
    skipped = 0
    missing_row = 0

    SessionLocal = get_db_session(config)
    with closing(SessionLocal()) as db:
        for pr_id in ids:
            try:
                snap = _read_legacy_snapshot(redis, pr_id)
                if _snapshot_empty(snap):
                    skipped += 1
                    continue

                pr = db.get(PrivacyRequest, pr_id)
                if pr is None:
                    missing_row += 1
                    continue

                changed = _apply_snapshot(db, pr_id, snap, force=force, dry_run=dry_run)
                if changed and not dry_run:
                    db.commit()
                    updated += 1
                elif changed and dry_run:
                    updated += 1
                else:
                    skipped += 1
            except Exception as exc:  # noqa: BLE001
                msg = f"{pr_id}: {exc}"
                logger.exception("DSR Redis migration failed for {}", pr_id)
                errors.append(msg)
                db.rollback()

    return DsrRedisMigrationResult(
        privacy_request_ids=len(ids),
        updated=updated,
        skipped=skipped,
        missing_row=missing_row,
        errors=errors,
    )

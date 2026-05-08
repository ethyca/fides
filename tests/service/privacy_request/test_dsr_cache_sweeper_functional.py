"""Functional tests for DSR cache sweeper (real Redis + Postgres).

Uses the live ``get_cache()`` connection like other integration-style tests (via the
session ``cache`` fixture).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.util.cache import get_cache, get_dsr_cache_store
from fides.config import CONFIG
from fides.service.privacy_request import dsr_cache_sweeper as sweeper_module
from fides.service.privacy_request.dsr_cache_sweeper import run_dsr_cache_sweeper
from tests.fixtures.application_fixtures import _create_privacy_request_for_policy

_TTL = 3600


def _patch_dsr_cache_sweeper_execution(
    monkeypatch: pytest.MonkeyPatch, **overrides: Any
) -> None:
    nested_updates: dict[str, Any] = {
        "batch_sleep_seconds": 0.0,
        "staleness_minutes": 30,
        "batch_size": 50,
    }
    nested_updates.update(overrides)
    tc = CONFIG.execution.dsr_cache_sweeper.model_copy(update=nested_updates)
    execution = CONFIG.execution.model_copy(update={"dsr_cache_sweeper": tc})
    monkeypatch.setattr(sweeper_module, "CONFIG", SimpleNamespace(execution=execution))


def _force_stale_updated_at(db: Session, privacy_request_id: str) -> None:
    stale = datetime.now(timezone.utc) - timedelta(hours=2)
    db.execute(
        update(PrivacyRequest)
        .where(PrivacyRequest.id == privacy_request_id)
        .values(updated_at=stale)
    )
    db.commit()


@pytest.mark.integration
@pytest.mark.integration_postgres
@pytest.mark.usefixtures("cache")
class TestDsrCacheSweeperFunctional:
    def test_clears_real_redis_keys_for_stale_terminal_request(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Eligible terminal PR with stale updated_at triggers clear(); Redis keys removed."""
        _patch_dsr_cache_sweeper_execution(monkeypatch)

        pr = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.complete,
        )
        try:
            _force_stale_updated_at(db, pr.id)

            store = get_dsr_cache_store(pr.id)
            store.write_async_execution(b"task-under-test", _TTL)
            assert len(store.get_all_keys()) >= 1

            result = run_dsr_cache_sweeper(db)

            assert result.rows_scanned >= 1
            assert result.eligible_dsr_count >= 1
            assert result.redis_clear_attempts >= 1
            assert result.redis_keys_deleted >= 1
            assert result.redis_errors == 0
            assert len(get_dsr_cache_store(pr.id).get_all_keys()) == 0
            r = get_cache()
            assert not r.exists(CONFIG.execution.dsr_cache_sweeper.maintenance_set_key)
        finally:
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

    def test_clears_redis_for_soft_deleted_stale_terminal_request(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Soft-deleted terminal PR with stale updated_at is still swept."""
        _patch_dsr_cache_sweeper_execution(monkeypatch)

        pr = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.complete,
        )
        try:
            store = get_dsr_cache_store(pr.id)
            store.write_async_execution(b"soft-deleted-task", _TTL)
            assert len(store.get_all_keys()) >= 1

            pr.soft_delete(db, user_id=None)
            _force_stale_updated_at(db, pr.id)

            result = run_dsr_cache_sweeper(db)

            assert result.rows_scanned >= 1
            assert result.eligible_dsr_count >= 1
            assert result.redis_clear_attempts >= 1
            assert result.redis_keys_deleted >= 1
            assert result.redis_errors == 0
            assert len(get_dsr_cache_store(pr.id).get_all_keys()) == 0
            r = get_cache()
            assert not r.exists(CONFIG.execution.dsr_cache_sweeper.maintenance_set_key)
        finally:
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

    def test_recent_terminal_request_is_not_cleaned(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """updated_at within staleness window should not be selected."""
        _patch_dsr_cache_sweeper_execution(monkeypatch)

        pr = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.complete,
        )
        try:
            store = get_dsr_cache_store(pr.id)
            store.write_async_execution(b"recent-task", _TTL)
            keys_before = len(store.get_all_keys())

            result = run_dsr_cache_sweeper(db)

            assert result.rows_scanned == 0
            assert result.eligible_dsr_count == 0
            assert result.redis_keys_deleted == 0
            assert len(store.get_all_keys()) == keys_before
        finally:
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

    def test_non_terminal_request_not_selected_even_if_stale(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _patch_dsr_cache_sweeper_execution(monkeypatch)

        pr = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.in_processing,
        )
        try:
            _force_stale_updated_at(db, pr.id)

            store = get_dsr_cache_store(pr.id)
            store.write_async_execution(b"active-task", _TTL)
            keys_before = len(store.get_all_keys())

            result = run_dsr_cache_sweeper(db)

            assert result.rows_scanned == 0
            assert result.eligible_dsr_count == 0
            assert result.redis_keys_deleted == 0
            assert len(store.get_all_keys()) == keys_before
        finally:
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

    def test_decoy_key_containing_eligible_uuid_not_deleted(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Keys that embed a UUID but do not match DSR key shapes must not be deleted."""
        _patch_dsr_cache_sweeper_execution(monkeypatch)

        pr = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.complete,
        )
        decoy = f"DECOY-{pr.id}-not-a-dsr-key"
        r = get_cache()
        try:
            _force_stale_updated_at(db, pr.id)

            store = get_dsr_cache_store(pr.id)
            store.write_async_execution(b"swept", _TTL)
            r.set(decoy, b"1", ex=_TTL)

            run_dsr_cache_sweeper(db)

            assert r.get(decoy) is not None
            # get_all_keys() uses SCAN match *{pr.id}*, so the decoy (which embeds the id)
            # still appears in the listing even though the sweeper correctly skips deleting it.
            keys_after = get_dsr_cache_store(pr.id).get_all_keys()
            assert decoy in keys_after
            assert not any(k.startswith(f"dsr:{pr.id}:") for k in keys_after)
        finally:
            r.delete(decoy)
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

    def test_two_privacy_requests_only_eligible_redis_is_cleared(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Stale terminal PR is swept; a stale non-terminal PR must keep its DSR cache keys."""
        _patch_dsr_cache_sweeper_execution(monkeypatch)

        pr_eligible = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.complete,
        )
        pr_other = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.in_processing,
        )
        try:
            _force_stale_updated_at(db, pr_eligible.id)
            _force_stale_updated_at(db, pr_other.id)

            store_a = get_dsr_cache_store(pr_eligible.id)
            store_b = get_dsr_cache_store(pr_other.id)
            store_a.write_async_execution(b"eligible-a", _TTL)
            store_b.write_async_execution(b"keep-b", _TTL)

            assert any(
                k.startswith(f"dsr:{pr_eligible.id}:") for k in store_a.get_all_keys()
            )
            assert any(
                k.startswith(f"dsr:{pr_other.id}:") for k in store_b.get_all_keys()
            )

            result = run_dsr_cache_sweeper(db)

            assert result.rows_scanned >= 1
            assert result.eligible_dsr_count >= 1
            keys_a = get_dsr_cache_store(pr_eligible.id).get_all_keys()
            keys_b = get_dsr_cache_store(pr_other.id).get_all_keys()
            assert not any(k.startswith(f"dsr:{pr_eligible.id}:") for k in keys_a)
            assert any(k.startswith(f"dsr:{pr_other.id}:") for k in keys_b)
        finally:
            get_dsr_cache_store(pr_eligible.id).clear()
            get_dsr_cache_store(pr_other.id).clear()
            pr_eligible.delete(db)
            pr_other.delete(db)

    def test_single_pass_deletes_en_and_legacy_id_prefixed_keys(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """SCAN path must remove encoded-object (EN_) and legacy id- keys for eligible PRs."""
        _patch_dsr_cache_sweeper_execution(monkeypatch)

        pr = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.complete,
        )
        r = get_cache()
        en_key = f"EN_DATA_USE_MAP__{pr.id}"
        legacy_key = f"id-{pr.id}-async-execution"
        try:
            _force_stale_updated_at(db, pr.id)

            get_dsr_cache_store(pr.id).write_async_execution(b"new-format", _TTL)
            r.set(en_key, b"encoded-placeholder", ex=_TTL)
            r.set(legacy_key, b"legacy-value", ex=_TTL)

            run_dsr_cache_sweeper(db)

            assert r.get(en_key) is None
            assert r.get(legacy_key) is None
            keys_after = get_dsr_cache_store(pr.id).get_all_keys()
            assert not any(k.startswith(f"dsr:{pr.id}:") for k in keys_after)
        finally:
            r.delete(en_key)
            r.delete(legacy_key)
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

    def test_single_pass_deletes_idx_set_and_migrated_keys(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Index set and migration marker keys must be removed when the PR is eligible."""
        _patch_dsr_cache_sweeper_execution(monkeypatch)

        pr = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.complete,
        )
        r = get_cache()
        idx_key = f"__idx:dsr:{pr.id}"
        mig_key = f"__migrated:{pr.id}"
        try:
            _force_stale_updated_at(db, pr.id)

            get_dsr_cache_store(pr.id).write_async_execution(b"dsr-value", _TTL)
            r.sadd(idx_key, "dummy-member")
            r.setex(mig_key, _TTL, "1")

            run_dsr_cache_sweeper(db)

            assert not r.exists(idx_key)
            assert not r.exists(mig_key)
            keys_after = get_dsr_cache_store(pr.id).get_all_keys()
            assert not any(k.startswith(f"dsr:{pr.id}:") for k in keys_after)
        finally:
            r.delete(idx_key)
            r.delete(mig_key)
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

    def test_legacy_single_pass_disabled_uses_clear_per_request(
        self,
        db: Session,
        policy: Policy,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Rollback toggle: legacy path still clears Redis via DSRCacheStore.clear()."""
        _patch_dsr_cache_sweeper_execution(monkeypatch, single_pass_redis_sweep=False)

        pr = _create_privacy_request_for_policy(
            db,
            policy,
            status=PrivacyRequestStatus.complete,
        )
        try:
            _force_stale_updated_at(db, pr.id)

            store = get_dsr_cache_store(pr.id)
            store.write_async_execution(b"legacy-path", _TTL)
            assert len(store.get_all_keys()) >= 1

            result = run_dsr_cache_sweeper(db)

            assert result.rows_scanned >= 1
            assert result.redis_keys_deleted >= 1
            assert result.redis_keys_scanned == 0
            assert len(get_dsr_cache_store(pr.id).get_all_keys()) == 0
        finally:
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

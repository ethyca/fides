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
from fides.api.util.cache import get_dsr_cache_store
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
            assert result.redis_clear_attempts >= 1
            assert result.redis_errors == 0
            assert len(get_dsr_cache_store(pr.id).get_all_keys()) == 0
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
            assert result.redis_clear_attempts >= 1
            assert result.redis_errors == 0
            assert len(get_dsr_cache_store(pr.id).get_all_keys()) == 0
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
            assert len(store.get_all_keys()) == keys_before
        finally:
            get_dsr_cache_store(pr.id).clear()
            pr.delete(db)

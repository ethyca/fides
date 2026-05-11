"""Postgres-backed ``DSRStore`` integration tests (DB + app fixtures).

Location: ``tests/lethe/integration/state/``. Marker: ``@pytest.mark.integration``.
"""

import uuid

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.util.cache import persist_dsr_async_task_id
from lethe.state import DSRStore
from lethe.state.models.manual_webhook_input import ManualWebhookInput


@pytest.mark.integration
class TestDSRStorePostgres:
    def test_encryption_round_trip(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.write_encryption("key", "0123456789abcdef", expire_seconds=3600)
        db.commit()
        db.refresh(privacy_request)
        assert DSRStore(db, privacy_request.id).get_encryption("key") == "0123456789abcdef"

    def test_drp_merge_and_get(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.merge_drp_request_body({"meta": {"version": "0.5"}}, expire_seconds=300)
        store.merge_drp_request_body({"regime": "ccpa"}, expire_seconds=300)
        db.commit()
        db.refresh(privacy_request)
        s2 = DSRStore(db, privacy_request.id)
        meta = s2.get_drp("meta")
        assert meta is not None
        assert '"version": "0.5"' in str(meta)
        assert s2.get_drp("regime") == "ccpa"

    def test_clear_privacy_request_state(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.write_encryption("key", "secret", expire_seconds=3600)
        store.merge_drp_request_body({"k": "v"}, expire_seconds=300)
        db.flush()
        store.clear_privacy_request_state()
        db.commit()
        db.refresh(privacy_request)
        assert privacy_request.encryption_key is None
        assert not privacy_request.drp_request_body

    def test_async_execution_privacy_request_round_trip(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.write_async_execution(b"celery-pr-bytes", expire_seconds=60)
        db.commit()
        db.refresh(privacy_request)
        assert privacy_request.celery_task_id == "celery-pr-bytes"
        assert DSRStore(db, privacy_request.id).get_async_execution() == "celery-pr-bytes"

    def test_async_execution_request_task_round_trip(self, db, request_task):
        store = DSRStore(db, request_task.id)
        store.write_async_execution("celery-rt-task", expire_seconds=60)
        db.commit()
        db.refresh(request_task)
        assert request_task.celery_task_id == "celery-rt-task"
        assert DSRStore(db, request_task.id).get_async_execution() == "celery-rt-task"

    def test_retry_count_round_trip(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.write_retry_count("4", expire_seconds=60)
        db.commit()
        db.refresh(privacy_request)
        assert privacy_request.requeue_retry_count == 4
        assert DSRStore(db, privacy_request.id).get_retry_count() == "4"

    def test_paused_and_failed_checkpoint_round_trip(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        paused_payload = {"detail": "waiting", "count": 2}
        store.write_paused_checkpoint(
            step="access",
            collection="ds:coll",
            action_needed=paused_payload,
        )
        store.write_failed_checkpoint(
            step="erasure",
            collection="ds2:coll2",
            action_needed={"error": "timeout"},
        )
        db.commit()
        db.refresh(privacy_request)
        assert privacy_request.paused_step == "access"
        assert privacy_request.paused_collection == "ds:coll"
        assert privacy_request.paused_action_needed == paused_payload
        assert privacy_request.failed_step == "erasure"
        s2 = DSRStore(db, privacy_request.id)
        assert s2.read_paused_checkpoint() == ("access", "ds:coll", paused_payload)
        step, coll, payload = s2.read_failed_checkpoint()
        assert step == "erasure"
        assert coll == "ds2:coll2"
        assert payload == {"error": "timeout"}

    def test_data_use_map_round_trip_serializes_iterables(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.write_data_use_map(
            {
                "plain": "x",
                "as_set": {"a", "b"},
                "as_list": [1, 2],
            }
        )
        db.commit()
        db.refresh(privacy_request)
        loaded = DSRStore(db, privacy_request.id).get_data_use_map()
        assert loaded is not None
        assert loaded["plain"] == "x"
        assert sorted(loaded["as_set"]) == ["a", "b"]
        assert loaded["as_list"] == [1, 2]

    def test_get_merged_drp_request_body_empty(self, db, privacy_request):
        db.refresh(privacy_request)
        assert DSRStore(db, privacy_request.id).get_merged_drp_request_body() == {}

    def test_append_email_checkpoint_filters_by_dataset(
        self, db, privacy_request, request_task
    ):
        store = DSRStore(db, privacy_request.id)
        store.append_email_checkpoint(
            request_task_id=request_task.id,
            checkpoint={
                "step": "access",
                "collection": {"dataset": "keep_ds", "name": "c1"},
                "body": "a",
            },
        )
        store.append_email_checkpoint(
            request_task_id=request_task.id,
            checkpoint={
                "step": "access",
                "collection": {"dataset": "other_ds", "name": "c2"},
                "body": "b",
            },
        )
        db.commit()
        matches = store.get_email_checkpoints_for_dataset(
            privacy_request_id=privacy_request.id,
            step="access",
            dataset="keep_ds",
        )
        assert len(matches) == 1
        assert matches[0]["body"] == "a"

    def test_get_encryption_ignores_unknown_attr(self, db, privacy_request):
        store = DSRStore(db, privacy_request.id)
        store.write_encryption("key", "sekret", expire_seconds=60)
        db.commit()
        assert store.get_encryption("not_key") is None

    def test_clear_privacy_request_state_resets_all_dsr_columns(
        self, db, privacy_request
    ):
        store = DSRStore(db, privacy_request.id)
        store.write_async_execution("task-xyz", expire_seconds=60)
        store.write_retry_count("7", expire_seconds=60)
        store.write_data_use_map({"u": "v"})
        store.write_paused_checkpoint(
            step="s1", collection="c1", action_needed={"x": 1}
        )
        store.write_failed_checkpoint(
            step="s2", collection="c2", action_needed={"y": 2}
        )
        db.flush()
        store.clear_privacy_request_state()
        db.commit()
        db.refresh(privacy_request)
        assert privacy_request.celery_task_id is None
        assert privacy_request.requeue_retry_count == 0
        assert privacy_request.data_use_map is None
        assert privacy_request.paused_step is None
        assert privacy_request.paused_collection is None
        assert privacy_request.paused_action_needed is None
        assert privacy_request.failed_step is None
        assert privacy_request.failed_collection is None
        assert privacy_request.failed_action_needed is None

    def test_clear_privacy_request_state_deletes_manual_webhook_input(
        self, db, privacy_request, access_manual_webhook
    ):
        store = DSRStore(db, privacy_request.id)
        store.upsert_manual_webhook_input(
            privacy_request_id=privacy_request.id,
            manual_webhook_id=access_manual_webhook.id,
            action_type="access",
            input_data={"email": "x@example.com"},
        )
        db.commit()
        assert (
            db.query(ManualWebhookInput)
            .filter(ManualWebhookInput.privacy_request_id == privacy_request.id)
            .count()
            == 1
        )

        store.clear_privacy_request_state()
        db.commit()

        assert (
            db.query(ManualWebhookInput)
            .filter(ManualWebhookInput.privacy_request_id == privacy_request.id)
            .count()
            == 0
        )
        assert (
            store.get_manual_webhook_input(
                privacy_request_id=privacy_request.id,
                manual_webhook_id=access_manual_webhook.id,
                action_type="access",
            )
            is None
        )

    def test_upsert_manual_webhook_input_updates_existing_row(
        self, db, privacy_request, access_manual_webhook
    ):
        store = DSRStore(db, privacy_request.id)
        store.upsert_manual_webhook_input(
            privacy_request_id=privacy_request.id,
            manual_webhook_id=access_manual_webhook.id,
            action_type="access",
            input_data={"v": 1},
        )
        db.flush()
        store.upsert_manual_webhook_input(
            privacy_request_id=privacy_request.id,
            manual_webhook_id=access_manual_webhook.id,
            action_type="access",
            input_data={"v": 2},
        )
        db.commit()
        assert (
            store.get_manual_webhook_input(
                privacy_request_id=privacy_request.id,
                manual_webhook_id=access_manual_webhook.id,
                action_type="access",
            )
            == {"v": 2}
        )
        assert (
            db.query(ManualWebhookInput)
            .filter(ManualWebhookInput.privacy_request_id == privacy_request.id)
            .count()
            == 1
        )

    def test_unknown_privacy_request_id_noops_without_error(self, db):
        missing_id = str(uuid.uuid4())
        store = DSRStore(db, missing_id)
        store.write_encryption("key", "x", expire_seconds=60)
        store.merge_drp_request_body({"a": 1}, expire_seconds=60)
        store.write_async_execution("t", expire_seconds=60)
        store.write_retry_count("1", expire_seconds=60)
        store.write_paused_checkpoint(step="s", collection="c", action_needed={})
        store.write_failed_checkpoint(step="s", collection="c", action_needed={})
        store.write_data_use_map({"k": "v"})
        store.append_email_checkpoint(
            request_task_id=str(uuid.uuid4()),
            checkpoint={"step": "access", "collection": {"dataset": "d"}},
        )
        assert store.get_async_execution() is None
        assert store.get_encryption("key") is None
        assert store.get_merged_drp_request_body() == {}
        assert store.read_paused_checkpoint() == (None, None, None)
        assert store.read_failed_checkpoint() == (None, None, None)
        assert store.get_data_use_map() is None
        assert store.get_retry_count() is None

    def test_persist_dsr_async_task_id_visible_after_separate_session_commit(
        self, db, privacy_request
    ):
        persist_dsr_async_task_id(privacy_request.id, "cross_session_task")
        db.expire_all()
        pr = db.get(PrivacyRequest, privacy_request.id)
        assert pr is not None
        assert pr.celery_task_id == "cross_session_task"

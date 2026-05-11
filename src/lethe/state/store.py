"""Postgres-backed DSR state store (replaces Redis DSRCacheStore for DSR keys)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union, cast
from uuid import uuid4

from sqlalchemy.orm import Session

from lethe.state.models.manual_webhook_input import ManualWebhookInput


class DSRStore:
    """Read/write facade for DSR state scoped to a privacy request id or request task id."""

    def __init__(self, db: Session, dsr_id: str) -> None:
        self._db = db
        self._dsr_id = dsr_id

    def _flush(self) -> None:
        self._db.flush()

    def _privacy_request(self):  # type: ignore[no-untyped-def]
        from fides.api.models.privacy_request.privacy_request import PrivacyRequest

        return self._db.get(PrivacyRequest, self._dsr_id)

    def _request_task(self):  # type: ignore[no-untyped-def]
        from fides.api.models.privacy_request.request_task import RequestTask

        return self._db.get(RequestTask, self._dsr_id)

    # --- Async execution (privacy request or request task row) ---

    def write_async_execution(
        self, value: Union[str, bytes], expire_seconds: int  # noqa: ARG002
    ) -> None:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        pr = self._privacy_request()
        if pr is not None:
            pr.celery_task_id = cast(str, value)
            self._flush()
            return
        rt = self._request_task()
        if rt is not None:
            rt.celery_task_id = cast(str, value)
            self._flush()
            return

    def get_async_execution(self) -> Optional[Union[str, bytes]]:
        pr = self._privacy_request()
        if pr is not None and pr.celery_task_id:
            return pr.celery_task_id
        rt = self._request_task()
        if rt is not None and rt.celery_task_id:
            return rt.celery_task_id
        return None

    # --- Encryption / DRP (privacy request only) ---

    def write_encryption(
        self, attr: str, value: Union[str, bytes], expire_seconds: int  # noqa: ARG002
    ) -> None:
        pr = self._privacy_request()
        if pr is None:
            return
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if attr == "key":
            pr.encryption_key = cast(str, value)
        self._flush()

    def get_encryption(self, attr: str) -> Optional[Union[str, bytes]]:
        pr = self._privacy_request()
        if pr is None or attr != "key":
            return None
        return pr.encryption_key

    def merge_drp_request_body(
        self, drp_body: Dict[str, Any], expire_seconds: int  # noqa: ARG002
    ) -> None:
        pr = self._privacy_request()
        if pr is None:
            return
        merged = dict(pr.drp_request_body or {})
        merged.update(drp_body)
        pr.drp_request_body = merged
        self._flush()

    def get_drp(self, attr: str) -> Optional[Union[str, bytes]]:
        pr = self._privacy_request()
        if pr is None or not pr.drp_request_body:
            return None
        val = pr.drp_request_body.get(attr)
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return cast(Union[str, bytes], val)

    def get_merged_drp_request_body(self) -> Dict[str, Any]:
        pr = self._privacy_request()
        if not pr or not pr.drp_request_body:
            return {}
        return dict(pr.drp_request_body)

    # --- Retry count (privacy request only) ---

    def write_retry_count(
        self, value: Union[str, bytes], expire_seconds: int  # noqa: ARG002
    ) -> None:
        pr = self._privacy_request()
        if pr is None:
            return
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        pr.requeue_retry_count = int(value)
        self._flush()

    def get_retry_count(self) -> Optional[Union[str, bytes]]:
        pr = self._privacy_request()
        if pr is None:
            return None
        return str(pr.requeue_retry_count)

    # --- Paused / failed checkpoint (privacy request only) ---

    def write_paused_checkpoint(
        self,
        *,
        step: Optional[str],
        collection: Optional[str],
        action_needed: Any,
    ) -> None:
        pr = self._privacy_request()
        if pr is None:
            return
        pr.paused_step = step
        pr.paused_collection = collection
        pr.paused_action_needed = action_needed
        self._flush()

    def write_failed_checkpoint(
        self,
        *,
        step: Optional[str],
        collection: Optional[str],
        action_needed: Any,
    ) -> None:
        pr = self._privacy_request()
        if pr is None:
            return
        pr.failed_step = step
        pr.failed_collection = collection
        pr.failed_action_needed = action_needed
        self._flush()

    def read_paused_checkpoint(self) -> tuple[
        Optional[str], Optional[str], Any
    ]:
        pr = self._privacy_request()
        if pr is None:
            return None, None, None
        return pr.paused_step, pr.paused_collection, pr.paused_action_needed

    def read_failed_checkpoint(self) -> tuple[
        Optional[str], Optional[str], Any
    ]:
        pr = self._privacy_request()
        if pr is None:
            return None, None, None
        return pr.failed_step, pr.failed_collection, pr.failed_action_needed

    # --- Data use map snapshot (privacy request only) ---

    def write_data_use_map(self, value: Dict[str, Any]) -> None:
        pr = self._privacy_request()
        if pr is None:
            return
        serializable: Dict[str, Any] = {
            k: (list(v) if hasattr(v, "__iter__") and not isinstance(v, (str, bytes, dict)) else v)
            for k, v in value.items()
        }
        pr.data_use_map = serializable
        self._flush()

    def get_data_use_map(self) -> Optional[Dict[str, Any]]:
        pr = self._privacy_request()
        if pr is None or not pr.data_use_map:
            return None
        return dict(pr.data_use_map)

    # --- Email connector checkpoints (request task JSON list) ---

    def append_email_checkpoint(
        self,
        *,
        request_task_id: str,
        checkpoint: Dict[str, Any],
    ) -> None:
        from fides.api.models.privacy_request.request_task import RequestTask

        rt = self._db.get(RequestTask, request_task_id)
        if rt is None:
            return
        checkpoints: List[Dict[str, Any]] = list(rt.email_checkpoints or [])
        checkpoints.append(checkpoint)
        rt.email_checkpoints = checkpoints
        self._flush()

    def get_email_checkpoints_for_dataset(
        self, *, privacy_request_id: str, step: str, dataset: str
    ) -> List[Dict[str, Any]]:
        from fides.api.models.privacy_request.request_task import RequestTask

        rts = (
            self._db.query(RequestTask)
            .filter(RequestTask.privacy_request_id == privacy_request_id)
            .all()
        )
        out: List[Dict[str, Any]] = []
        for rt in rts:
            for entry in rt.email_checkpoints or []:
                coll = entry.get("collection") or {}
                if entry.get("step") == step and coll.get("dataset") == dataset:
                    out.append(entry)
        return out

    # --- Manual webhook input ---

    def upsert_manual_webhook_input(
        self,
        *,
        privacy_request_id: str,
        manual_webhook_id: str,
        action_type: str,
        input_data: Dict[str, Any],
    ) -> None:
        row = (
            self._db.query(ManualWebhookInput)
            .filter(
                ManualWebhookInput.privacy_request_id == privacy_request_id,
                ManualWebhookInput.manual_webhook_id == manual_webhook_id,
                ManualWebhookInput.action_type == action_type,
            )
            .first()
        )
        if row:
            row.input_data = input_data
        else:
            self._db.add(
                ManualWebhookInput(
                    id=f"mwi_{uuid4()}",
                    privacy_request_id=privacy_request_id,
                    manual_webhook_id=manual_webhook_id,
                    action_type=action_type,
                    input_data=input_data,
                )
            )
        self._flush()

    def get_manual_webhook_input(
        self,
        *,
        privacy_request_id: str,
        manual_webhook_id: str,
        action_type: str,
    ) -> Optional[Dict[str, Any]]:
        row = (
            self._db.query(ManualWebhookInput)
            .filter(
                ManualWebhookInput.privacy_request_id == privacy_request_id,
                ManualWebhookInput.manual_webhook_id == manual_webhook_id,
                ManualWebhookInput.action_type == action_type,
            )
            .first()
        )
        if row is None:
            return None
        data = row.input_data
        if isinstance(data, dict):
            return data
        return None

    def clear_privacy_request_state(self) -> None:
        """Clear Postgres-backed cache fields for this privacy request id."""
        pr = self._privacy_request()
        if pr is None:
            return
        pr.encryption_key = None
        pr.drp_request_body = None
        pr.data_use_map = None
        pr.paused_step = None
        pr.paused_collection = None
        pr.paused_action_needed = None
        pr.failed_step = None
        pr.failed_collection = None
        pr.failed_action_needed = None
        pr.celery_task_id = None
        pr.requeue_retry_count = 0
        self._db.query(ManualWebhookInput).filter(
            ManualWebhookInput.privacy_request_id == pr.id
        ).delete(synchronize_session=False)
        self._flush()

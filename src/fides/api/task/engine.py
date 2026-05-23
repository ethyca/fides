from __future__ import annotations

from typing import Any, Optional, Protocol

from fides.config import CONFIG


class DSREngine(Protocol):
    """Abstraction over DSR execution backends (Celery, Temporal)."""

    def dispatch_privacy_request(
        self,
        privacy_request_id: str,
        from_webhook_id: Optional[str] = None,
        from_step: Optional[str] = None,
    ) -> Optional[str]:
        """Start or resume a privacy request. Returns an engine-specific run ID."""
        ...

    def dispatch_request_task(
        self,
        request_task_id: str,
        privacy_request_id: str,
        action_type: str,
        privacy_request_proceed: bool = True,
    ) -> None:
        """Queue an individual collection task."""
        ...

    def signal_task_complete(
        self,
        privacy_request_id: str,
        collection_address: str,
        data: Optional[dict[str, Any]] = None,
    ) -> None:
        """Signal that a manual or callback task has received external input."""
        ...


def get_dsr_engine() -> DSREngine:
    """Return the appropriate DSR engine based on config."""
    if CONFIG.execution.use_temporal_workflow_engine:
        from fides.api.task.temporal.engine import TemporalDSREngine

        return TemporalDSREngine()

    from fides.api.task.celery_engine import CeleryDSREngine

    return CeleryDSREngine()

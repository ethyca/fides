from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import CurrentStep
from fides.api.service.privacy_request.manual_webhook_service import (
    ManualWebhookResults,
)


@dataclass
class PipelineContext:
    """Mutable state carried through all pipeline steps.

    Pre-populated by the Celery task wrapper; optional fields are filled
    incrementally as steps execute.
    """

    session: Session
    privacy_request: PrivacyRequest
    policy: Policy
    resume_step: Optional[CurrentStep]
    from_webhook_id: Optional[str] = None

    # Populated by GraphConstructionStep
    datasets: Optional[list[DatasetConfig]] = None
    dataset_graph: Optional[DatasetGraph] = None
    identity_data: Optional[dict[str, Any]] = None
    connection_configs: Optional[list[ConnectionConfig]] = None
    fides_connector_datasets: Optional[set[str]] = None

    # Populated by ManualWebhooksStep
    manual_webhook_access_results: Optional[ManualWebhookResults] = None
    manual_webhook_erasure_results: Optional[ManualWebhookResults] = None

    # Populated by UploadAccessStep
    access_result_urls: list[str] = field(default_factory=list)

from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api import common_exceptions
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import CurrentStep
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.service.privacy_request.pipeline.orchestrator import (
    RequestPipelineOrchestrator,
)
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context
from fides.api.util.memory_watchdog import memory_limiter


@celery_app.task(base=DatabaseTask, bind=True)
@memory_limiter
@log_context(capture_args={"privacy_request_id": LoggerContextKeys.privacy_request_id})
def run_privacy_request(
    self: DatabaseTask,
    privacy_request_id: str,
    from_webhook_id: Optional[str] = None,
    from_step: Optional[str] = None,
) -> None:
    """
    Dispatch a privacy_request into the execution layer by:
        1. Generate a graph from all the currently configured datasets
        2. Take the provided identity data
        3. Start the access request / erasure request execution
        4. When finished, upload the results to the configured storage destination if applicable
    """
    resume_step: Optional[CurrentStep] = CurrentStep(from_step) if from_step else None  # type: ignore
    if from_step:
        with logger.contextualize(privacy_request_id=privacy_request_id):
            logger.info("Resuming privacy request from checkpoint: '{}'", from_step)

    with self.get_new_session() as session:
        privacy_request = _load_privacy_request(session, privacy_request_id)

        with logger.contextualize(
            privacy_request_source=(
                privacy_request.source.value if privacy_request.source else None
            ),
            privacy_request_id=privacy_request.id,
        ):
            ctx = PipelineContext(
                session=session,
                privacy_request=privacy_request,
                policy=privacy_request.policy,
                resume_step=resume_step,
                from_webhook_id=from_webhook_id,
            )
            RequestPipelineOrchestrator().run(ctx)


def _load_privacy_request(session: Session, privacy_request_id: str) -> PrivacyRequest:
    privacy_request = (
        PrivacyRequest.query_without_large_columns(session)
        .filter(PrivacyRequest.id == privacy_request_id)
        .first()
    )
    if not privacy_request:
        raise common_exceptions.PrivacyRequestNotFound(
            f"Privacy request with id {privacy_request_id} not found"
        )
    return privacy_request


# Re-exports for backward compatibility -- consumers should import from the new modules directly.
from fides.api.service.privacy_request.access_result_service import (  # noqa: E402
    save_access_results as save_access_results,
)
from fides.api.service.privacy_request.completion_notification_service import (  # noqa: E402
    initiate_paused_privacy_request_followup as initiate_paused_privacy_request_followup,
)
from fides.api.service.privacy_request.email_batch_service import (  # noqa: E402
    get_consent_email_connection_configs as get_consent_email_connection_configs,
)
from fides.api.service.privacy_request.email_batch_service import (  # noqa: E402
    get_erasure_email_connection_configs as get_erasure_email_connection_configs,
)
from fides.api.service.privacy_request.pipeline.steps.erasure import (  # noqa: E402
    _verify_masking_secrets as _verify_masking_secrets,
)
from fides.api.task.graph_task import (  # noqa: E402
    build_consent_dataset_graph as build_consent_dataset_graph,
)

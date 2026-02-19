from __future__ import annotations

from loguru import logger

from fides.api.common_exceptions import (
    PrivacyRequestPaused,
    ValidationError,
)
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.service.privacy_request.pipeline.steps.access import AccessStep
from fides.api.service.privacy_request.pipeline.steps.consent import ConsentStep
from fides.api.service.privacy_request.pipeline.steps.email_post_send import (
    EmailPostSendStep,
)
from fides.api.service.privacy_request.pipeline.steps.erasure import ErasureStep
from fides.api.service.privacy_request.pipeline.steps.finalization import (
    FinalizationStep,
)
from fides.api.service.privacy_request.pipeline.steps.finalize_erasure import (
    FinalizeErasureStep,
)
from fides.api.service.privacy_request.pipeline.steps.graph_construction import (
    GraphConstructionStep,
)
from fides.api.service.privacy_request.pipeline.steps.initialization import (
    InitializationStep,
)
from fides.api.service.privacy_request.pipeline.steps.manual_webhooks import (
    ManualWebhooksStep,
)
from fides.api.service.privacy_request.pipeline.steps.post_webhooks import (
    PostWebhooksStep,
)
from fides.api.service.privacy_request.pipeline.steps.pre_webhooks import (
    PreWebhooksStep,
)
from fides.api.service.privacy_request.pipeline.steps.upload_access import (
    UploadAccessStep,
)
from fides.api.util.logger import _log_exception, _log_warning
from fides.config import CONFIG


class RequestPipelineOrchestrator:
    def __init__(self) -> None:
        self.steps: list[PipelineStep] = [
            InitializationStep(),
            ManualWebhooksStep(),
            PreWebhooksStep(),
            GraphConstructionStep(),
            AccessStep(),
            UploadAccessStep(),
            ErasureStep(),
            FinalizeErasureStep(),
            ConsentStep(),
            EmailPostSendStep(),
            PostWebhooksStep(),
            FinalizationStep(),
        ]

    def run(self, ctx: PipelineContext) -> None:
        try:
            for step in self.steps:
                if step.should_run(ctx):
                    if step.checkpoint:
                        ctx.privacy_request.cache_failed_checkpoint_details(
                            step.checkpoint
                        )
                    result = step.execute(ctx)
                    if result == StepResult.HALT:
                        return
        except PrivacyRequestPaused as exc:
            ctx.privacy_request.pause_processing(ctx.session)
            _log_warning(exc, CONFIG.dev_mode)
        except ValidationError as exc:
            logger.error(f"Error validating dataset references: {str(exc)}")
            ctx.privacy_request.add_error_execution_log(
                ctx.session,
                connection_key=None,
                dataset_name="Dataset reference validation",
                collection_name=None,
                message=str(exc),
                action_type=ctx.privacy_request.policy.get_action_type(),  # type: ignore[arg-type]
            )
            ctx.privacy_request.error_processing(db=ctx.session)
        except BaseException as exc:  # pylint: disable=broad-except
            ctx.privacy_request.add_error_execution_log(
                ctx.session,
                connection_key=None,
                dataset_name="Privacy request processing",
                collection_name=None,
                message=str(exc),
                action_type=ctx.privacy_request.policy.get_action_type(),  # type: ignore
            )
            ctx.privacy_request.error_processing(db=ctx.session)
            _log_exception(exc, CONFIG.dev_mode)

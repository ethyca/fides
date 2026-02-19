from __future__ import annotations

from typing import Optional

from fides.api.models.policy import PolicyPreWebhook
from fides.api.schemas.policy import CurrentStep
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.service.privacy_request.webhook_execution_service import (
    run_webhooks_and_report_status,
)


class PreWebhooksStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.pre_webhooks

    def execute(self, ctx: PipelineContext) -> StepResult:
        proceed = run_webhooks_and_report_status(
            ctx.session,
            privacy_request=ctx.privacy_request,
            webhook_cls=PolicyPreWebhook,  # type: ignore
            after_webhook_id=ctx.from_webhook_id,
        )
        if not proceed:
            return StepResult.HALT
        return StepResult.CONTINUE

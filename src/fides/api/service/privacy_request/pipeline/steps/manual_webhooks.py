from __future__ import annotations

from typing import Optional

from fides.api.schemas.policy import CurrentStep
from fides.api.service.privacy_request.manual_webhook_service import (
    get_manual_webhook_access_inputs,
    get_manual_webhook_erasure_inputs,
)
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext


class ManualWebhooksStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return None

    def execute(self, ctx: PipelineContext) -> StepResult:
        ctx.manual_webhook_access_results = get_manual_webhook_access_inputs(
            ctx.session, ctx.privacy_request, ctx.policy
        )
        if not ctx.manual_webhook_access_results.proceed:
            return StepResult.HALT

        ctx.manual_webhook_erasure_results = get_manual_webhook_erasure_inputs(
            ctx.session, ctx.privacy_request, ctx.policy
        )
        if not ctx.manual_webhook_erasure_results.proceed:
            return StepResult.HALT

        return StepResult.CONTINUE

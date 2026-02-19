from __future__ import annotations

from typing import Optional

from loguru import logger

from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.service.privacy_request.email_batch_service import needs_batch_email_send
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext


class EmailPostSendStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.email_post_send

    @property
    def required_action_types(self) -> Optional[set[ActionType]]:
        return {ActionType.erasure, ActionType.consent}

    def execute(self, ctx: PipelineContext) -> StepResult:
        if needs_batch_email_send(
            ctx.session, ctx.identity_data or {}, ctx.privacy_request
        ):
            ctx.privacy_request.pause_processing_for_email_send(ctx.session)
            logger.info("Privacy request exiting: awaiting email send.")
            return StepResult.HALT
        return StepResult.CONTINUE

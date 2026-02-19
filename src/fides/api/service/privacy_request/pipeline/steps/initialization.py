from __future__ import annotations

from typing import Optional

from loguru import logger

from fides.api.schemas.policy import CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.duplication_detection import check_for_duplicates
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext


class InitializationStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return None

    def execute(self, ctx: PipelineContext) -> StepResult:
        if ctx.privacy_request.status == PrivacyRequestStatus.canceled:
            logger.info("Terminating privacy request: request canceled.")
            return StepResult.HALT

        if ctx.privacy_request.deleted_at is not None:
            logger.info("Terminating privacy request: request deleted.")
            return StepResult.HALT

        check_for_duplicates(db=ctx.session, privacy_request=ctx.privacy_request)
        if ctx.privacy_request.status == PrivacyRequestStatus.duplicate:
            return StepResult.HALT

        logger.info("Dispatching privacy request")
        ctx.privacy_request.start_processing(ctx.session)
        return StepResult.CONTINUE

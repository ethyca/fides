from __future__ import annotations

from typing import Optional

from fides.api.schemas.policy import CurrentStep
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext


class FinalizeErasureStep(PipelineStep):
    """Checkpoint placeholder so DSR 3.0 can resume after the erasure step.

    The checkpoint caching is handled by the orchestrator; the execute body
    is intentionally empty.
    """

    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.finalize_erasure

    def execute(self, ctx: PipelineContext) -> StepResult:
        return StepResult.CONTINUE

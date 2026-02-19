from __future__ import annotations

from typing import Optional

from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.task.action_strategies.registry import ACTION_STRATEGIES


class AccessStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.access

    @property
    def required_action_types(self) -> Optional[set[ActionType]]:
        return {ActionType.access, ActionType.erasure}

    def execute(self, ctx: PipelineContext) -> StepResult:
        ACTION_STRATEGIES[ActionType.access].run_pipeline_action(ctx)
        return StepResult.HALT

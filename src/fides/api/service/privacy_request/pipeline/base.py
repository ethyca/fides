from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from fides.api.models.privacy_request import can_run_checkpoint
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.service.privacy_request.pipeline.context import PipelineContext


class StepResult(Enum):
    CONTINUE = "continue"
    HALT = "halt"


class PipelineStep(ABC):
    """Base class for discrete steps in the privacy request pipeline."""

    @property
    @abstractmethod
    def checkpoint(self) -> Optional[CurrentStep]: ...

    @property
    def required_action_types(self) -> Optional[set[ActionType]]:
        return None

    def should_run(self, ctx: PipelineContext) -> bool:
        if self.checkpoint and not can_run_checkpoint(self.checkpoint, ctx.resume_step):
            return False
        if self.required_action_types:
            return any(
                ctx.policy.get_rules_for_action(action_type=at)
                for at in self.required_action_types
            )
        return True

    @abstractmethod
    def execute(self, ctx: PipelineContext) -> StepResult: ...

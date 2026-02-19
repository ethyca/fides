from __future__ import annotations

from typing import Optional

from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.task.graph_runners import access_runner


class AccessStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.access

    @property
    def required_action_types(self) -> Optional[set[ActionType]]:
        return {ActionType.access, ActionType.erasure}

    def execute(self, ctx: PipelineContext) -> StepResult:
        assert ctx.dataset_graph is not None
        assert ctx.connection_configs is not None
        assert ctx.identity_data is not None
        access_runner(
            privacy_request=ctx.privacy_request,
            policy=ctx.policy,
            graph=ctx.dataset_graph,
            connection_configs=ctx.connection_configs,
            identity=ctx.identity_data,
            session=ctx.session,
            privacy_request_proceed=True,
        )
        return StepResult.CONTINUE

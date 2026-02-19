from __future__ import annotations

from typing import Optional

from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.task.graph_runners import consent_runner
from fides.api.task.graph_task import build_consent_dataset_graph


class ConsentStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.consent

    @property
    def required_action_types(self) -> Optional[set[ActionType]]:
        return {ActionType.consent}

    def execute(self, ctx: PipelineContext) -> StepResult:
        consent_runner(
            privacy_request=ctx.privacy_request,
            policy=ctx.policy,
            graph=build_consent_dataset_graph(ctx.datasets, ctx.session),
            connection_configs=ctx.connection_configs,
            identity=ctx.identity_data,
            session=ctx.session,
            privacy_request_proceed=True,
        )
        return StepResult.CONTINUE

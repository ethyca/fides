from __future__ import annotations

from typing import Optional

from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.service.privacy_request.access_result_service import (
    upload_and_save_access_results,
)
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.task.graph_task import filter_by_enabled_actions


class UploadAccessStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return CurrentStep.upload_access

    @property
    def required_action_types(self) -> Optional[set[ActionType]]:
        return {ActionType.access, ActionType.erasure}

    def execute(self, ctx: PipelineContext) -> StepResult:
        assert ctx.connection_configs is not None
        raw_access_results: dict = ctx.privacy_request.get_raw_access_results()
        filtered_access_results = filter_by_enabled_actions(
            raw_access_results, ctx.connection_configs
        )
        ctx.access_result_urls = upload_and_save_access_results(
            ctx.session,
            ctx.policy,
            filtered_access_results,
            ctx.dataset_graph,
            ctx.privacy_request,
            ctx.manual_webhook_access_results,
            ctx.fides_connector_datasets,
        )
        return StepResult.CONTINUE

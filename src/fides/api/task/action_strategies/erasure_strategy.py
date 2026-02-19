from __future__ import annotations

from typing import TYPE_CHECKING, List

from loguru import logger

from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.task.action_strategies.base import ActionStrategy
from fides.api.task.execute_request_tasks import (
    get_upstream_access_data_for_erasure_task,
)
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session

    from fides.api.models.privacy_request import RequestTask
    from fides.api.service.privacy_request.pipeline.context import PipelineContext
    from fides.api.task.graph_task import GraphTask
    from fides.api.task.task_resources import TaskResources


class ErasureStrategy(ActionStrategy):
    @property
    def action_type(self) -> ActionType:
        return ActionType.erasure

    @property
    def next_step(self) -> CurrentStep:
        return CurrentStep.finalize_erasure

    def run_pipeline_action(self, ctx: PipelineContext) -> None:
        from fides.api.task.create_request_tasks import run_erasure_request

        run_erasure_request(
            privacy_request=ctx.privacy_request,
            session=ctx.session,
            privacy_request_proceed=True,
        )

    def execute_node(
        self,
        graph_task: GraphTask,
        request_task: RequestTask,
        upstream_results: Query,
        session: Session,
        resources: TaskResources,
    ) -> None:
        retrieved_data: List[Row] = request_task.get_data_for_erasures() or []
        upstream_access_data: List[List[Row]] = []
        try:
            upstream_access_data = get_upstream_access_data_for_erasure_task(
                request_task, session, resources
            )
        except Exception as e:
            logger.error(
                "Unable to get upstream access data for erasure task {}: {}",
                request_task.collection_address,
                e,
            )
        graph_task.erasure_request(retrieved_data, inputs=upstream_access_data)

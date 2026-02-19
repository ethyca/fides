from __future__ import annotations

from typing import TYPE_CHECKING, List

from fides.api.common_exceptions import PrivacyRequestExit
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.task.action_strategies.base import ActionStrategy
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session

    from fides.api.models.privacy_request import RequestTask
    from fides.api.service.privacy_request.pipeline.context import PipelineContext
    from fides.api.task.graph_task import GraphTask
    from fides.api.task.task_resources import TaskResources


class AccessStrategy(ActionStrategy):
    @property
    def action_type(self) -> ActionType:
        return ActionType.access

    @property
    def next_step(self) -> CurrentStep:
        return CurrentStep.upload_access

    def run_pipeline_action(self, ctx: PipelineContext) -> None:
        from fides.api.task.create_request_tasks import run_access_request

        run_access_request(
            privacy_request=ctx.privacy_request,
            policy=ctx.policy,
            graph=ctx.dataset_graph,
            connection_configs=ctx.connection_configs,
            identity=ctx.identity_data,
            session=ctx.session,
            privacy_request_proceed=True,
        )
        raise PrivacyRequestExit()

    def execute_node(
        self,
        graph_task: GraphTask,
        request_task: RequestTask,
        upstream_results: Query,
        session: Session,
        resources: TaskResources,
    ) -> None:
        from fides.api.task.execute_request_tasks import _build_upstream_access_data

        upstream_access_data: List[List[Row]] = _build_upstream_access_data(
            graph_task.execution_node.input_keys, upstream_results
        )
        graph_task.access_request(*upstream_access_data)

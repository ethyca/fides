from __future__ import annotations

from typing import TYPE_CHECKING, List

from fides.api.common_exceptions import PrivacyRequestExit
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.task.action_strategies.base import ActionStrategy

if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session

    from fides.api.models.privacy_request import RequestTask
    from fides.api.service.privacy_request.pipeline.context import PipelineContext
    from fides.api.task.graph_task import GraphTask
    from fides.api.task.task_resources import TaskResources


class ConsentStrategy(ActionStrategy):
    @property
    def action_type(self) -> ActionType:
        return ActionType.consent

    @property
    def next_step(self) -> CurrentStep:
        return CurrentStep.finalize_consent

    def run_pipeline_action(self, ctx: PipelineContext) -> None:
        from fides.api.task.create_request_tasks import run_consent_request
        from fides.api.task.graph_task import build_consent_dataset_graph

        assert ctx.datasets is not None
        graph = build_consent_dataset_graph(ctx.datasets, ctx.session)
        run_consent_request(
            privacy_request=ctx.privacy_request,
            graph=graph,
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
        access_data: List = []
        if upstream_results:
            access_data = upstream_results[0].get_access_data() or []
        graph_task.consent_request(access_data[0] if access_data else {})

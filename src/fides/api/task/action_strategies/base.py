from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from fides.api.schemas.policy import ActionType, CurrentStep

if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session

    from fides.api.models.privacy_request import RequestTask
    from fides.api.service.privacy_request.pipeline.context import PipelineContext
    from fides.api.task.graph_task import GraphTask
    from fides.api.task.task_resources import TaskResources


class ActionStrategy(ABC):
    @property
    @abstractmethod
    def action_type(self) -> ActionType: ...

    @property
    @abstractmethod
    def next_step(self) -> CurrentStep:
        """CurrentStep to resume from after all nodes complete."""
        ...

    @abstractmethod
    def run_pipeline_action(self, ctx: PipelineContext) -> None:
        """Called by pipeline steps. Creates request tasks and raises PrivacyRequestExit."""
        ...

    @abstractmethod
    def execute_node(
        self,
        graph_task: GraphTask,
        request_task: RequestTask,
        upstream_results: Query,
        session: Session,
        resources: TaskResources,
    ) -> None:
        """Execute action-specific logic for a single node."""
        ...

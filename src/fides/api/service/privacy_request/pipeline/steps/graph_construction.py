from __future__ import annotations

from typing import Optional

from loguru import logger
from sqlalchemy.orm import selectinload

from fides.api import common_exceptions
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.connectors.fides_connector import filter_fides_connector_datasets
from fides.api.service.privacy_request.pipeline.base import PipelineStep, StepResult
from fides.api.service.privacy_request.pipeline.context import PipelineContext
from fides.api.task.manual.manual_task_utils import create_manual_task_artificial_graphs


class GraphConstructionStep(PipelineStep):
    @property
    def checkpoint(self) -> Optional[CurrentStep]:
        return None

    def execute(self, ctx: PipelineContext) -> StepResult:
        try:
            ctx.policy.rules[0]  # type: ignore[attr-defined]
        except IndexError:
            error_message = (
                f"Policy with key {ctx.policy.key} must contain at least one Rule."
            )
            ctx.privacy_request.add_error_execution_log(
                ctx.session,
                connection_key=None,
                dataset_name="Policy validation",
                collection_name=None,
                message=error_message,
                action_type=ActionType.access,
            )
            ctx.privacy_request.error_processing(db=ctx.session)
            raise common_exceptions.MisconfiguredPolicyException(error_message)

        datasets = (
            ctx.session.query(DatasetConfig)
            .options(
                selectinload(DatasetConfig.connection_config),
                selectinload(DatasetConfig.ctl_dataset),
            )
            .all()
        )
        dataset_graphs = [
            dataset_config.get_graph()
            for dataset_config in datasets
            if not dataset_config.connection_config.disabled
        ]

        manual_task_graphs = create_manual_task_artificial_graphs(
            ctx.session, config_types=[ActionType.access, ActionType.erasure]
        )
        dataset_graphs.extend(manual_task_graphs)

        dataset_graph = DatasetGraph(*dataset_graphs)

        ctx.privacy_request.add_success_execution_log(
            ctx.session,
            connection_key=None,
            dataset_name="Dataset reference validation",
            collection_name=None,
            message=f"Dataset reference validation successful for privacy request: {ctx.privacy_request.id}",
            action_type=ctx.privacy_request.policy.get_action_type(),  # type: ignore
        )

        identity_data = {
            key: value["value"] if isinstance(value, dict) else value
            for key, value in ctx.privacy_request.get_cached_identity_data().items()
        }

        connection_configs = (
            ctx.session.query(ConnectionConfig)
            .options(selectinload(ConnectionConfig.datasets))
            .all()
        )
        fides_connector_datasets: set[str] = filter_fides_connector_datasets(
            connection_configs
        )

        ctx.datasets = datasets
        ctx.dataset_graph = dataset_graph
        ctx.identity_data = identity_data
        ctx.connection_configs = connection_configs
        ctx.fides_connector_datasets = fides_connector_datasets

        if (
            ctx.privacy_request.status
            == PrivacyRequestStatus.requires_manual_finalization
            and ctx.privacy_request.finalized_at is None
        ):
            return StepResult.HALT

        return StepResult.CONTINUE

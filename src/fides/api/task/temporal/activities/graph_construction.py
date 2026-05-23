"""Activities for building the traversal graph and persisting RequestTasks.

These activities wrap existing graph construction code from
create_request_tasks.py, running it inside a Temporal activity
with its own DB session.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from temporalio import activity

from fides.api.task.temporal.converters import (
    GraphPlan,
    NodeInfo,
    PrivacyRequestContext,
    TraversalPhase,
)


def _build_graph_plan_from_tasks(
    session: Session,
    privacy_request_id: str,
    action_type: Any,
    phase: TraversalPhase,
) -> GraphPlan:
    """Build a serializable GraphPlan from persisted RequestTasks.

    Marks nodes as already_completed or already_skipped based on their
    DB status. The workflow uses these flags to skip re-execution of
    nodes that already have data (preserving access results and
    acknowledging completed erasures).
    """
    from fides.api.graph.config import ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS
    from fides.api.models.privacy_request import RequestTask
    from fides.api.schemas.privacy_request import ExecutionLogStatus
    from fides.api.task.manual.manual_task_address import ManualTaskAddress

    graph_plan = GraphPlan(
        privacy_request_id=privacy_request_id,
        phase=phase,
    )

    tasks = (
        session.query(RequestTask)
        .filter(
            RequestTask.privacy_request_id == privacy_request_id,
            RequestTask.action_type == action_type,
        )
        .all()
    )

    for task in tasks:
        completed = task.status == ExecutionLogStatus.complete
        skipped = task.status == ExecutionLogStatus.skipped

        graph_plan.nodes[task.collection_address] = NodeInfo(
            address=task.collection_address,
            upstream=task.upstream_tasks or [],
            downstream=task.downstream_tasks or [],
            is_root=task.collection_address == ROOT_COLLECTION_ADDRESS.value,
            is_terminator=task.collection_address == TERMINATOR_ADDRESS.value,
            is_manual_task=ManualTaskAddress.is_manual_task_address(
                task.request_task_address
            ),
            async_type=task.async_type,
            request_task_id=str(task.id),
            already_completed=completed,
            already_skipped=skipped,
        )

    return graph_plan


@activity.defn
async def load_privacy_request_context(
    privacy_request_id: str,
) -> PrivacyRequestContext:
    """Load all context needed to orchestrate a privacy request."""
    from sqlalchemy.orm import selectinload

    from fides.api.models.connectionconfig import ConnectionConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.schemas.policy import ActionType
    from fides.api.service.privacy_request.request_runner_service import (
        filter_fides_connector_datasets,
    )
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = (
            session.query(PrivacyRequest)
            .options(
                selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
            )
            .filter(PrivacyRequest.id == privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        policy = privacy_request.policy

        connection_configs = (
            session.query(ConnectionConfig)
            .options(selectinload(ConnectionConfig.datasets))
            .all()
        )

        identity_data = {
            key: value["value"] if isinstance(value, dict) else value
            for key, value in privacy_request.get_cached_identity_data().items()
        }

        return PrivacyRequestContext(
            privacy_request_id=privacy_request_id,
            policy_id=str(policy.id),
            has_access_rules=bool(
                policy.get_rules_for_action(ActionType.access)
                or policy.get_rules_for_action(ActionType.erasure)
            ),
            has_erasure_rules=bool(policy.get_rules_for_action(ActionType.erasure)),
            has_consent_rules=bool(policy.get_rules_for_action(ActionType.consent)),
            identity_data=identity_data,
            property_id=privacy_request.property_id,
            fides_connector_datasets=list(
                filter_fides_connector_datasets(connection_configs)
            ),
        )


@activity.defn
async def build_and_persist_access_graph(
    privacy_request_id: str,
) -> GraphPlan:
    """Build the access traversal graph and persist RequestTasks.

    Builds the graph fresh from current dataset configs — on retry/reset
    this re-executes, solving the stale graph problem.
    """
    from sqlalchemy.orm import selectinload

    from fides.api.graph.config import CollectionAddress
    from fides.api.graph.graph import DatasetGraph
    from fides.api.graph.traversal import Traversal
    from fides.api.models.connectionconfig import ConnectionConfig
    from fides.api.models.datasetconfig import DatasetConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest, RequestTask
    from fides.api.schemas.policy import ActionType
    from fides.api.service.privacy_request.request_runner_service import (
        apply_dataset_graph_filters,
    )
    from fides.api.task.create_request_tasks import (
        collect_tasks_fn,
        format_data_use_map_for_caching,
        get_connection_configs_with_manual_tasks,
        persist_initial_erasure_request_tasks,
        persist_new_access_request_tasks,
    )
    from fides.api.task.manual.manual_task_utils import (
        create_manual_task_artificial_graphs,
    )
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = (
            session.query(PrivacyRequest)
            .options(
                selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
            )
            .filter(PrivacyRequest.id == privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        policy = privacy_request.policy

        datasets = (
            session.query(DatasetConfig)
            .options(
                selectinload(DatasetConfig.connection_config),
                selectinload(DatasetConfig.ctl_dataset),
            )
            .all()
        )

        connection_configs = (
            session.query(ConnectionConfig)
            .options(selectinload(ConnectionConfig.datasets))
            .all()
        )

        dataset_graphs = [
            dc.get_graph() for dc in datasets if not dc.connection_config.disabled
        ]
        manual_graphs = create_manual_task_artificial_graphs(
            session, config_types=[ActionType.access, ActionType.erasure]
        )
        dataset_graphs.extend(manual_graphs)
        dataset_graphs = apply_dataset_graph_filters(
            dataset_graphs, privacy_request.property_id
        )
        dataset_graph = DatasetGraph(*dataset_graphs)

        identity_data = {
            key: value["value"] if isinstance(value, dict) else value
            for key, value in privacy_request.get_cached_identity_data().items()
        }

        traversal = Traversal(dataset_graph, identity_data, policy=policy)
        traversal_nodes: dict[CollectionAddress, Any] = {}
        end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)

        privacy_request.create_manual_task_instances(
            session, get_connection_configs_with_manual_tasks(session)
        )

        persist_new_access_request_tasks(
            session,
            privacy_request,
            traversal,
            traversal_nodes,
            end_nodes,
            dataset_graph,
        )

        if policy.get_rules_for_action(ActionType.erasure):
            persist_initial_erasure_request_tasks(
                session,
                privacy_request,
                traversal_nodes,
                list(dataset_graph.nodes.keys()),
                dataset_graph,
            )

        privacy_request.cache_data_use_map(
            format_data_use_map_for_caching(
                {
                    addr: tn.node.dataset.connection_key
                    for addr, tn in traversal_nodes.items()
                },
                connection_configs,
            )
        )

        if traversal.skipped_nodes:
            for node_address, skip_message in traversal.skipped_nodes.items():
                privacy_request.add_skipped_execution_log(
                    db=session,
                    connection_key=None,
                    dataset_name=getattr(node_address, "dataset", str(node_address)),
                    collection_name=getattr(node_address, "collection", None),
                    message=skip_message,
                    action_type=ActionType.access,
                )
        else:
            privacy_request.add_success_execution_log(
                db=session,
                connection_key=None,
                dataset_name="__traversal__",
                collection_name=None,
                message="Traversal successful for privacy request",
                action_type=ActionType.access,
            )

        session.commit()

        return _build_graph_plan_from_tasks(
            session, privacy_request_id, ActionType.access, TraversalPhase.ACCESS
        )


@activity.defn
async def build_erasure_graph_plan(privacy_request_id: str) -> GraphPlan:
    """Build a GraphPlan from existing erasure RequestTasks."""
    from fides.api.schemas.policy import ActionType
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        return _build_graph_plan_from_tasks(
            session, privacy_request_id, ActionType.erasure, TraversalPhase.ERASURE
        )


@activity.defn
async def build_and_persist_consent_graph(
    privacy_request_id: str,
    identity_data: dict,
) -> GraphPlan:
    """Build the consent traversal graph and persist RequestTasks.

    Consent graphs are flat — one node per dataset, no dependencies
    between nodes. All nodes execute in parallel from root.
    """
    from sqlalchemy.orm import selectinload

    from fides.api.models.datasetconfig import DatasetConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest, RequestTask
    from fides.api.schemas.policy import ActionType
    from fides.api.service.privacy_request.request_runner_service import (
        build_consent_dataset_graph,
    )
    from fides.api.task.create_request_tasks import run_consent_request
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = (
            session.query(PrivacyRequest)
            .options(
                selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
            )
            .filter(PrivacyRequest.id == privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        datasets = (
            session.query(DatasetConfig)
            .options(
                selectinload(DatasetConfig.connection_config),
                selectinload(DatasetConfig.ctl_dataset),
            )
            .all()
        )

        consent_graph = build_consent_dataset_graph(datasets, session)

        run_consent_request(
            privacy_request=privacy_request,
            graph=consent_graph,
            identity=identity_data,
            session=session,
            privacy_request_proceed=False,
        )

        return _build_graph_plan_from_tasks(
            session, privacy_request_id, ActionType.consent, TraversalPhase.CONSENT
        )

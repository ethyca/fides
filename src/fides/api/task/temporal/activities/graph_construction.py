"""Activities for building the traversal graph and persisting RequestTasks.

These activities wrap existing graph construction code from
create_request_tasks.py, running it inside a Temporal activity
with its own DB session.
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from sqlalchemy.orm import Session
from temporalio import activity

from fides.api.task.temporal.converters import (
    GraphPlan,
    NodeInfo,
    PrivacyRequestContext,
    TraversalPhase,
)
from fides.api.task.temporal.graph_diff import (
    GraphDiffResult,
    NodeStatus,
)


def _build_graph_plan_from_tasks(
    session: Session,
    privacy_request_id: str,
    action_type: Any,
    phase: str,
    diff_result: GraphDiffResult | None = None,
) -> GraphPlan:
    """Build a serializable GraphPlan from persisted RequestTasks.

    Marks nodes as already_completed or already_skipped based on their
    DB status. When a diff_result is provided (reprocessing), applies
    dirty/clean status from the diff to determine which nodes need
    re-execution.
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

        is_dirty = False
        dirty_reasons: list[str] = []
        if diff_result and task.collection_address in diff_result.nodes:
            node_diff = diff_result.nodes[task.collection_address]
            is_dirty = node_diff.status in (NodeStatus.DIRTY, NodeStatus.ADDED)
            dirty_reasons = [r.value for r in node_diff.reasons]

        should_skip = (completed or skipped) and not is_dirty

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
            already_completed=should_skip and completed,
            already_skipped=should_skip and skipped,
            is_dirty=is_dirty,
            dirty_reasons=dirty_reasons,
        )

    return graph_plan


def _sync_erasure_tasks_with_access_diff(
    session: Session,
    privacy_request: Any,
    access_diff: GraphDiffResult,
    traversal_nodes: dict[Any, Any],
    dataset_graph: Any,
) -> None:
    """Sync erasure RequestTasks after access graph diff.

    - ADDED access nodes: create corresponding erasure tasks
    - DIRTY access nodes: reset corresponding erasure task data
    - ORPHAN access nodes: mark corresponding erasure task as skipped
    """
    from fides.api.models.privacy_request import RequestTask
    from fides.api.schemas.policy import ActionType
    from fides.api.schemas.privacy_request import ExecutionLogStatus
    from fides.api.task.graph_utils import (
        base_task_data,
        build_erasure_networkx_digraph,
        compute_all_descendants,
    )

    existing_erasure = {
        t.collection_address: t
        for t in session.query(RequestTask)
        .filter(
            RequestTask.privacy_request_id == privacy_request.id,
            RequestTask.action_type == ActionType.erasure,
        )
        .all()
    }

    erasure_end_nodes = list(dataset_graph.nodes.keys())
    erasure_graph = build_erasure_networkx_digraph(traversal_nodes, erasure_end_nodes)
    all_descendants = compute_all_descendants(erasure_graph)

    for addr, node_diff in access_diff.nodes.items():
        if node_diff.status == NodeStatus.ADDED:
            if addr not in existing_erasure:
                addr_key = _find_traversal_addr(traversal_nodes, addr)
                if not addr_key or addr_key not in traversal_nodes:
                    continue
                task_data = base_task_data(
                    erasure_graph,
                    dataset_graph,
                    privacy_request,
                    addr_key,
                    traversal_nodes,
                    all_descendants,
                )
                task_data["action_type"] = ActionType.erasure
                RequestTask.create(db=session, data=task_data)
                logger.info("Created erasure task for added node {}", addr)

        elif node_diff.status == NodeStatus.DIRTY:
            task = existing_erasure.get(addr)
            if task:
                task.status = ExecutionLogStatus.pending
                task.data_for_erasures = []
                task.rows_masked = None
                addr_key = _find_traversal_addr(traversal_nodes, addr)
                if addr_key and addr_key in traversal_nodes:
                    tn = traversal_nodes[addr_key]
                    task.traversal_details = tn.format_traversal_details_for_save()
                    task.collection = tn.node.collection.model_dump(mode="json")
                session.add(task)
                logger.info("Reset erasure task for dirty access node {}", addr)

        elif node_diff.status == NodeStatus.ORPHAN:
            task = existing_erasure.get(addr)
            if task:
                task.status = ExecutionLogStatus.skipped
                session.add(task)
                logger.info("Marked orphan erasure task {} as skipped", addr)

    for addr, task in existing_erasure.items():
        addr_key = _find_traversal_addr(traversal_nodes, addr)
        if addr_key and addr_key in erasure_graph:
            predecessors = list(erasure_graph.predecessors(addr_key))
            successors = list(erasure_graph.successors(addr_key))
            task.upstream_tasks = [
                p.value if hasattr(p, "value") else str(p) for p in predecessors
            ]
            task.downstream_tasks = [
                s.value if hasattr(s, "value") else str(s) for s in successors
            ]
            desc = all_descendants.get(addr_key, set())
            task.all_descendant_tasks = [
                d.value if hasattr(d, "value") else str(d) for d in desc
            ]
            session.add(task)

    session.flush()


def cleanup_async_state(session: Session, task: Any) -> None:
    """Clean up async-specific state on a dirty RequestTask.

    - Polling tasks: mark sub-requests as skipped (abandon silently)
    - Callback tasks: reset callback_succeeded
    """
    from fides.api.models.privacy_request.request_task import RequestTaskSubRequest

    if task.async_type and task.async_type.value == "polling":
        for sub_request in task.sub_requests or []:
            if sub_request.status not in ("complete", "error", "skipped"):
                sub_request.status = "skipped"
                session.add(sub_request)
        logger.info(
            "Abandoned {} polling sub-requests for {}",
            len(task.sub_requests or []),
            task.collection_address,
        )


def has_dirty_manual_nodes(diff_result: GraphDiffResult) -> bool:
    """Check if any dirty/added nodes are manual task addresses."""
    from fides.api.task.manual.manual_task_address import ManualTaskAddress

    return any(
        ManualTaskAddress.is_manual_task_address(addr)
        for addr in diff_result.dirty_nodes + diff_result.added_nodes
    )


def _recreate_manual_task_instances(
    session: Session,
    privacy_request: Any,
    diff_result: GraphDiffResult,
) -> None:
    """Recreate ManualTaskInstances for dirty manual tasks.

    When a manual task's field definitions change, the existing
    ManualTaskInstances may not match. create_manual_task_instances
    is idempotent (skips existing config_ids), so calling it again
    picks up any new configs.
    """
    if has_dirty_manual_nodes(diff_result):
        from fides.api.task.manual.manual_task_utils import (
            get_connection_configs_with_manual_tasks,
        )

        privacy_request.create_manual_task_instances(
            session, get_connection_configs_with_manual_tasks(session)
        )
        logger.info(
            "Refreshed ManualTaskInstances for privacy request {}",
            privacy_request.id,
        )


def _find_traversal_addr(traversal_nodes: dict[Any, Any], addr_str: str) -> Any | None:
    """Find the CollectionAddress key in traversal_nodes matching a string."""
    for tn_addr in traversal_nodes:
        if (hasattr(tn_addr, "value") and tn_addr.value == addr_str) or str(
            tn_addr
        ) == addr_str:
            return tn_addr
    return None


def _apply_diff_to_request_tasks(
    session: Session,
    privacy_request: Any,
    existing_tasks: list[Any],
    diff_result: GraphDiffResult,
    traversal: Any,
    traversal_nodes: dict[Any, Any],
    end_nodes: list[Any],
    dataset_graph: Any,
    action_type: Any,
) -> None:
    """Apply graph diff results to existing RequestTasks.

    - DIRTY nodes: reset status to pending, clear stale data
    - ADDED nodes: create new RequestTasks
    - ORPHAN nodes: mark as skipped
    - CLEAN nodes: leave untouched
    """
    from fides.api.graph.config import ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS
    from fides.api.schemas.privacy_request import ExecutionLogStatus
    from fides.api.task.graph_utils import (
        base_task_data,
        build_access_networkx_digraph,
        compute_all_descendants,
    )

    existing_by_addr = {t.collection_address: t for t in existing_tasks}

    for addr, node_diff in diff_result.nodes.items():
        if node_diff.status == NodeStatus.DIRTY:
            task = existing_by_addr.get(addr)
            if task:
                task.status = ExecutionLogStatus.pending
                task.access_data = []
                task.data_for_erasures = []
                task.rows_masked = None
                task.consent_sent = None
                task.callback_succeeded = None

                cleanup_async_state(session, task)

                addr_key = _find_traversal_addr(traversal_nodes, addr)
                if addr_key and addr_key in traversal_nodes:
                    tn = traversal_nodes[addr_key]
                    td = tn.format_traversal_details_for_save()
                    task.traversal_details = td
                    task.collection = tn.node.collection.model_dump(mode="json")

                session.add(task)
                logger.info(
                    "Reset dirty task {} (reasons: {})",
                    addr,
                    [r.value for r in node_diff.reasons],
                )

        elif node_diff.status == NodeStatus.ORPHAN:
            task = existing_by_addr.get(addr)
            if task:
                task.status = ExecutionLogStatus.skipped
                session.add(task)
                logger.info("Marked orphan task {} as skipped", addr)

    _recreate_manual_task_instances(session, privacy_request, diff_result)

    networkx_graph = build_access_networkx_digraph(
        traversal_nodes, end_nodes, traversal
    )
    all_descendants = compute_all_descendants(networkx_graph)

    added_addrs = diff_result.added_nodes
    if added_addrs:
        from fides.api.models.privacy_request import RequestTask

        for addr_str in added_addrs:
            addr_key = _find_traversal_addr(traversal_nodes, addr_str)
            if not addr_key or addr_key not in traversal_nodes:
                continue

            task_data = base_task_data(
                networkx_graph,
                dataset_graph,
                privacy_request,
                addr_key,
                traversal_nodes,
                all_descendants,
            )
            task_data["action_type"] = action_type
            RequestTask.create(db=session, data=task_data)
            logger.info("Created new task for added node {}", addr_str)

    for task in existing_tasks:
        addr_key = _find_traversal_addr(traversal_nodes, task.collection_address)
        if addr_key and addr_key in traversal_nodes:
            predecessors = list(networkx_graph.predecessors(addr_key))
            successors = list(networkx_graph.successors(addr_key))
            task.upstream_tasks = [
                p.value if hasattr(p, "value") else str(p) for p in predecessors
            ]
            task.downstream_tasks = [
                s.value if hasattr(s, "value") else str(s) for s in successors
            ]
            desc = all_descendants.get(addr_key, set())
            task.all_descendant_tasks = [
                d.value if hasattr(d, "value") else str(d) for d in desc
            ]
            session.add(task)

    session.flush()


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

    Builds the graph fresh from current dataset configs. On reprocess
    (existing tasks present), computes a diff between old and new graphs
    to determine which nodes need re-execution.
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
    from fides.api.task.graph_utils import (
        collect_tasks_fn,
        format_data_use_map_for_caching,
        persist_initial_erasure_request_tasks,
        persist_new_access_request_tasks,
    )
    from fides.api.task.manual.manual_task_utils import (
        create_manual_task_artificial_graphs,
        get_connection_configs_with_manual_tasks,
    )
    from fides.api.task.temporal.graph_diff import (
        build_new_node_snapshots_from_traversal,
        build_old_node_snapshots_from_request_tasks,
        compute_graph_diff,
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

        # Check for existing tasks (reprocessing)
        existing_tasks = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request_id,
                RequestTask.action_type == ActionType.access,
            )
            .all()
        )

        diff_result = None
        is_reprocess = len(existing_tasks) > 0

        if is_reprocess:
            cc_dict = {cc.key: cc for cc in connection_configs}
            old_snapshots = build_old_node_snapshots_from_request_tasks(existing_tasks)
            new_snapshots = build_new_node_snapshots_from_traversal(
                traversal_nodes, dataset_graph, cc_dict
            )
            diff_result = compute_graph_diff(old_snapshots, new_snapshots)
            logger.info(
                "Reprocessing access graph for {}: {}",
                privacy_request_id,
                diff_result.to_summary(),
            )

            _apply_diff_to_request_tasks(
                session,
                privacy_request,
                existing_tasks,
                diff_result,
                traversal,
                traversal_nodes,
                end_nodes,
                dataset_graph,
                ActionType.access,
            )

            if policy.get_rules_for_action(ActionType.erasure):
                _sync_erasure_tasks_with_access_diff(
                    session,
                    privacy_request,
                    diff_result,
                    traversal_nodes,
                    dataset_graph,
                )
        else:
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
                dataset_name="Dataset traversal",
                collection_name=None,
                message="Traversal successful for privacy request",
                action_type=ActionType.access,
            )

        session.commit()

        return _build_graph_plan_from_tasks(
            session,
            privacy_request_id,
            ActionType.access,
            TraversalPhase.ACCESS,
            diff_result=diff_result,
        )


@activity.defn
async def build_erasure_graph_plan(privacy_request_id: str) -> GraphPlan:
    """Build a GraphPlan from existing erasure RequestTasks.

    Propagates dirty state from access tasks: if an access node was dirty
    and re-executed, the corresponding erasure node needs fresh
    data_for_erasures and should re-execute.
    """
    from fides.api.models.privacy_request import RequestTask
    from fides.api.schemas.policy import ActionType
    from fides.api.schemas.privacy_request import ExecutionLogStatus
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        access_tasks = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request_id,
                RequestTask.action_type == ActionType.access,
            )
            .all()
        )

        erasure_tasks = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request_id,
                RequestTask.action_type == ActionType.erasure,
            )
            .all()
        )

        access_by_addr = {t.collection_address: t for t in access_tasks}
        diff_result = build_erasure_diff_from_access_state(
            access_by_addr, erasure_tasks
        )

        if diff_result:
            logger.info(
                "Erasure graph diff for {}: {}",
                privacy_request_id,
                diff_result.to_summary(),
            )

        return _build_graph_plan_from_tasks(
            session,
            privacy_request_id,
            ActionType.erasure,
            TraversalPhase.ERASURE,
            diff_result=diff_result,
        )


def build_erasure_diff_from_access_state(
    access_by_addr: dict[str, Any],
    erasure_tasks: list[Any],
) -> GraphDiffResult | None:
    """Build a diff for erasure tasks based on corresponding access task state.

    An erasure node is dirty if:
    - Its corresponding access task was re-executed (pending status means
      it was reset by the access diff)
    - The erasure task itself errored
    """
    from fides.api.schemas.privacy_request import ExecutionLogStatus
    from fides.api.task.temporal.graph_diff import (
        DirtyReason,
        NodeDiffResult,
    )

    has_changes = False
    diff = GraphDiffResult()

    for task in erasure_tasks:
        addr = task.collection_address
        access_task = access_by_addr.get(addr)

        reasons: list[DirtyReason] = []

        if task.status in (ExecutionLogStatus.error, ExecutionLogStatus.pending):
            reasons.append(DirtyReason.PREVIOUSLY_ERRORED)

        if access_task and access_task.status in (
            ExecutionLogStatus.pending,
            ExecutionLogStatus.in_processing,
        ):
            reasons.append(DirtyReason.UPSTREAM_DIRTY)

        if reasons:
            diff.nodes[addr] = NodeDiffResult(
                address=addr,
                status=NodeStatus.DIRTY,
                reasons=reasons,
                old_request_task_id=str(task.id),
            )
            has_changes = True
        else:
            diff.nodes[addr] = NodeDiffResult(
                address=addr,
                status=NodeStatus.CLEAN,
                old_request_task_id=str(task.id),
            )

    return diff if has_changes else None


@activity.defn
async def build_and_persist_consent_graph(
    privacy_request_id: str,
    identity_data: dict,
) -> GraphPlan:
    """Build the consent traversal graph and persist RequestTasks.

    Consent graphs are flat — one node per dataset, no dependencies
    between nodes. All nodes execute in parallel from root.

    On reprocess, diffs old vs new consent nodes to handle
    connections added/removed/changed.
    """
    from sqlalchemy.orm import selectinload

    from fides.api.models.datasetconfig import DatasetConfig
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest, RequestTask
    from fides.api.schemas.policy import ActionType
    from fides.api.schemas.privacy_request import ExecutionLogStatus
    from fides.api.service.privacy_request.request_runner_service import (
        build_consent_dataset_graph,
    )
    from fides.api.task.graph_utils import (
        base_task_data,
        build_consent_networkx_digraph,
        compute_all_descendants,
        persist_new_consent_request_tasks,
    )
    from fides.api.task.manual.manual_task_utils import (
        get_connection_configs_with_manual_tasks,
    )
    from fides.api.task.temporal.graph_diff import (
        DirtyReason,
        NodeDiffResult,
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

        datasets = (
            session.query(DatasetConfig)
            .options(
                selectinload(DatasetConfig.connection_config),
                selectinload(DatasetConfig.ctl_dataset),
            )
            .all()
        )

        consent_graph = build_consent_dataset_graph(datasets, session)

        existing_tasks = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request_id,
                RequestTask.action_type == ActionType.consent,
            )
            .all()
        )

        diff_result = None

        if existing_tasks:
            existing_addrs = {t.collection_address for t in existing_tasks}
            new_addrs = {addr.value for addr in consent_graph.nodes}

            diff_result = build_consent_diff(existing_tasks, new_addrs)

            if diff_result:
                logger.info(
                    "Consent graph diff for {}: {}",
                    privacy_request_id,
                    diff_result.to_summary(),
                )

            for addr_str in new_addrs - existing_addrs:
                from fides.api.graph.config import CollectionAddress

                for col_addr, node in consent_graph.nodes.items():
                    if col_addr.value == addr_str:
                        traversal_nodes = {
                            col_addr: type(
                                "TN",
                                (),
                                {
                                    "node": node,
                                    "format_traversal_details_for_save": lambda: {},
                                },
                            )()
                        }
                        graph_nx = build_consent_networkx_digraph(traversal_nodes)
                        all_desc = compute_all_descendants(graph_nx)
                        task_data = base_task_data(
                            graph_nx,
                            consent_graph,
                            privacy_request,
                            col_addr,
                            traversal_nodes,
                            all_desc,
                        )
                        task_data["action_type"] = ActionType.consent
                        task_data["access_data"] = []
                        RequestTask.create(db=session, data=task_data)
                        logger.info("Created consent task for added node {}", addr_str)
                        break

            for task in existing_tasks:
                if task.collection_address not in new_addrs:
                    task.status = ExecutionLogStatus.skipped
                    session.add(task)

            session.flush()
        else:
            from fides.api.graph.traversal import TraversalNode

            traversal_nodes = {
                col_addr: TraversalNode(node)
                for col_addr, node in consent_graph.nodes.items()
            }

            privacy_request.create_manual_task_instances(
                session, get_connection_configs_with_manual_tasks(session)
            )

            persist_new_consent_request_tasks(
                session,
                privacy_request,
                traversal_nodes,
                identity_data,
                consent_graph,
            )

        return _build_graph_plan_from_tasks(
            session,
            privacy_request_id,
            ActionType.consent,
            TraversalPhase.CONSENT,
            diff_result=diff_result,
        )


def build_consent_diff(
    existing_tasks: list[Any],
    new_addrs: set[str],
) -> GraphDiffResult | None:
    """Build diff for consent tasks.

    Consent nodes are dirty if errored/pending, or if their connection
    disappeared (orphan). New connections are ADDED.
    """
    from fides.api.schemas.privacy_request import ExecutionLogStatus
    from fides.api.task.temporal.graph_diff import (
        DirtyReason,
        NodeDiffResult,
    )

    has_changes = False
    diff = GraphDiffResult()

    existing_addrs = set()
    for task in existing_tasks:
        addr = task.collection_address
        existing_addrs.add(addr)

        if addr not in new_addrs:
            diff.nodes[addr] = NodeDiffResult(
                address=addr,
                status=NodeStatus.ORPHAN,
                old_request_task_id=str(task.id),
            )
            has_changes = True
        elif task.status in (ExecutionLogStatus.error, ExecutionLogStatus.pending):
            diff.nodes[addr] = NodeDiffResult(
                address=addr,
                status=NodeStatus.DIRTY,
                reasons=[DirtyReason.PREVIOUSLY_ERRORED],
                old_request_task_id=str(task.id),
            )
            has_changes = True
        else:
            diff.nodes[addr] = NodeDiffResult(
                address=addr,
                status=NodeStatus.CLEAN,
                old_request_task_id=str(task.id),
            )

    for addr in new_addrs - existing_addrs:
        diff.nodes[addr] = NodeDiffResult(
            address=addr,
            status=NodeStatus.ADDED,
            reasons=[DirtyReason.NODE_ADDED],
        )
        has_changes = True

    return diff if has_changes else None

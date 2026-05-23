"""Celery-specific DSR task orchestration.

Graph construction utilities, task persistence, and task hydration functions
have been moved to ``fides.api.task.graph_utils``. This module re-exports
them for backward compatibility and contains only Celery-specific orchestration
(``run_access_request``, ``run_erasure_request``, ``run_consent_request``).
"""

from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import TraversalError
from fides.api.graph.config import (
    CollectionAddress,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import (
    Traversal,
    TraversalNode,
    log_traversal_error_and_update_privacy_request,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    COMPLETED_EXECUTION_LOG_STATUSES,
    PrivacyRequest,
    RequestTask,
)
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.task.execute_request_tasks import log_task_queued, queue_request_task
from fides.api.task.graph_utils import (
    base_task_data,
    build_access_networkx_digraph,
    build_consent_networkx_digraph,
    build_erasure_networkx_digraph,
    collect_tasks_fn,
    compute_all_descendants,
    format_data_use_map_for_caching,
    persist_initial_erasure_request_tasks,
    persist_new_access_request_tasks,
    persist_new_consent_request_tasks,
    update_erasure_tasks_with_access_data,
)
from fides.api.task.manual.manual_task_utils import (
    get_connection_configs_with_manual_tasks,
)
from fides.api.util.logger_context_utils import log_context

__all__ = [
    "base_task_data",
    "build_access_networkx_digraph",
    "build_consent_networkx_digraph",
    "build_erasure_networkx_digraph",
    "collect_tasks_fn",
    "compute_all_descendants",
    "format_data_use_map_for_caching",
    "get_connection_configs_with_manual_tasks",
    "persist_initial_erasure_request_tasks",
    "persist_new_access_request_tasks",
    "persist_new_consent_request_tasks",
    "update_erasure_tasks_with_access_data",
]


@log_context
def run_access_request(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
    privacy_request_proceed: bool = True,
) -> List[RequestTask]:
    """
    DSR 3.0: Build the "access" graph, add its tasks to the database and queue the root task.  If erasure rules
    are present, build the "erasure" graph at the same time so their nodes match, but these erasure nodes are
    not yet ready to run until the access graph is complete in-full.

    If we are *reprocessing* a Privacy Request, instead queue tasks whose upstream nodes are complete.
    """

    if privacy_request.access_tasks.count():
        # If we are reprocessing a privacy request, just see if there
        # are existing ready tasks; don't create new ones.
        # Possible edge cases here where we have no ready tasks and
        # Privacy Request is hanging in an in-processing state.
        ready_tasks: List[RequestTask] = get_existing_ready_tasks(
            session, privacy_request, ActionType.access
        )
    else:
        try:
            traversal: Traversal = Traversal(graph, identity, policy=policy)

            # Traversal.traverse populates traversal_nodes in place, adding parents and children to each traversal_node.
            traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}
            end_nodes: List[CollectionAddress] = traversal.traverse(
                traversal_nodes, collect_tasks_fn
            )

            # Snapshot manual task field instances for this privacy request
            privacy_request.create_manual_task_instances(
                session, get_connection_configs_with_manual_tasks(session)
            )

            # Save Access Request Tasks to the database
            ready_tasks = persist_new_access_request_tasks(
                session, privacy_request, traversal, traversal_nodes, end_nodes, graph
            )

            if (
                policy.get_rules_for_action(action_type=ActionType.erasure)
                and not privacy_request.erasure_tasks.count()
            ):
                # If applicable, go ahead and save Erasure Request Tasks to the Database.
                # These erasure tasks aren't ready to run until the access graph is completed
                # in full, but this makes sure the nodes in the graphs match.
                erasure_end_nodes: List[CollectionAddress] = list(graph.nodes.keys())
                persist_initial_erasure_request_tasks(
                    session, privacy_request, traversal_nodes, erasure_end_nodes, graph
                )

            # cache a map of collections -> data uses for the output package of access requests
            privacy_request.cache_data_use_map(
                format_data_use_map_for_caching(
                    {
                        coll_address: tn.node.dataset.connection_key
                        for (coll_address, tn) in traversal_nodes.items()
                    },
                    connection_configs,
                )
            )

            # Add execution logs for skipped nodes
            if traversal.skipped_nodes:
                logger.warning(
                    "Some nodes were skipped, the identities provided were not sufficient to reach them"
                )
                for node_address, skip_message in traversal.skipped_nodes.items():
                    logger.debug(skip_message)
                    privacy_request.add_skipped_execution_log(
                        session,
                        connection_key=None,
                        dataset_name="Dataset traversal",
                        collection_name=node_address.replace(":", "."),
                        message=skip_message,
                        action_type=ActionType.access,
                    )
            # Or log success if all collections are reachable
            else:
                privacy_request.add_success_execution_log(
                    session,
                    connection_key=None,
                    dataset_name="Dataset traversal",
                    collection_name=None,
                    message=f"Traversal successful for privacy request: {privacy_request.id}",
                    action_type=ActionType.access,
                )
        except TraversalError as err:
            log_traversal_error_and_update_privacy_request(
                privacy_request, session, err
            )
            raise err

    for task in ready_tasks:
        log_task_queued(task, "main runner")
        queue_request_task(task, privacy_request_proceed)

    return ready_tasks


@log_context
def run_erasure_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    session: Session,
    privacy_request_proceed: bool = True,
) -> List[RequestTask]:
    """
    DSR 3.0: Update erasure Request Tasks that were built in the "run_access_request" step with data
    collected to build masking requests and queue the root task for processing.

    If we are reprocessing a Privacy Request, instead queue tasks whose upstream nodes are complete.
    """
    update_erasure_tasks_with_access_data(session, privacy_request)
    ready_tasks: List[RequestTask] = (
        get_existing_ready_tasks(session, privacy_request, ActionType.erasure) or []
    )

    for task in ready_tasks:
        log_task_queued(task, "main runner")
        queue_request_task(task, privacy_request_proceed)
    return ready_tasks


@log_context
def run_consent_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
    privacy_request_proceed: bool = True,
) -> List[RequestTask]:
    """
    DSR 3.0: Build the "consent" graph, add its tasks to the database and queue the root task.

    If we are reprocessing a Privacy Request, instead queue tasks whose upstream nodes are complete.

    The graph built is very simple: there are no relationships between the nodes, every node has
    identity data input and every node outputs whether the consent request succeeded.

    The DatasetGraph passed in is expected to have one Node per Dataset.  That Node is expected to carry out requests
    for the Dataset as a whole.
    """

    if privacy_request.consent_tasks.count():
        logger.info("Consent processing: reprocessing existing tasks")
        ready_tasks: List[RequestTask] = get_existing_ready_tasks(
            session, privacy_request, ActionType.consent
        )
    else:
        logger.info("Consent processing: building consent graph")
        traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}
        # Unlike erasure and access graphs, we don't call traversal.traverse, but build a simpler
        # graph that just has one node per dataset
        for col_address, node in graph.nodes.items():
            traversal_node = TraversalNode(node)
            traversal_nodes[col_address] = traversal_node

        # Snapshot manual task field instances for this privacy request
        privacy_request.create_manual_task_instances(
            session, get_connection_configs_with_manual_tasks(session)
        )

        ready_tasks = persist_new_consent_request_tasks(
            session, privacy_request, traversal_nodes, identity, graph
        )
        logger.info(
            "Consent processing: persisted {} consent task(s)",
            len(ready_tasks),
        )

    for task in ready_tasks:
        log_task_queued(task, "main runner")
        queue_request_task(task, privacy_request_proceed)
    logger.info(
        "Consent processing: queued {} task(s) for execution",
        len(ready_tasks),
    )
    return ready_tasks


def get_existing_ready_tasks(
    session: Session, privacy_request: PrivacyRequest, action_type: ActionType
) -> List[RequestTask]:
    """
    Return existing RequestTasks if applicable in the event of reprocessing instead
    of creating new ones
    """
    ready: List[RequestTask] = []
    request_task_count: int = privacy_request.get_tasks_by_action(action_type).count()
    if request_task_count > 0:
        # Defer loading large JSON columns to prevent OOM when reprocessing DSRs with many tasks
        base_query = privacy_request.get_tasks_by_action(action_type).filter(
            RequestTask.status.notin_(COMPLETED_EXECUTION_LOG_STATUSES)
        )
        incomplete_tasks: Query = RequestTask.query_with_deferred_data(base_query)

        for task in incomplete_tasks:
            # Checks if both upstream tasks are complete and the task is not currently in-flight (if using workers)
            if task.can_queue_request_task(session, should_log=True):
                task.update_status(session, ExecutionLogStatus.pending)
                ready.append(task)
            elif task.status == ExecutionLogStatus.error:
                # Important to reset errored status to pending so it can be rerun
                task.update_status(session, ExecutionLogStatus.pending)

        if ready:
            logger.info(
                "Found existing {} task(s) ready to reprocess: {}.",
                action_type.value,
                [t.collection_address for t in ready],
            )
        return ready
    return ready

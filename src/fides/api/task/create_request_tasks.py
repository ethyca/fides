# pylint: disable=too-many-lines
import json
from typing import Any, Dict, List, Optional, Set

import networkx
from loguru import logger
from networkx import NetworkXNoCycle
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import TraversalError
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
    FieldAddress,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import (
    ARTIFICIAL_NODES,
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
    TraversalDetails,
)
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.task.deprecated_graph_task import format_data_use_map_for_caching
from fides.api.task.execute_request_tasks import log_task_queued, queue_request_task
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.task.manual.manual_task_utils import (
    get_connection_configs_with_manual_tasks,
)
from fides.api.util.logger_context_utils import log_context


def _add_edge_if_no_nodes(
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    networkx_graph: networkx.DiGraph,
) -> None:
    """
    Adds an edge from the root node to the terminator node, altering the networkx_graph in-place.

    Handles edge case if there are no traversal nodes in the graph at all
    """
    if not traversal_nodes.items():
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS)


def build_access_networkx_digraph(
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    traversal: Traversal,
) -> networkx.DiGraph:
    """
    DSR 3.0: Builds an access networkx graph to get consistent formatting of nodes to build the Request Tasks,
    regardless of whether node is real or artificial.

    Primarily though, this lets us use networkx.descendants to calculate every node that can be reached from the current
    node to more easily mark downstream nodes as failed if the current node fails.
    """
    networkx_graph = networkx.DiGraph()
    networkx_graph.add_nodes_from(traversal_nodes.keys())
    networkx_graph.add_nodes_from(ARTIFICIAL_NODES)

    # The first nodes visited are the nodes that only need identity data.
    # Therefore, they are all immediately downstream of the root.
    first_nodes: Dict[FieldAddress, str] = traversal.extract_seed_field_addresses()

    for node in [
        CollectionAddress(initial_node.dataset, initial_node.collection)
        for initial_node in first_nodes
    ]:
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, node)

    for collection_address, traversal_node in traversal_nodes.items():
        for child in traversal_node.children:
            # For every node, add a downstream edge to its children
            # that were calculated in traversal.traverse
            networkx_graph.add_edge(collection_address, child)

    for node in end_nodes:
        # Connect the end nodes, those that have no downstream dependencies, to the terminator node
        networkx_graph.add_edge(node, TERMINATOR_ADDRESS)

    manual_nodes = [
        addr
        for addr in traversal_nodes.keys()
        if ManualTaskAddress.is_manual_task_address(addr)
    ]
    for manual_node in manual_nodes:
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, manual_node)

    _add_edge_if_no_nodes(traversal_nodes, networkx_graph)
    return networkx_graph


def _evaluate_erasure_dependencies(
    traversal_node: TraversalNode, end_nodes: List[CollectionAddress]
) -> Set[CollectionAddress]:
    """
    Return a set of collection addresses corresponding to collections that need
    to be erased before the given task.

    Remove the dependent collection addresses
    from `end_nodes` so they can be executed in the correct order. If a task does
    not have any dependencies it is linked directly to the root node
    """
    erase_after = traversal_node.node.collection.erase_after
    for collection in erase_after:
        if collection in end_nodes:
            # end_node list is modified in place
            end_nodes.remove(collection)
    # this task will execute after the collections in `erase_after` or
    # execute at the beginning by linking it to the root node
    if len(erase_after):
        erase_after.add(ROOT_COLLECTION_ADDRESS)
    return erase_after if len(erase_after) else {ROOT_COLLECTION_ADDRESS}


def build_erasure_networkx_digraph(
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
) -> networkx.DiGraph:
    """
    DSR 3.0: Builds a networkx graph of erasure nodes to get consistent formatting of nodes to build the Request Tasks,
    regardless of whether node is real or artificial.

    Erasure graphs are different from access graphs, in that we've queried all the data we need upfront in the access
    graphs, so that all nodes can in theory run entirely in parallel, except for the "erase_after" dependencies.

    We tack on the "erase_after" dependencies here that aren't captured in traversal.traverse.

    """
    networkx_graph = networkx.DiGraph()
    networkx_graph.add_nodes_from(traversal_nodes.keys())
    networkx_graph.add_nodes_from(ARTIFICIAL_NODES)

    for node_name, traversal_node in traversal_nodes.items():
        # Add an edge from the root node to the current node, unless explicit erasure
        # dependencies are defined. Modifies end_nodes in place
        erasure_dependencies: Set[CollectionAddress] = _evaluate_erasure_dependencies(
            traversal_node, end_nodes
        )
        for dep in erasure_dependencies:
            networkx_graph.add_edge(dep, node_name)

    for node in end_nodes:
        # Connect each end node without downstream dependencies to the terminator node
        networkx_graph.add_edge(node, TERMINATOR_ADDRESS)

    try:
        # Run extra checks on the graph since we potentially modified traversal_nodes
        networkx.find_cycle(networkx_graph, ROOT_COLLECTION_ADDRESS)
    except NetworkXNoCycle:
        logger.info("No cycles found as expected")
    else:
        raise TraversalError(
            "The values for the `erase_after` fields created a cycle in the DAG."
        )

    _add_edge_if_no_nodes(traversal_nodes, networkx_graph)
    return networkx_graph


def build_consent_networkx_digraph(
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
) -> networkx.DiGraph:
    """
    DSR 3.0: Builds a networkx graph of consent nodes to get consistent formatting of nodes to build the Request Tasks,
    regardless of whether node is real or artificial.
    """
    networkx_graph = networkx.DiGraph()
    networkx_graph.add_nodes_from(traversal_nodes.keys())
    networkx_graph.add_nodes_from([TERMINATOR_ADDRESS, ROOT_COLLECTION_ADDRESS])

    for collection_address, _ in traversal_nodes.items():
        # Consent graphs are simple. One node for every dataset (which has a mocked collection)
        # and no dependencies between nodes.
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, collection_address)
        networkx_graph.add_edge(collection_address, TERMINATOR_ADDRESS)

    _add_edge_if_no_nodes(traversal_nodes, networkx_graph)
    return networkx_graph


def base_task_data(
    graph: networkx.DiGraph,
    dataset_graph: DatasetGraph,
    privacy_request: PrivacyRequest,
    node: CollectionAddress,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
) -> Dict:
    """Build a dictionary of common RequestTask attributes that are shared for building
    access, consent, and erasure tasks"""

    collection_representation: Optional[Dict] = None
    traversal_details = {}

    if node not in ARTIFICIAL_NODES:
        # Save a representation of the collection that can be re-hydrated later
        # when executing the node, so we don't have to recalculate incoming
        # and outgoing edges.
        collection_representation = json.loads(
            # Serialize with duck typing so we get the nested sub fields as well
            dataset_graph.nodes[node].collection.model_dump_json(serialize_as_any=True)
        )

        # Saves traversal details based on data dependencies like incoming edges
        # and input keys, also useful for building the Execution Node
        if node in traversal_nodes:
            traversal_details = traversal_nodes[
                node
            ].format_traversal_details_for_save()
        else:
            # If node is not in traversal_nodes, then it is a node added for
            # custom request field processing. We manually build the traversal details,
            # with no incoming or outgoing edges and no input keys.
            graph_node = dataset_graph.nodes[node]
            traversal_details = TraversalDetails.create_empty_traversal(
                graph_node.dataset.connection_key
            ).model_dump(mode="json")

    return {
        "privacy_request_id": privacy_request.id,
        "upstream_tasks": sorted(
            [upstream.value for upstream in graph.predecessors(node)]
        ),
        "downstream_tasks": sorted(
            [downstream.value for downstream in graph.successors(node)]
        ),
        "all_descendant_tasks": sorted(
            [descend.value for descend in list(networkx.descendants(graph, node))]
        ),
        "collection_address": node.value,
        "dataset_name": node.dataset,
        "collection_name": node.collection,
        "status": (
            ExecutionLogStatus.complete
            if node == ROOT_COLLECTION_ADDRESS
            else ExecutionLogStatus.pending
        ),
        "collection": collection_representation,
        "traversal_details": traversal_details,
    }


def persist_new_access_request_tasks(
    session: Session,
    privacy_request: PrivacyRequest,
    traversal: Traversal,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    dataset_graph: DatasetGraph,
) -> List[RequestTask]:
    """
    Create individual access RequestTasks from the TraversalNodes and persist to the database.
    This should only run the first time a privacy request runs.
    """
    logger.info(
        "Creating access request tasks for privacy request {}.", privacy_request.id
    )
    graph: networkx.DiGraph = build_access_networkx_digraph(
        traversal_nodes, end_nodes, traversal
    )

    for node in list(networkx.topological_sort(graph)):
        if privacy_request.get_existing_request_task(
            session, action_type=ActionType.access, collection_address=node
        ):
            continue

        RequestTask.create(
            session,
            data={
                **base_task_data(
                    graph, dataset_graph, privacy_request, node, traversal_nodes
                ),
                "access_data": (
                    [traversal.seed_data] if node == ROOT_COLLECTION_ADDRESS else []
                ),  # For consistent treatment of nodes, add the seed data to the root node.  Subsequent
                # tasks will save the data collected on the same field.
                "action_type": ActionType.access,
            },
        )

    root_task: RequestTask = privacy_request.get_root_task_by_action(ActionType.access)

    return [root_task]


def persist_initial_erasure_request_tasks(
    session: Session,
    privacy_request: PrivacyRequest,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    dataset_graph: DatasetGraph,
) -> List[RequestTask]:
    """
    Create starter individual erasure RequestTasks from the TraversalNodes and persist to the database.

    These are not ready to run yet as they are still waiting for access data from the access graph
    to be able to build masking requests
    """
    logger.info(
        "Creating initial erasure request tasks for privacy request {}.",
        privacy_request.id,
    )
    graph: networkx.DiGraph = build_erasure_networkx_digraph(traversal_nodes, end_nodes)

    for node in list(networkx.topological_sort(graph)):
        if privacy_request.get_existing_request_task(
            session, action_type=ActionType.erasure, collection_address=node
        ):
            continue

        RequestTask.create(
            session,
            data={
                **base_task_data(
                    graph, dataset_graph, privacy_request, node, traversal_nodes
                ),
                "action_type": ActionType.erasure,
            },
        )

    # If a policy has an erasure rule, this method is run immediately after creating the access tasks, so their
    # nodes in the database are the same.  There are no "ready" tasks yet, because we need to wait for the
    # access step to run, so we return an empty list here.
    return []


def _get_data_for_erasures(
    session: Session, privacy_request: PrivacyRequest, request_task: RequestTask
) -> List[Dict]:
    """
    Return the access data in erasure format needed to format the masking request for the current node.
    """
    # Get the access task of the same name as the erasure task so we can transfer the data
    # collected for masking onto the current erasure task
    corresponding_access_task: Optional[RequestTask] = (
        privacy_request.get_existing_request_task(
            db=session,
            action_type=ActionType.access,
            collection_address=request_task.request_task_address,
        )
    )
    retrieved_task_data: List[Dict] = []
    if (
        corresponding_access_task
        and request_task.request_task_address not in ARTIFICIAL_NODES
    ):
        # IMPORTANT. Use "data_for_erasures" - not RequestTask.access_data.
        # For arrays, "access_data" may remove non-matched elements from arrays, but to build erasure
        # queries we need the original data in the appropriate indices
        retrieved_task_data = corresponding_access_task.get_data_for_erasures()

    return retrieved_task_data


def update_erasure_tasks_with_access_data(
    session: Session,
    privacy_request: PrivacyRequest,
) -> None:
    """
    Update individual erasure RequestTasks with data from the TraversalNodes and persist to the database.
    """
    logger.info(
        "Updating erasure request tasks with data needed for masking requests {}.",
        privacy_request.id,
    )

    for request_task in privacy_request.erasure_tasks:
        # I pull access data saved in the format suitable for erasures
        # off of the access nodes to be saved onto the erasure nodes.
        retrieved_task_data = _get_data_for_erasures(
            session, privacy_request, request_task
        )
        request_task.data_for_erasures = retrieved_task_data
        request_task.save(session)


def persist_new_consent_request_tasks(
    session: Session,
    privacy_request: PrivacyRequest,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    identity: Dict[str, Any],
    dataset_graph: DatasetGraph,
) -> List[RequestTask]:
    """
    Create individual erasure RequestTasks from the TraversalNodes and persist to the database.  This should only
    run the first time a privacy request runs.

    Consent propagation graphs are much simpler with no relationships between nodes. Every node has identity data input,
    and every node outputs whether the consent request succeeded.
    """
    graph: networkx.DiGraph = build_consent_networkx_digraph(traversal_nodes)

    for node in list(networkx.topological_sort(graph)):
        if privacy_request.get_existing_request_task(
            session, action_type=ActionType.consent, collection_address=node
        ):
            continue
        RequestTask.create(
            session,
            data={
                **base_task_data(
                    graph, dataset_graph, privacy_request, node, traversal_nodes
                ),
                # Consent nodes take in identity data from their upstream root node
                "access_data": ([identity] if node == ROOT_COLLECTION_ADDRESS else []),
                "action_type": ActionType.consent,
            },
        )

    root_task: RequestTask = privacy_request.get_root_task_by_action(ActionType.consent)

    return [root_task]


def collect_tasks_fn(
    tn: TraversalNode, data: Dict[CollectionAddress, TraversalNode]
) -> None:
    """
    A function that is passed to traversal.traverse() that returns the modified
    traversal node with its parents and children linked as an action.
    """
    if not tn.is_root_node():
        data[tn.address] = tn


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
        ready_tasks: List[RequestTask] = get_existing_ready_tasks(
            session, privacy_request, ActionType.consent
        )
    else:
        logger.info("Building consent graph")
        traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}
        # Unlike erasure and access graphs, we don't call traversal.traverse, but build a simpler
        # graph that just has one node per dataset
        for col_address, node in graph.nodes.items():
            traversal_node = TraversalNode(node)
            traversal_nodes[col_address] = traversal_node

        ready_tasks = persist_new_consent_request_tasks(
            session, privacy_request, traversal_nodes, identity, graph
        )

    for task in ready_tasks:
        log_task_queued(task, "main runner")
        queue_request_task(task, privacy_request_proceed)
    return ready_tasks


def get_existing_ready_tasks(
    session: Session, privacy_request: PrivacyRequest, action_type: ActionType
) -> List[RequestTask]:
    """
    Return existing RequestTasks if applicable in the event of reprocessing instead
    of creating new ones
    """
    ready: List[RequestTask] = []
    request_tasks: Query = privacy_request.get_tasks_by_action(action_type)
    if request_tasks.count():
        incomplete_tasks: Query = request_tasks.filter(
            RequestTask.status.notin_(COMPLETED_EXECUTION_LOG_STATUSES)
        )

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

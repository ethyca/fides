# pylint: disable=too-many-lines
import json
from typing import Any, Dict, List, Optional, Set, Tuple

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
    format_traversal_details_for_save,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequest,
    RequestTask,
    TraversalDetails,
    completed_statuses,
)
from fides.api.schemas.policy import ActionType
from fides.api.task.deprecated_graph_task import format_data_use_map_for_caching
from fides.api.task.execute_request_tasks import (
    run_access_node,
    run_consent_node,
    run_erasure_node,
)
from fides.api.util.cache import CustomJSONEncoder
from fides.api.util.collection_util import Row


def build_access_networkx_digraph(
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    traversal: Traversal,
) -> networkx.DiGraph:
    """
    Builds an access networkx graph to get consistent formatting of nodes, regardless of whether node is real or artificial.

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

    add_edge_if_no_nodes(traversal_nodes, networkx_graph)
    return networkx_graph


def _evaluate_erasure_dependencies(
    traversal_node: TraversalNode, end_nodes: List[CollectionAddress]
) -> Set[CollectionAddress]:
    """
    Return a set of collection addresses corresponding to collections that need
    to be erased before the given task. Remove the dependent collection addresses
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
    Builds a networkx graph of erasure nodes to get consistent formatting of nodes, regardless of whether node is real or artificial.

    Erasure graphs are different from access graphs, in that we've queried all the data we need upfront in the access
    graphs, so the nodes can in theory run entirely in parallel, except for the "erase_after" dependencies.

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

    add_edge_if_no_nodes(traversal_nodes, networkx_graph)
    return networkx_graph


def add_edge_if_no_nodes(
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    networkx_graph: networkx.DiGraph,
):
    """Handle edge case of there are no traversal nodes in the graph at all
    Just connect the root node to the terminator node
    """
    if not traversal_nodes.items():
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS)


def build_consent_networkx_digraph(
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
) -> networkx.DiGraph:
    """
    Builds a networkx graph of consent nodes to get consistent formatting of nodes, regardless of whether node is real or artificial.
    """
    networkx_graph = networkx.DiGraph()
    networkx_graph.add_nodes_from(traversal_nodes.keys())
    networkx_graph.add_nodes_from([TERMINATOR_ADDRESS, ROOT_COLLECTION_ADDRESS])

    for collection_address, _ in traversal_nodes.items():
        # Consent graphs are simple. One node for every dataset (which has a mocked collection)
        # and no dependencies between nodes.
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, collection_address)
        networkx_graph.add_edge(collection_address, TERMINATOR_ADDRESS)

    add_edge_if_no_nodes(traversal_nodes, networkx_graph)
    return networkx_graph


def _order_tasks_by_input_key(
    input_keys: List[CollectionAddress], upstream_tasks: Query
) -> List[Optional[RequestTask]]:
    """Order tasks by input key. If task doesn't exist, add None in its place"""
    tasks: List[Optional[RequestTask]] = []
    for key in input_keys:
        task = next(
            (
                upstream
                for upstream in upstream_tasks
                if upstream.collection_address == key.value
            ),
            None,
        )
        tasks.append(task)
    return tasks


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
    if node not in ARTIFICIAL_NODES:
        # Save a representation of the collection that can be re-hydrated later
        # when executing the node
        collection_representation = json.loads(
            dataset_graph.nodes[node].collection.json()
        )

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
        "status": ExecutionLogStatus.complete
        if node == ROOT_COLLECTION_ADDRESS
        else ExecutionLogStatus.pending,
        "collection": collection_representation,
        "traversal_details": format_traversal_details_for_save(node, traversal_nodes),
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
                "access_data": json.dumps([traversal.seed_data], cls=CustomJSONEncoder)
                if node == ROOT_COLLECTION_ADDRESS
                else [],
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

    return []


def _get_data_for_erasures(
    session: Session, privacy_request: PrivacyRequest, request_task: RequestTask
) -> Tuple[List[Dict], List[List[Row]]]:
    """
    Return the access data in erasure format needed to format the masking request for the current node.
    """
    corresponding_access_task: Optional[
        RequestTask
    ] = privacy_request.get_existing_request_task(
        db=session,
        action_type=ActionType.access,
        collection_address=request_task.request_task_address,
    )
    retrieved_task_data: List[Dict] = []
    combined_input_data: List[List[Row]] = []
    if (
        corresponding_access_task
        and not request_task.request_task_address in ARTIFICIAL_NODES
    ):
        # IMPORTANT. Use "data_for_erasures" - not RequestTask.access_data.
        # For arrays, "access_data" may remove non-matched elements, but to build erasure
        # queries we need the original data in the appropriate indices
        retrieved_task_data = corresponding_access_task.get_decoded_data_for_erasures()

        traversal_details = TraversalDetails.parse_obj(
            request_task.traversal_details or {}
        )

        # Select tasks from input keys (which are built based on data depenendencies), rather than upstream
        # tasks here.  We want the access data that was fed into the node of the same name.  This is
        # for things like email erasure nodes, where the access node of the same name didn't fetch results.
        input_tasks: Query = session.query(RequestTask).filter(
            RequestTask.privacy_request_id == privacy_request.id,
            RequestTask.action_type == ActionType.access,
            RequestTask.collection_address.in_(traversal_details.input_keys or []),
            RequestTask.status == ExecutionLogStatus.complete,
        )

        input_keys = [
            CollectionAddress.from_string(input_key)
            for input_key in traversal_details.input_keys
        ]

        ordered_access_tasks_by_input_key: List[
            Optional[RequestTask]
        ] = _order_tasks_by_input_key(input_keys, input_tasks)

        for input_data in ordered_access_tasks_by_input_key or []:
            combined_input_data.append(
                input_data.get_decoded_data_for_erasures() or [] if input_data else []
            )

    return retrieved_task_data, combined_input_data


def update_erasure_tasks_with_access_data(
    session: Session,
    privacy_request: PrivacyRequest,
) -> List[RequestTask]:
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
        retrieved_task_data, combined_input_data = _get_data_for_erasures(
            session, privacy_request, request_task
        )
        request_task.data_for_erasures = json.dumps(
            retrieved_task_data, cls=CustomJSONEncoder
        )
        request_task.erasure_input_data = json.dumps(
            combined_input_data, cls=CustomJSONEncoder
        )
        request_task.save(session)

    return []


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
                "access_data": json.dumps([identity], cls=CustomJSONEncoder)
                if node == ROOT_COLLECTION_ADDRESS
                else [],
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


def log_task_queued(request_task: RequestTask) -> None:
    logger.info(
        "Queuing {} task {} from main runner. Privacy Request: {}, Request Task {}",
        request_task.action_type.value,
        request_task.collection_address,
        request_task.privacy_request_id,
        request_task.id,
    )


def run_access_request(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
    queue_privacy_request: bool = True,
) -> List[RequestTask]:
    """
    Build the "access" graph, add its tasks to the database and queue the root task.

    If we are reprocessing a Privacy Request, instead queue tasks whose upstream nodes are complete.
    """
    ready_tasks: List[RequestTask] = get_existing_ready_tasks(
        session, privacy_request, ActionType.access
    )
    if not privacy_request.access_tasks.count():
        logger.info("Building access graph for {}", privacy_request.id)
        traversal: Traversal = Traversal(graph, identity)

        # Traversal.traverse populates traversal_nodes in place, adding parents and children to each traversal_node.
        traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}
        end_nodes: List[CollectionAddress] = traversal.traverse(
            traversal_nodes, collect_tasks_fn
        )
        # Save Access Request Tasks to the database
        ready_tasks: List[RequestTask] = persist_new_access_request_tasks(
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

    for task in ready_tasks:
        log_task_queued(task)
        run_access_node.delay(privacy_request.id, task.id, queue_privacy_request)

    return ready_tasks


def run_erasure_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    session: Session,
    queue_privacy_request: bool = True,
) -> List[RequestTask]:
    """
    Build the "erasure" graph, add its tasks to the database and queue the root task.

    If we are reprocessing a Privacy Request, instead queue tasks whose upstream nodes are complete.
    """
    update_erasure_tasks_with_access_data(session, privacy_request)
    ready_tasks: List[RequestTask] = (
        get_existing_ready_tasks(session, privacy_request, ActionType.erasure) or []
    )

    for task in ready_tasks:
        log_task_queued(task)
        run_erasure_node.delay(privacy_request.id, task.id, queue_privacy_request)
    return ready_tasks


def run_consent_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
    queue_privacy_request: bool = True,
) -> List[RequestTask]:
    """
    Build the "consent" graph, add its tasks to the database and queue the root task.

    If we are reprocessing a Privacy Request, instead queue tasks whose upstream nodes are complete.

    The graph built is very simple: there are no relationships between the nodes, every node has
    identity data input and every node outputs whether the consent request succeeded.

    The DatasetGraph passed in is expected to have one Node per Dataset.  That Node is expected to carry out requests
    for the Dataset as a whole.
    """
    ready_tasks: List[RequestTask] = get_existing_ready_tasks(
        session, privacy_request, ActionType.consent
    )
    if not privacy_request.consent_tasks.count():
        logger.info("Building consent graph for {}", privacy_request.id)
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
        log_task_queued(task)
        run_consent_node.delay(privacy_request.id, task.id, queue_privacy_request)
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
            RequestTask.status.notin_(completed_statuses)
        )

        for task in incomplete_tasks:
            if task.upstream_tasks_complete(session):
                task.update_status(session, ExecutionLogStatus.pending)
                ready.append(task)
            elif task.status == ExecutionLogStatus.error:
                # Important to reset errored status to pending so it can be rerun
                task.update_status(session, ExecutionLogStatus.pending)

        if ready:
            logger.info(
                "Found existing {} task(s) ready to reprocess: {}. Privacy Request: {}",
                action_type.value,
                [t.collection_address for t in ready],
                privacy_request.id,
            )
        return ready
    return ready

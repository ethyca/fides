# pylint: disable=too-many-lines
import json
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx
from fideslang.validation import FidesKey
from loguru import logger
from networkx import NetworkXNoCycle
from sqlalchemy.orm import Query, Session

from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
    FieldAddress,
)
from fides.api.graph.execution import TraversalDetails
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.privacy_request import PrivacyRequest, RequestTask, TaskStatus
from fides.api.schemas.policy import ActionType
from fides.api.task.execute_tasks import (
    run_access_node,
    run_consent_node,
    run_erasure_node,
)
from fides.api.util.collection_util import Row

ARTIFICIAL_NODES: List[CollectionAddress] = [
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
]


def _format_traversal_details_for_save(
    node: CollectionAddress, env: Dict[CollectionAddress, TraversalNode]
) -> Dict:
    """Format selected TraversalNode details in a way they can be saved in the database.

    This will let us execute the node when ready without having to reconstruct the traversal node later.
    """
    if node in ARTIFICIAL_NODES:
        return {}

    traversal_node: TraversalNode = env[node]
    connection_key: FidesKey = traversal_node.node.dataset.connection_key

    return TraversalDetails(
        dataset_connection_key=connection_key,
        incoming_edges=[
            [edge.f1.value, edge.f2.value] for edge in traversal_node.incoming_edges()
        ],
        outgoing_edges=[
            [edge.f1.value, edge.f2.value] for edge in traversal_node.outgoing_edges()
        ],
        input_keys=[tn.value for tn in traversal_node.input_keys()],
    ).dict()


def build_access_networkx_digraph(
    env: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    traversal: Traversal,
) -> networkx.DiGraph:
    """
    Builds an access networkx graph to get consistent formatting of nodes, regardless of whether node is real or artificial.

    Primarily though, this lets us use networkx.descendants to calculate every node that can be reached from the current
    node to more easily mark downstream nodes as failed if the current node fails.
    """
    networkx_graph = networkx.DiGraph()
    networkx_graph.add_nodes_from(env.keys())
    networkx_graph.add_nodes_from(ARTIFICIAL_NODES)

    # The first nodes visited are the nodes that only need identity data.
    # Therefore, they are all immediately downstream of the root.
    first_nodes: Dict[FieldAddress, str] = traversal.extract_seed_field_addresses()

    for node in [
        CollectionAddress(initial_node.dataset, initial_node.collection)
        for initial_node in first_nodes
    ]:
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, node)

    for collection_address, traversal_node in env.items():
        for child in traversal_node.children:
            # For every node, add a downstream edge to its children
            # that were calculated in traversal.traverse
            networkx_graph.add_edge(collection_address, child)

    for node in end_nodes:
        # Connect the end nodes, those that have no downstream dependencies, to the terminator node
        networkx_graph.add_edge(node, TERMINATOR_ADDRESS)

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
    return erase_after if len(erase_after) else {ROOT_COLLECTION_ADDRESS}


def build_erasure_networkx_digraph(
    traversal_nodes: Dict[CollectionAddress, Any],
    end_nodes: List[CollectionAddress],
) -> networkx.DiGraph:
    """
    Builds a networkx graph of erasure nodes to get consistent formatting of nodes, regardless of whether node is real or artificial.

    In addition, a major benefit is adding in "erase_after" dependencies that aren't captured in traversal.traverse
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
        raise Exception("Cycles found in erasure DAG")

    return networkx_graph


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
    """Build a dictionary of common RequestTask attributes that are shared between
    access, consent, and erasures"""
    collection_representation: Optional[Dict] = None
    if node not in ARTIFICIAL_NODES:
        # Save a representation of the collection that can be re-hydrated later
        # when executing the node
        collection_representation = json.loads(
            dataset_graph.nodes[node].collection.json()
        )

    return {
        "privacy_request_id": privacy_request.id,
        "upstream_tasks": [upstream.value for upstream in graph.predecessors(node)],
        "downstream_tasks": [downstream.value for downstream in graph.successors(node)],
        "all_descendant_tasks": [
            descend.value for descend in list(networkx.descendants(graph, node))
        ],
        "collection_address": node.value,
        "dataset_name": node.dataset,
        "collection_name": node.collection,
        "status": TaskStatus.complete
        if node == ROOT_COLLECTION_ADDRESS
        else TaskStatus.pending,
        "collection": collection_representation,
        "traversal_details": _format_traversal_details_for_save(node, traversal_nodes),
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
                "access_data": [traversal.seed_data]
                if node == ROOT_COLLECTION_ADDRESS
                else [],
                "action_type": ActionType.access,
            },
        )

    root_task: RequestTask = privacy_request.get_root_task_by_action(ActionType.access)

    return [root_task]


def _get_data_for_erasures(
    session: Session,
    privacy_request: PrivacyRequest,
    node: CollectionAddress,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
) -> Tuple[List[Dict], List[List[Row]]]:
    """
    Return the access data in erasure format needed to format the masking request for the current node.
    """
    corresponding_access_task: Optional[
        RequestTask
    ] = privacy_request.get_existing_request_task(
        db=session, action_type=ActionType.access, collection_address=node
    )
    retrieved_task_data: List[Dict] = []
    combined_input_data: List[List[Row]] = []
    if corresponding_access_task:
        # IMPORTANT. Use "data_for_erasures" - not RequestTask.access_data.
        # For arrays, "access_data" may remove non-matched elements, but to build erasure
        # queries we need the original data in the appropriate indices
        retrieved_task_data = corresponding_access_task.data_for_erasures

        # Select upstream inputs of this node for things like email connectors, which
        # don't retrieve data directly
        input_tasks: Query = session.query(RequestTask).filter(
            RequestTask.privacy_request_id == privacy_request.id,
            RequestTask.action_type == ActionType.access,
            RequestTask.collection_address.in_(
                corresponding_access_task.upstream_tasks
            ),
            RequestTask.status == TaskStatus.complete,
        )
        ordered_upstream_tasks: List[Optional[RequestTask]] = (
            []
            if node in ARTIFICIAL_NODES
            else _order_tasks_by_input_key(
                traversal_nodes[node].input_keys(), input_tasks
            )
        )

        for input_data in ordered_upstream_tasks or []:
            combined_input_data.append(
                input_data.data_for_erasures or [] if input_data else []
            )

    return retrieved_task_data, combined_input_data


def persist_new_erasure_request_tasks(
    session: Session,
    privacy_request: PrivacyRequest,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    dataset_graph: DatasetGraph,
) -> List[RequestTask]:
    """
    Create individual erasure RequestTasks from the TraversalNodes and persist to the database.
    This should only run the first time a privacy request runs.
    """
    logger.info(
        "Creating erasure request tasks for privacy request {}.", privacy_request.id
    )
    graph: networkx.DiGraph = build_erasure_networkx_digraph(traversal_nodes, end_nodes)

    for node in list(networkx.topological_sort(graph)):
        if privacy_request.get_existing_request_task(
            session, action_type=ActionType.erasure, collection_address=node
        ):
            continue

        retrieved_task_data, combined_input_data = _get_data_for_erasures(
            session, privacy_request, node, traversal_nodes
        )

        RequestTask.create(
            session,
            data={
                **base_task_data(
                    graph, dataset_graph, privacy_request, node, traversal_nodes
                ),
                "data_for_erasures": retrieved_task_data,
                "erasure_input_data": combined_input_data,
                "action_type": ActionType.erasure,
            },
        )

    root_task: RequestTask = privacy_request.get_root_task_by_action(ActionType.erasure)

    return [root_task]


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
                "consent_data": identity if node == ROOT_COLLECTION_ADDRESS else {},
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
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
) -> List[RequestTask]:
    """
    Build the "access" graph, add its tasks to the database and queue the root task.

    If we are reprocessing a Privacy Request, instead queue tasks whose upstream nodes are complete.
    """
    ready_tasks: List[RequestTask] = get_existing_ready_tasks(
        session, privacy_request, ActionType.access
    )
    if not ready_tasks:
        logger.info("Building access graph for {}", privacy_request.id)
        traversal: Traversal = Traversal(graph, identity)

        # Traversal.traverse populates traversal_nodes in place, adding parents and children to each traversal_node.
        traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}
        end_nodes: List[CollectionAddress] = traversal.traverse(
            traversal_nodes, collect_tasks_fn
        )
        ready_tasks = persist_new_access_request_tasks(
            session, privacy_request, traversal, traversal_nodes, end_nodes, graph
        )

    for task in ready_tasks:
        log_task_queued(task)
        run_access_node.delay(privacy_request.id, task.id)
    return ready_tasks


def run_erasure_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
) -> List[RequestTask]:
    """
    Build the "erasure" graph, add its tasks to the database and queue the root task.

    If we are reprocessing a Privacy Request, instead queue tasks whose upstream nodes are complete.
    """
    ready_tasks: List[RequestTask] = get_existing_ready_tasks(
        session, privacy_request, ActionType.access
    )
    if not ready_tasks:
        logger.info("Building erasure graph for {}", privacy_request.id)
        traversal: Traversal = Traversal(graph, identity)

        traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}
        # Traversal.traverse populates traversal_nodes in place, adding parents and children to each traversal_node.
        traversal.traverse(traversal_nodes, collect_tasks_fn)
        # Unlike access requests, for erasures, all tasks are linked to the terminator node.
        erasure_end_nodes: List[CollectionAddress] = list(graph.nodes.keys())

        ready_tasks = persist_new_erasure_request_tasks(
            session, privacy_request, traversal_nodes, erasure_end_nodes, graph
        )

    for task in ready_tasks:
        log_task_queued(task)
        run_erasure_node.delay(privacy_request.id, task.id)
    return ready_tasks


def run_consent_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
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
    if not ready_tasks:
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
        run_consent_node.delay(privacy_request.id, task.id)
    return ready_tasks


def get_existing_ready_tasks(
    session: Session, privacy_request: PrivacyRequest, action_type: ActionType
) -> List[RequestTask]:
    """
    Return existing RequestTasks if applicable in the event of reprocessing instead
    of creating new ones
    """
    ready: List[RequestTask] = []
    request_tasks = privacy_request.get_tasks_by_action(action_type)
    if request_tasks.count():
        incomplete_tasks: Query = request_tasks.filter(
            RequestTask.status != TaskStatus.complete
        )
        for task in incomplete_tasks:
            if task.upstream_tasks_complete(session):
                task.update_status(session, TaskStatus.pending)
                ready.append(task)
            elif task.status == TaskStatus.error:
                task.update_status(session, TaskStatus.pending)

        if ready:
            logger.info(
                "Found existing {} task(s) read to reprocess: {}. Privacy Request: {}",
                action_type.value,
                [t.collection_address for t in ready],
                privacy_request.id,
            )
        return ready
    return ready

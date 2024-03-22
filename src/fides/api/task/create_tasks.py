# pylint: disable=too-many-lines
import json
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx
from dask import delayed  # type: ignore[attr-defined]
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
    connection_key = traversal_node.node.dataset.connection_key

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
    Builds a networkx graph to get consistent formatting of upstream/downstream nodes, regardless of whether the node
    is an actual node, or a "root"/"terminator" node.

    Primarily though, we can utilize networkx's "descendants" method to pre-calculate every downstream node that
    can be reached by each current node
    """
    first_nodes: Dict[FieldAddress, str] = traversal.extract_seed_field_addresses()

    networkx_graph = networkx.DiGraph()
    networkx_graph.add_nodes_from(env.keys())
    networkx_graph.add_nodes_from([TERMINATOR_ADDRESS, ROOT_COLLECTION_ADDRESS])

    for node in [
        CollectionAddress(initial_node.dataset, initial_node.collection)
        for initial_node in first_nodes
    ]:
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, node)

    for collection_address, traversal_node in env.items():
        for child in traversal_node.children:
            networkx_graph.add_edge(collection_address, child)

    for node in end_nodes:
        networkx_graph.add_edge(node, TERMINATOR_ADDRESS)

    return networkx_graph


def persist_access_request_tasks(
    session: Session,
    privacy_request: PrivacyRequest,
    traversal: Traversal,
    traversal_nodes: Dict[CollectionAddress, Any],
    end_nodes: List[CollectionAddress],
    dataset_graph: DatasetGraph,
) -> Tuple[RequestTask, List[RequestTask]]:
    """
    Create individual RequestTasks from the TraversalNodes and persist to the database.
    """
    logger.info(
        "Creating access request tasks for privacy request {}.", privacy_request.id
    )
    graph: networkx.DiGraph = build_access_networkx_digraph(
        traversal_nodes, end_nodes, traversal
    )

    ready_tasks: List[RequestTask] = []

    for node in list(networkx.topological_sort(graph)):
        existing_task = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == ActionType.access,
                RequestTask.collection_address == node.value,
            )
            .first()
        )
        if existing_task:
            logger.info(
                "Existing task already exists {}",
                existing_task.collection_address,
                existing_task.action_type,
            )
            continue

        collection_representation: Optional[Dict] = None
        if node not in ARTIFICIAL_NODES:
            collection_representation = json.loads(
                dataset_graph.nodes[node].collection.json()
            )

        task = RequestTask.create(
            session,
            data={
                "privacy_request_id": privacy_request.id,
                "upstream_tasks": [
                    upstream.value for upstream in graph.predecessors(node)
                ],
                "downstream_tasks": [
                    downstream.value for downstream in graph.successors(node)
                ],
                "dataset_name": node.dataset,
                "collection_name": node.collection,
                "status": TaskStatus.complete
                if node == ROOT_COLLECTION_ADDRESS
                else TaskStatus.pending,
                "access_data": [traversal.seed_data]
                if node == ROOT_COLLECTION_ADDRESS
                else [],
                "action_type": ActionType.access,
                "collection_address": node.value,
                "all_descendant_tasks": [
                    descend.value for descend in list(networkx.descendants(graph, node))
                ],
                "collection": collection_representation,
                "traversal_details": _format_traversal_details_for_save(
                    node, traversal_nodes
                ),
            },
        )
        ready_tasks.append(task)

    root_task: Optional[RequestTask] = privacy_request.get_root_task_by_action(
        ActionType.access
    )

    return root_task, ready_tasks


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
    env: Dict[CollectionAddress, Any],
    end_nodes: List[CollectionAddress],
) -> networkx.DiGraph:
    """
    Builds a networkx graph to get consistent formatting of upstream/downstream nodes, regardless of whether the node
    is an actual node, or a "root"/"terminator" node.

    Primarily though, we can utilize networkx's "descendants" method to pre-calculate every downstream node that
    can be reached by each current node
    """
    networkx_graph = networkx.DiGraph()
    networkx_graph.add_nodes_from(env.keys())
    networkx_graph.add_nodes_from([ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS])

    for node_name, traversal_node in env.items():
        # Modifies end nodes in place as well?
        erasure_dependencies = _evaluate_erasure_dependencies(traversal_node, end_nodes)
        for dep in erasure_dependencies:
            networkx_graph.add_edge(dep, node_name)

    for node in end_nodes:
        networkx_graph.add_edge(node, TERMINATOR_ADDRESS)

    try:
        networkx.find_cycle(networkx_graph, ROOT_COLLECTION_ADDRESS)
    except NetworkXNoCycle:
        logger.info("No cycles found as expected")
    else:
        raise Exception("Cycles found in erasure DAG")

    return networkx_graph


def order_tasks_by_input_key(
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


def persist_erasure_request_tasks(
    session: Session,
    privacy_request: PrivacyRequest,
    env: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    dataset_graph: DatasetGraph,
):
    """
    Erasure tasks need to access the Access Tasks.erasure_data
    """
    logger.info(
        "Creating erasure request tasks for privacy request {}.", privacy_request.id
    )
    graph: networkx.DiGraph = build_erasure_networkx_digraph(env, end_nodes)

    ready_tasks: List[RequestTask] = []

    for node in list(networkx.topological_sort(graph)):
        existing_task = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == ActionType.erasure,
                RequestTask.collection_address == node.value,
            )
            .first()
        )

        if existing_task:
            continue

        # Select ACCESS task of the same name
        corresponding_access_task = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == ActionType.access,
                RequestTask.collection_address == node.value,
                RequestTask.status == TaskStatus.complete,
            )
            .first()
        )
        retrieved_task_data: List[Dict] = []
        if corresponding_access_task:
            # IMPORTANT. Use "data_for_erasures" - not RequestTask.access_data
            retrieved_task_data = corresponding_access_task.data_for_erasures

        # Select upstream inputs of this node for things like email connectors
        input_tasks: Query = session.query(RequestTask).filter(
            RequestTask.privacy_request_id == privacy_request.id,
            RequestTask.action_type == ActionType.access,
            RequestTask.collection_address.in_(
                corresponding_access_task.upstream_tasks
            ),
            RequestTask.status == TaskStatus.complete,
        )
        ordered_upstream_tasks = (
            []
            if node in ARTIFICIAL_NODES
            else order_tasks_by_input_key(env[node].input_keys(), input_tasks)
        )

        combined_input_data = []
        for input_data in ordered_upstream_tasks or []:
            combined_input_data.append(input_data.data_for_erasures or [])

        json_collection: Optional[Dict] = None
        if node not in ARTIFICIAL_NODES:
            json_collection = json.loads(dataset_graph.nodes[node].collection.json())

        task = RequestTask.create(
            session,
            data={
                "privacy_request_id": privacy_request.id,
                "upstream_tasks": [
                    upstream.value for upstream in graph.predecessors(node)
                ],
                "downstream_tasks": [
                    downstream.value for downstream in graph.successors(node)
                ],
                "dataset_name": node.dataset,
                "collection_name": node.collection,
                "status": TaskStatus.complete
                if node == ROOT_COLLECTION_ADDRESS
                else TaskStatus.pending,
                "data_for_erasures": retrieved_task_data,
                "erasure_input_data": combined_input_data,
                "action_type": ActionType.erasure,
                "collection_address": node.value,
                "all_descendant_tasks": [
                    descend.value for descend in list(networkx.descendants(graph, node))
                ],
                "collection": json_collection,
                "traversal_details": _format_traversal_details_for_save(node, env),
            },
        )
        ready_tasks.append(task)

    root_task: Optional[RequestTask] = privacy_request.get_root_task_by_action(
        ActionType.erasure
    )

    return root_task, ready_tasks


def build_consent_networkx_digraph(
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
) -> networkx.DiGraph:
    """
    Builds a networkx graph to get consistent formatting of upstream/downstream nodes, regardless of whether the node
    is an actual node, or a "root"/"terminator" node.

    Primarily though, we can utilize networkx's "descendants" method to pre-calculate every downstream node that
    can be reached by each current node
    """
    networkx_graph = networkx.DiGraph()
    networkx_graph.add_nodes_from(traversal_nodes.keys())
    networkx_graph.add_nodes_from([TERMINATOR_ADDRESS, ROOT_COLLECTION_ADDRESS])

    for collection_address, traversal_node in traversal_nodes.items():
        networkx_graph.add_edge(ROOT_COLLECTION_ADDRESS, collection_address)
        networkx_graph.add_edge(collection_address, TERMINATOR_ADDRESS)

    return networkx_graph


def persist_consent_request_tasks(
    session: Session,
    privacy_request: PrivacyRequest,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    identity: Dict[str, Any],
    dataset_graph: DatasetGraph,
):
    """
    The graph built is very simple: there are no relationships between the nodes, every node has
    identity data input and every node outputs whether the consent request succeeded.

    The DatasetGraph passed in is expected to have one Node per Dataset.  That Node is expected to carry out requests
    for the Dataset as a whole.

    """
    graph: networkx.DiGraph = build_consent_networkx_digraph(traversal_nodes)

    ready_tasks: List[RequestTask] = []

    for node in list(networkx.topological_sort(graph)):
        existing_task = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == ActionType.consent,
                RequestTask.collection_address == node.value,
            )
            .first()
        )

        if existing_task:
            continue

        collection_representation: Optional[Dict] = None
        if node not in ARTIFICIAL_NODES:
            collection_representation = json.loads(
                dataset_graph.nodes[node].collection.json()
            )

        task = RequestTask.create(
            session,
            data={
                "privacy_request_id": privacy_request.id,
                "upstream_tasks": [
                    upstream.value for upstream in graph.predecessors(node)
                ],
                "downstream_tasks": [
                    downstream.value for downstream in graph.successors(node)
                ],
                "dataset_name": node.dataset,
                "collection_name": node.collection,
                "status": TaskStatus.complete
                if node == ROOT_COLLECTION_ADDRESS
                else TaskStatus.pending,
                "consent_data": identity if node == ROOT_COLLECTION_ADDRESS else {},
                "action_type": ActionType.consent,
                "collection_address": node.value,
                "all_descendant_tasks": [
                    descend.value for descend in list(networkx.descendants(graph, node))
                ],
                "collection": collection_representation,
                "traversal_details": _format_traversal_details_for_save(
                    node, traversal_nodes
                ),
            },
        )
        ready_tasks.append(task)

    root_task: Optional[RequestTask] = privacy_request.get_root_task_by_action(
        ActionType.consent
    )

    return root_task, ready_tasks


def collect_tasks_fn(
    tn: TraversalNode, data: Dict[CollectionAddress, TraversalNode]
) -> None:
    """
    A function that is passed to traversal.traverse() that returns the modified
    traversal node with its parents and children linked as an action.
    """
    if not tn.is_root_node():
        data[tn.address] = tn


def run_access_request(
    privacy_request: PrivacyRequest,
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
) -> None:
    """
    Build the "access" graph, add its tasks to the database and queue the root task.
    """
    traversal: Traversal = Traversal(graph, identity)

    # Traversal.traverse populates traversal_nodes in place, adding parents and children to each traversal_node.
    traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}
    end_nodes: List[CollectionAddress] = traversal.traverse(
        traversal_nodes, collect_tasks_fn
    )

    root_task, pending_request_tasks = persist_access_request_tasks(
        session, privacy_request, traversal, traversal_nodes, end_nodes, graph
    )
    # TODO handle if root task doesn't exist
    if not root_task:
        raise Exception()

    logger.info(
        "Queuing access task {}. Privacy Request: {}, Request Task {}",
        root_task.collection_address,
        privacy_request.id,
        root_task.id,
    )

    run_access_node.delay(privacy_request.id, root_task.id)
    return


def run_erasure_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
) -> List[RequestTask]:
    """
    Build the "erasure" graph, add its tasks to the database and queue the root task.
    """
    logger.info("Building erasure graph")
    traversal: Traversal = Traversal(graph, identity)

    env: Dict[CollectionAddress, TraversalNode] = {}
    # Traversal.traverse populates traversal_nodes in place, adding parents and children to each traversal_node.
    traversal.traverse(env, collect_tasks_fn)
    # Unlike access requests, for erasures, all tasks are linked to the terminator node.
    erasure_end_nodes = list(graph.nodes.keys())

    root_task, pending_erasure_tasks = persist_erasure_request_tasks(
        session, privacy_request, env, erasure_end_nodes, graph
    )

    # TODO handle if root task doesn't exist
    if not root_task:
        raise Exception()

    logger.info(
        "Queuing erasure task {}. Privacy Request: {}, Request Task {}",
        root_task.collection_address,
        privacy_request.id,
        root_task.id,
    )

    run_erasure_node.delay(privacy_request.id, root_task.id)
    return pending_erasure_tasks


def run_consent_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
) -> None:
    """
    Build the "consent" graph, add its tasks to the database and queue the root task.

    The graph built is very simple: there are no relationships between the nodes, every node has
    identity data input and every node outputs whether the consent request succeeded.

    The DatasetGraph passed in is expected to have one Node per Dataset.  That Node is expected to carry out requests
    for the Dataset as a whole.
    """
    traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}
    # Unlike erasure and access graphs, we don't call traversal.traverse, but build a simpler
    # graph that just has all the datasets in it
    for col_address, node in graph.nodes.items():
        traversal_node = TraversalNode(node)
        traversal_nodes[col_address] = traversal_node

    root_task, pending_request_tasks = persist_consent_request_tasks(
        session, privacy_request, traversal_nodes, identity, graph
    )

    if not root_task:
        raise Exception()

    logger.info(
        "Queuing consent task {}. Privacy Request: {}, Request Task {}",
        root_task.collection_address,
        privacy_request.id,
        root_task.id,
    )
    run_consent_node.delay(privacy_request.id, root_task.id)

    return

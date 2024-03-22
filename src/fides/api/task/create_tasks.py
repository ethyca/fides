# pylint: disable=too-many-lines
import json
from typing import Any, Dict, List, Optional, Set

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


def _format_traversal_details_for_save(
    node: CollectionAddress, env: Dict[CollectionAddress, TraversalNode]
):
    """Format selected TraversalNode details in a way they can be saved in the database.

    This will let us execute the node when ready without having to reconstruct the traversal node later.
    """
    if node in [ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS]:
        return None

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
    env: Dict[CollectionAddress, Any],
    end_nodes: List[CollectionAddress],
    dataset_graph: DatasetGraph,
):
    """
    Create access PrivacyRequestTasks and persist to the database.

    Add PrivacyRequestTasks to the database or update existing Privacy Request tasks to a pending status

    There should only be one task for each node of each action type.

    This should only be called if a PrivacyRequest is in a pending or errored state.
    """
    graph: networkx.DiGraph = build_access_networkx_digraph(env, end_nodes, traversal)

    ready_tasks: List[RequestTask] = []

    for node in list(networkx.topological_sort(graph)):
        existing_completed_task = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == ActionType.access,
                RequestTask.collection_address == node.value,
                RequestTask.status == TaskStatus.complete,
            )
            .first()
        )

        if existing_completed_task:
            continue

        json_collection: Optional[Dict] = None
        if node not in [ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS]:
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
                "access_data": [traversal.seed_data]
                if node == ROOT_COLLECTION_ADDRESS
                else [],
                "action_type": ActionType.access,
                "collection_address": node.value,
                "all_descendant_tasks": [
                    descend.value for descend in list(networkx.descendants(graph, node))
                ],
                "collection": json_collection,
                "traversal_details": _format_traversal_details_for_save(node, env),
            },
        )
        ready_tasks.append(task)

    return ready_tasks


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
    graph: networkx.DiGraph = build_erasure_networkx_digraph(env, end_nodes)

    ready_tasks: List[RequestTask] = []

    for node in list(networkx.topological_sort(graph)):
        existing_completed_task = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == ActionType.erasure,
                RequestTask.collection_address == node.value,
                RequestTask.status == TaskStatus.complete,
            )
            .first()
        )

        if existing_completed_task:
            continue

        # Select access task of the same name
        erasure_task = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == ActionType.access,
                RequestTask.collection_address == node.value,
                RequestTask.status == TaskStatus.complete,
            )
            .first()
        )
        retrieved_task_data = []
        if erasure_task:
            retrieved_task_data = erasure_task.data_for_erasures

        # Select upstream inputs of this node for things like email connectors
        input_tasks = session.query(RequestTask).filter(
            RequestTask.privacy_request_id == privacy_request.id,
            RequestTask.action_type == ActionType.access,
            RequestTask.collection_address.in_(erasure_task.upstream_tasks),
            RequestTask.status == TaskStatus.complete,
        )
        ordered_upstream_tasks = (
            []
            if node in [ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS]
            else order_tasks_by_input_key(env[node].input_keys(), input_tasks)
        )

        combined_input_data = []
        for input_data in ordered_upstream_tasks or []:
            combined_input_data.append(input_data.data_for_erasures or [])

        json_collection: Optional[Dict] = None
        if node not in [ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS]:
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
                "data_for_erasures": retrieved_task_data or [],
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

    return ready_tasks


def persist_consent_request_tasks(
    session: Session,
    privacy_request: PrivacyRequest,
    env: Dict[CollectionAddress, TraversalNode],
    identity: Dict[str, Any],
    dataset_graph: DatasetGraph,
):
    """
    The graph built is very simple: there are no relationships between the nodes, every node has
    identity data input and every node outputs whether the consent request succeeded.

    The DatasetGraph passed in is expected to have one Node per Dataset.  That Node is expected to carry out requests
    for the Dataset as a whole.

    """
    ready_tasks: List[RequestTask] = []
    node_keys: List[CollectionAddress] = [node for node in list(env.keys())]
    for node in node_keys + [ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS]:
        existing_completed_task = (
            session.query(RequestTask)
            .filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == ActionType.consent,
                RequestTask.collection_address == node.value,
                RequestTask.status == TaskStatus.complete,
            )
            .first()
        )

        if existing_completed_task:
            continue

        json_collection: Optional[Dict] = None
        if node == ROOT_COLLECTION_ADDRESS:
            upstream_tasks = []
            downstream_tasks = [node.value for node in node_keys]
        elif node == TERMINATOR_ADDRESS:
            upstream_tasks = [node.value for node in node_keys]
            downstream_tasks = []
        else:
            upstream_tasks = [ROOT_COLLECTION_ADDRESS.value]
            downstream_tasks = [TERMINATOR_ADDRESS.value]
            if node not in [ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS]:
                json_collection = json.loads(
                    dataset_graph.nodes[node].collection.json()
                )

        task = RequestTask.create(
            session,
            data={
                "privacy_request_id": privacy_request.id,
                "upstream_tasks": upstream_tasks,
                "downstream_tasks": downstream_tasks,
                "dataset_name": node.dataset,
                "collection_name": node.collection,
                "status": TaskStatus.complete
                if node == ROOT_COLLECTION_ADDRESS
                else TaskStatus.pending,
                "consent_data": identity if node == ROOT_COLLECTION_ADDRESS else {},
                "action_type": ActionType.consent,
                "collection_address": node.value,
                "all_descendant_tasks": [TERMINATOR_ADDRESS.value],
                "collection": json_collection,
                "traversal_details": _format_traversal_details_for_save(node, env),
            },
        )
        ready_tasks.append(task)

    return ready_tasks


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

    env: Dict[CollectionAddress, TraversalNode] = {}
    # Traversal.traverse modifies "env" in place, adding parents and children to the traversal nodes
    end_nodes: List[CollectionAddress] = traversal.traverse(env, collect_tasks_fn)

    created_privacy_request_tasks: List[RequestTask] = persist_access_request_tasks(
        session, privacy_request, traversal, env, end_nodes, graph
    )
    for task in created_privacy_request_tasks:
        if task.upstream_tasks_complete(session):
            logger.info(
                f"Queuing access task {privacy_request.id} > {task.id}: {task.collection_address}"
            )
            run_access_node.delay(privacy_request.id, task.id)
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
    # Run traversal.traverse which modifies env in place to have all the nodes linked in the proper order
    traversal.traverse(env, collect_tasks_fn)
    erasure_end_nodes = list(graph.nodes.keys())

    created_privacy_request_tasks = persist_erasure_request_tasks(
        session, privacy_request, env, erasure_end_nodes, graph
    )

    queued_tasks = []
    for task in created_privacy_request_tasks:
        if (
            task.upstream_tasks_complete(session)
            and task.collection_address != ROOT_COLLECTION_ADDRESS.value
        ):
            logger.info(
                f"Queuing erasure task {privacy_request.id} > {task.id}: {task.collection_address}"
            )
            queued_tasks.append(task)
            run_erasure_node.delay(privacy_request.id, task.id)

    return queued_tasks


def run_consent_request(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    graph: DatasetGraph,
    identity: Dict[str, Any],
    session: Session,
) -> List[RequestTask]:
    """
    Build the "consent" graph, add its tasks to the database and queue the root task.

    The graph built is very simple: there are no relationships between the nodes, every node has
    identity data input and every node outputs whether the consent request succeeded.

    The DatasetGraph passed in is expected to have one Node per Dataset.  That Node is expected to carry out requests
    for the Dataset as a whole.
    """
    env = {}
    for col_address, node in graph.nodes.items():
        traversal_node = TraversalNode(node)
        env[col_address] = traversal_node

    created_consent_tasks = persist_consent_request_tasks(
        session, privacy_request, env, identity, graph
    )

    queued_tasks = []
    for task in created_consent_tasks:
        if (
            task.upstream_tasks_complete(session)
            and task.collection_address != ROOT_COLLECTION_ADDRESS.value
        ):
            logger.info(
                f"Queuing consent task {privacy_request.id} > {task.id}: {task.collection_address}"
            )
            queued_tasks.append(task)
            run_consent_node.delay(privacy_request.id, task.id)

    return queued_tasks

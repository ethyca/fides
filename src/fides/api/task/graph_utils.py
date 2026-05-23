# pylint: disable=too-many-lines
"""Engine-agnostic utilities for graph construction, task persistence, and
task hydration. Used by both the Celery and Temporal execution paths."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set

import networkx
from loguru import logger
from networkx import NetworkXNoCycle
from sqlalchemy.orm import Query, Session, defer

from fides.api.common_exceptions import ResumeTaskException, TraversalError
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
)
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.util.collection_util import Row

# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def format_data_use_map_for_caching(
    connection_key_mapping: Dict[CollectionAddress, str],
    connection_configs: list,
) -> Dict[str, Set[str]]:
    """
    Create a map of `Collection`s mapped to their associated `DataUse`s
    to be stored in the cache. This is done before request execution, so that we
    maintain the _original_ state of the graph as it's used for request execution.
    The graph is subject to change "from underneath" the request execution runtime,
    but we want to avoid picking up those changes in our data use map.

    `DataUse`s are associated with a `Collection` by means of the `System`
    that's linked to a `Collection`'s `Connection` definition.

    Example:
    {
       <collection1>: {"data_use_1", "data_use_2"},
       <collection2>: {"data_use_1"},
    }
    """
    from fides.api.models.sql_models import System  # type: ignore[attr-defined]

    resp: Dict[str, Set[str]] = {}
    connection_config_mapping = {
        connection_config.key: connection_config
        for connection_config in connection_configs
    }
    for collection_addr, connection_key in connection_key_mapping.items():
        connection_config = connection_config_mapping.get(connection_key, None)
        if not connection_config or not connection_config.system:
            resp[collection_addr.value] = set()
            continue
        data_uses: Set[str] = System.get_data_uses(
            [connection_config.system], include_parents=False
        )
        resp[collection_addr.value] = data_uses

    return resp


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

    # Validate that all erase_after references point to collections that
    # exist in the traversal or end_nodes. Dangling references (e.g. from a
    # deleted integration) would silently create phantom nodes in the graph
    # via networkx.add_edge, leading to a KeyError during task creation.
    valid_nodes = set(traversal_nodes.keys()) | set(end_nodes) | set(ARTIFICIAL_NODES)
    for node_name, traversal_node in traversal_nodes.items():
        for ref in traversal_node.node.collection.erase_after:
            if ref not in valid_nodes:
                raise TraversalError(
                    f"Erasure cannot proceed: collection '{node_name}' has an "
                    f"'Erase After' dependency on '{ref}', which no longer "
                    f"exists in the dataset graph. Update the 'Erase After' "
                    f"setting on this collection in the dataset configuration "
                    f"to remove the stale reference."
                )

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


def compute_all_descendants(
    graph: networkx.DiGraph,
) -> Dict[CollectionAddress, Set[CollectionAddress]]:
    """
    Compute descendants for ALL nodes in O(N+E) using reverse topological order.

    This is much more efficient than calling networkx.descendants() for each node,
    which would be O(N * (N+E)) = O(N²) for a graph with N nodes.

    By processing in reverse topological order (leaves first), we can compute
    each node's descendants as the union of its children's descendants plus
    its direct children.

    Returns a Dict mapping each node (CollectionAddress) in the graph to the
    set of all nodes that are reachable from it (i.e. its transitive successors).
    This is used to populate the ``all_descendant_tasks`` field on each
    RequestTask so that any node can quickly determine every downstream task
    that must complete before the overall request is finished.
    """
    all_descendants: Dict[CollectionAddress, Set[CollectionAddress]] = {
        node: set() for node in graph.nodes
    }

    # Process nodes in reverse topological order (leaves first)
    for node in reversed(list(networkx.topological_sort(graph))):
        # This node's descendants = union of (each child + child's descendants)
        for child in graph.successors(node):
            all_descendants[node].add(child)
            all_descendants[node].update(all_descendants[child])

    return all_descendants


def base_task_data(
    graph: networkx.DiGraph,
    dataset_graph: DatasetGraph,
    privacy_request: Any,
    node: CollectionAddress,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    all_descendants: Dict[CollectionAddress, Set[CollectionAddress]],
) -> Dict:
    """Build a dictionary of common RequestTask attributes that are shared for building
    access, consent, and erasure tasks"""
    from fides.api.models.privacy_request import TraversalDetails
    from fides.api.models.worker_task import ExecutionLogStatus

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
            [descend.value for descend in all_descendants.get(node, set())]
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


# ---------------------------------------------------------------------------
# Task persistence
# ---------------------------------------------------------------------------


def persist_new_access_request_tasks(
    session: Session,
    privacy_request: Any,
    traversal: Traversal,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    dataset_graph: DatasetGraph,
) -> list:
    """
    Create individual access RequestTasks from the TraversalNodes and persist to the database.
    This should only run the first time a privacy request runs.
    """
    from fides.api.models.privacy_request import RequestTask
    from fides.api.schemas.policy import ActionType

    logger.info(
        "Creating access request tasks for privacy request {}.", privacy_request.id
    )
    graph: networkx.DiGraph = build_access_networkx_digraph(
        traversal_nodes, end_nodes, traversal
    )

    # Pre-compute all descendants in O(N+E) instead of O(N²)
    all_descendants = compute_all_descendants(graph)

    for node in list(networkx.topological_sort(graph)):
        if privacy_request.get_existing_request_task(
            session, action_type=ActionType.access, collection_address=node
        ):
            continue

        RequestTask.create(
            session,
            data={
                **base_task_data(
                    graph,
                    dataset_graph,
                    privacy_request,
                    node,
                    traversal_nodes,
                    all_descendants,
                ),
                "access_data": (
                    [traversal.seed_data] if node == ROOT_COLLECTION_ADDRESS else []
                ),  # For consistent treatment of nodes, add the seed data to the root node.  Subsequent
                # tasks will save the data collected on the same field.
                "action_type": ActionType.access,
            },
        )

    root_task = privacy_request.get_root_task_by_action(ActionType.access)

    return [root_task]


def persist_initial_erasure_request_tasks(
    session: Session,
    privacy_request: Any,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    end_nodes: List[CollectionAddress],
    dataset_graph: DatasetGraph,
) -> list:
    """
    Create starter individual erasure RequestTasks from the TraversalNodes and persist to the database.

    These are not ready to run yet as they are still waiting for access data from the access graph
    to be able to build masking requests
    """
    from fides.api.models.privacy_request import RequestTask
    from fides.api.schemas.policy import ActionType

    logger.info(
        "Creating initial erasure request tasks for privacy request {}.",
        privacy_request.id,
    )
    graph: networkx.DiGraph = build_erasure_networkx_digraph(traversal_nodes, end_nodes)

    # Pre-compute all descendants in O(N+E) instead of O(N²)
    all_descendants = compute_all_descendants(graph)

    for node in list(networkx.topological_sort(graph)):
        if privacy_request.get_existing_request_task(
            session, action_type=ActionType.erasure, collection_address=node
        ):
            continue

        RequestTask.create(
            session,
            data={
                **base_task_data(
                    graph,
                    dataset_graph,
                    privacy_request,
                    node,
                    traversal_nodes,
                    all_descendants,
                ),
                "action_type": ActionType.erasure,
            },
        )

    # If a policy has an erasure rule, this method is run immediately after creating the access tasks, so their
    # nodes in the database are the same.  There are no "ready" tasks yet, because we need to wait for the
    # access step to run, so we return an empty list here.
    return []


def _get_data_for_erasures(
    session: Session, privacy_request: Any, request_task: Any
) -> List[Dict]:
    """
    Return the access data in erasure format needed to format the masking request for the current node.
    """
    # Get the access task of the same name as the erasure task so we can transfer the data
    # collected for masking onto the current erasure task
    from fides.api.schemas.policy import ActionType

    corresponding_access_task = privacy_request.get_existing_request_task(
        db=session,
        action_type=ActionType.access,
        collection_address=request_task.request_task_address,
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
    privacy_request: Any,
) -> None:
    """
    Update individual erasure RequestTasks with data from the TraversalNodes and persist to the database.
    """
    from fides.api.models.privacy_request import RequestTask

    logger.info(
        "Updating erasure request tasks with data needed for masking requests {}.",
        privacy_request.id,
    )

    # Defer large columns except _data_for_erasures which we're setting
    erasure_tasks_query = RequestTask.query_with_deferred_data(
        privacy_request.erasure_tasks, defer_erasure_data=False
    )
    for request_task in erasure_tasks_query:
        # I pull access data saved in the format suitable for erasures
        # off of the access nodes to be saved onto the erasure nodes.
        retrieved_task_data = _get_data_for_erasures(
            session, privacy_request, request_task
        )
        request_task.data_for_erasures = retrieved_task_data
        request_task.save(session)


def persist_new_consent_request_tasks(
    session: Session,
    privacy_request: Any,
    traversal_nodes: Dict[CollectionAddress, TraversalNode],
    identity: Dict[str, Any],
    dataset_graph: DatasetGraph,
) -> list:
    """
    Create individual consent RequestTasks from the TraversalNodes and persist to the database.  This should only
    run the first time a privacy request runs.

    Consent propagation graphs are much simpler with no relationships between nodes. Every node has identity data input,
    and every node outputs whether the consent request succeeded.
    """
    from fides.api.models.privacy_request import RequestTask
    from fides.api.schemas.policy import ActionType

    graph: networkx.DiGraph = build_consent_networkx_digraph(traversal_nodes)

    # Pre-compute all descendants in O(N+E) instead of O(N²)
    all_descendants = compute_all_descendants(graph)

    for node in list(networkx.topological_sort(graph)):
        if privacy_request.get_existing_request_task(
            session, action_type=ActionType.consent, collection_address=node
        ):
            continue
        RequestTask.create(
            session,
            data={
                **base_task_data(
                    graph,
                    dataset_graph,
                    privacy_request,
                    node,
                    traversal_nodes,
                    all_descendants,
                ),
                # Consent nodes take in identity data from their upstream root node
                "access_data": ([identity] if node == ROOT_COLLECTION_ADDRESS else []),
                "action_type": ActionType.consent,
            },
        )

    root_task = privacy_request.get_root_task_by_action(ActionType.consent)

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


# ---------------------------------------------------------------------------
# Task hydration (used by both Celery and Temporal execution)
# ---------------------------------------------------------------------------


def create_graph_task(session: Session, request_task: Any, resources: Any) -> Any:
    """Hydrates a GraphTask from the saved collection details on the Request Task in the database

    This could fail if things like our Collection definitions have changed since we created the Task
    to begin with - this may be unrecoverable and a new Privacy Request should be created.
    """
    from fides.api.models.privacy_request import ExecutionLog
    from fides.api.models.worker_task import ExecutionLogStatus
    from fides.api.task.graph_task import (
        GraphTask,
        mark_current_and_downstream_nodes_as_failed,
    )
    from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask

    try:
        collection_address = request_task.request_task_address

        graph_task: GraphTask
        if ManualTaskAddress.is_manual_task_address(collection_address):
            graph_task = ManualTaskGraphTask(resources)
        else:
            graph_task = GraphTask(resources)

    except Exception as exc:
        logger.debug(
            "Cannot execute task - error loading task from database. Exception {}",
            str(exc),
        )
        ExecutionLog.create(
            db=session,
            data={
                "connection_key": None,
                "dataset_name": request_task.dataset_name,
                "collection_name": request_task.collection_name,
                "fields_affected": [],
                "action_type": request_task.action_type,
                "status": ExecutionLogStatus.error,
                "privacy_request_id": request_task.privacy_request_id,
                "message": str(exc),
            },
        )
        mark_current_and_downstream_nodes_as_failed(request_task, session)

        raise ResumeTaskException(
            f"Cannot resume request task. Error hydrating task from database: Request Task {request_task.id} for Privacy Request {request_task.privacy_request_id}. {exc}"
        )

    return graph_task


def _order_tasks_by_input_key(
    input_keys: List[CollectionAddress], upstream_tasks: Query
) -> list:
    """Order tasks by input key. If task doesn't exist, add None in its place

    Data being passed to GraphTask.access_request is expected to have the same order
    as input keys so we know which data belongs to which upstream collection
    """
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


def build_upstream_access_data(
    input_keys: List[CollectionAddress],
    upstream_tasks: Query,
) -> List[List[Row]]:
    """
    Helper function to build the access data for the current node.
    The access data is passed in the same order as the input keys.
    If we don't have access data for an upstream node, return an empty list.
    """

    ordered_upstream: List[Optional[RequestTask]] = _order_tasks_by_input_key(
        input_keys, upstream_tasks
    )
    return [task.get_access_data() if task else [] for task in ordered_upstream]

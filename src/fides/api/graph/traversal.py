# pylint: disable=too-many-instance-attributes, too-many-branches, too-many-statements
from __future__ import annotations

import json
from collections import defaultdict, deque
from itertools import chain
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

import pydash.collections
from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    TraversalError,
    UnreachableEdgesError,
    UnreachableNodesError,
)
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    Collection,
    CollectionAddress,
    FieldAddress,
    FieldPath,
    GraphDataset,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph, Edge, Node
from fides.api.graph.node_filters import (
    CustomRequestFieldFilter,
    NodeFilter,
    OptionalIdentityFilter,
    PolicyDataCategoryFilter,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    PrivacyRequest,
    RequestTask,
    TraversalDetails,
)
from fides.api.schemas.policy import ActionType
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.util.collection_util import Row, append, partition
from fides.api.util.logger_context_utils import Contextualizable, LoggerContextKeys
from fides.api.util.matching_queue import MatchingQueue

ARTIFICIAL_NODES: List[CollectionAddress] = [
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
]

Datastore = Dict[CollectionAddress, List[Row]]
"""A type expressing retrieved rows of data from a specified collection"""


def artificial_traversal_node(address: CollectionAddress) -> TraversalNode:
    """generate an 'artificial' traversal_node pointing to the given address. This is used to
    generate artificial root and termination nodes that correspond to just an address, but
    have no actual corresponding collection dataset"""
    ds: Collection = Collection(name=address.collection, fields=[])
    node = Node(
        GraphDataset(
            name=address.dataset, collections=[ds], connection_key="__IGNORE__"
        ),
        ds,
    )
    return TraversalNode(node)


class BaseTraversal:
    """Handling for a single reified traversal of a graph based on input (seed) data."""

    def extract_seed_field_addresses(
        self,
    ) -> Dict[FieldAddress, str]:
        """Find seeded values in the graph based on the input seed and return
        a list of the populated seed nodes"""

        return {
            identity_address: seed_key
            for identity_address, seed_key in self.graph.identity_keys.items()
            if seed_key in self.seed_data
        }

    def __init__(
        self,
        graph: DatasetGraph,
        data: Dict[str, Any],
        *,
        policy: Optional[Policy] = None,
        node_filters: Optional[List[NodeFilter]] = None,
        skip_verification: bool = False,
    ):
        self.graph = graph
        self.seed_data = data
        self.policy = policy
        self._skip_verification = skip_verification

        # Node filters are used to allow unreachable nodes to be ignored
        # if they don't apply to the given scenario
        self.node_filters = node_filters or []

        self.traversal_node_dict = {k: TraversalNode(v) for k, v in graph.nodes.items()}
        self.edges: Set[Edge] = graph.edges.copy()
        self.root_node = artificial_traversal_node(ROOT_COLLECTION_ADDRESS)

        # Pre-index edges by node address for O(1) lookup
        self.edges_by_node: Dict[CollectionAddress, List[Edge]] = defaultdict(list)
        for edge in self.edges:
            self.edges_by_node[edge.f1.collection_address()].append(edge)
            self.edges_by_node[edge.f2.collection_address()].append(edge)

        # Pre-build dataset -> collections index for O(1) lookup (Fix for O(N²))
        self._collections_by_dataset: Dict[str, Set[str]] = defaultdict(set)
        for addr in self.traversal_node_dict.keys():
            self._collections_by_dataset[addr.dataset].add(addr.value)

        # Pre-compute string versions of node dependencies
        # This avoids expensive hash operations during traversal
        self.node_after_str: Dict[str, Set[str]] = {}
        self.dataset_after_str: Dict[str, Set[str]] = {}

        for addr, traversal_node in self.traversal_node_dict.items():
            # Collection-level after dependencies
            self.node_after_str[addr.value] = {
                dep.value for dep in traversal_node.node.collection.after
            }
            # Dataset-level after dependencies - use pre-built index for O(1) lookup
            dataset_deps: Set[str] = set()
            for dataset_name in traversal_node.node.dataset.after:
                # O(1) lookup instead of O(N) scan
                dataset_deps.update(self._collections_by_dataset.get(dataset_name, set()))
            self.dataset_after_str[addr.value] = dataset_deps

        # Add root node to the pre-computed dependencies (it has no dependencies)
        self.node_after_str[ROOT_COLLECTION_ADDRESS.value] = set()
        self.dataset_after_str[ROOT_COLLECTION_ADDRESS.value] = set()

        for (
            start_field_address,
            seed_key,
        ) in self.extract_seed_field_addresses().items():
            edge = Edge(
                FieldAddress(
                    ROOT_COLLECTION_ADDRESS.dataset,
                    ROOT_COLLECTION_ADDRESS.collection,
                    seed_key,
                ),
                start_field_address,
            )
            self.edges.add(edge)
            # Add to edge index
            self.edges_by_node[ROOT_COLLECTION_ADDRESS].append(edge)
            self.edges_by_node[start_field_address.collection_address()].append(edge)

        # Ensure manual_task collections execute right after ROOT

        for addr in self.traversal_node_dict.keys():
            if ManualTaskAddress.is_manual_task_address(addr):
                # Add a simple synthetic edge ROOT.id -> manual_data.id
                edge = Edge(
                    FieldAddress(
                        ROOT_COLLECTION_ADDRESS.dataset,
                        ROOT_COLLECTION_ADDRESS.collection,
                        "id",
                    ),
                    addr.field_address(FieldPath("id")),
                )
                self.edges.add(edge)
                # Add to edge index
                self.edges_by_node[ROOT_COLLECTION_ADDRESS].append(edge)
                self.edges_by_node[addr].append(edge)

        if not self._skip_verification:
            self._verify_traversal()

    def _verify_traversal(self) -> None:
        """Verify that a valid traversal exists. This method simply assembles a traversal
        and raises an error on any traversal failure conditions."""
        self.traverse(
            {self.root_node.address: [self.seed_data]},
            lambda n, m: logger.info("Traverse {}", n.address),
        )

    def traversal_map(
        self,
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], List[CollectionAddress]]:
        """Generate a descriptive map of the traversal generated.

        For each traversal_node N, list
         { N.address:
             {"from": {traversal_node address:
                       [field in "from", field in N for all edges from "from" to N]}}
             {"to": {traversal_node address,
                       [field in N, field in "to"" for all edges from N to "to"]}}

        """

        def traversal_dict_fn(
            tn: TraversalNode, data: Dict[CollectionAddress, Dict[str, Any]]
        ) -> None:
            data[tn.address] = tn.debug()

        db = {ROOT_COLLECTION_ADDRESS: [self.seed_data]}
        traversal_ends = self.traverse(db, traversal_dict_fn)

        return {str(k): v for k, v in db.items()}, traversal_ends

    def should_exclude_node(self, node: TraversalNode) -> bool:
        """Returns True if any filter indicates the node should be excluded"""
        return any(filter.exclude_node(node) for filter in self.node_filters)

    def traverse(  # pylint: disable=R0914
        self,
        environment: Dict[CollectionAddress, Any],
        node_run_fn: Callable[[TraversalNode, Dict[CollectionAddress, Any]], None],
    ) -> List[CollectionAddress]:
        """Traverse and call run() on each traversal_node in turn.

        Uses In-Degree Tracking (Kahn's Algorithm variant) for O(N+E) complexity.
        Instead of O(N) scanning for eligible nodes, we track dependency counts
        and maintain a ready queue.

        The algorithm:
        1. Compute initial "blocked by" counts for each node based on:
           - 'after' dependencies (collection-level and dataset-level)
           - Edge-based dependencies (nodes reachable from ROOT)
        2. Nodes with blocked_by == 0 go into the ready queue
        3. When a node completes, decrement blocked_by for its dependents
        4. Nodes that reach blocked_by == 0 are added to ready queue

        Returns a list of termination traversal_node addresses so that we can
        take action on completed traversal.
        """
        if environment:
            logger.info("Starting traversal")

        # Track which nodes are finished
        finished_nodes: Dict[CollectionAddress, TraversalNode] = {}
        finished_str: Set[str] = set()

        # Track deleted edges (same as original algorithm)
        deleted_edges_tracker: Dict[Edge, bool] = {}

        # Compute "blocked by" count for each node based on 'after' dependencies
        # blocked_by[addr] = number of unfinished nodes that must run before addr
        blocked_by: Dict[str, int] = {}

        for addr_str in self.node_after_str.keys():
            if addr_str == ROOT_COLLECTION_ADDRESS.value:
                blocked_by[addr_str] = 0
                continue

            # Count unfinished 'after' dependencies
            after_deps = self.node_after_str.get(addr_str, set())
            dataset_deps = self.dataset_after_str.get(addr_str, set())
            all_deps = after_deps | dataset_deps

            # Only count dependencies that are actually in our graph
            valid_deps = all_deps & set(self.node_after_str.keys())
            blocked_by[addr_str] = len(valid_deps)

        # Build reverse dependency map: when node X finishes, which nodes become unblocked?
        # unblocks[X] = set of nodes that are waiting for X
        unblocks: Dict[str, Set[str]] = defaultdict(set)

        for addr_str in self.node_after_str.keys():
            if addr_str == ROOT_COLLECTION_ADDRESS.value:
                continue

            after_deps = self.node_after_str.get(addr_str, set())
            dataset_deps = self.dataset_after_str.get(addr_str, set())
            all_deps = after_deps | dataset_deps

            for dep in all_deps:
                if dep in self.node_after_str:  # Valid dependency
                    unblocks[dep].add(addr_str)

        # Ready queue: nodes with no blocking 'after' dependencies
        # We still need to check edge-based reachability dynamically
        ready_queue: deque[TraversalNode] = deque()

        # Start with ROOT (always ready)
        ready_queue.append(self.root_node)

        # Track nodes that have been discovered via edges (reachable from ROOT)
        discovered: Set[str] = {ROOT_COLLECTION_ADDRESS.value}

        # Pending queue: nodes discovered but blocked by 'after' dependencies
        pending: Dict[str, TraversalNode] = {}

        while ready_queue or pending:
            # Try to get a node from the ready queue
            current_node: Optional[TraversalNode] = None

            if ready_queue:
                current_node = ready_queue.popleft()
            else:
                # No ready nodes - check if any pending nodes are now ready
                # This handles the edge case where a node was discovered but blocked
                newly_ready = [
                    addr for addr, node in pending.items()
                    if blocked_by.get(addr, 0) == 0
                ]
                if newly_ready:
                    addr = newly_ready[0]
                    current_node = pending.pop(addr)
                else:
                    # Deadlock: pending nodes but none are ready
                    logger.error(
                        "Node could not be reached given specified ordering [{}]",
                        ", ".join(pending.keys()),
                    )
                    raise TraversalError(
                        f"Node could not be reached given the specified ordering: [{', '.join(pending.keys())}]"
                    )

            if current_node is None:
                break

            # Process the node
            node_run_fn(current_node, environment)
            finished_nodes[current_node.address] = current_node
            finished_str.add(current_node.address.value)

            # Update blocked_by counts for nodes waiting on this one
            for waiting_addr in unblocks.get(current_node.address.value, set()):
                if waiting_addr in blocked_by:
                    blocked_by[waiting_addr] -= 1
                    # If this node is pending and now has 0 blockers, move to ready
                    if waiting_addr in pending and blocked_by[waiting_addr] == 0:
                        ready_queue.append(pending.pop(waiting_addr))

            # Handle edge-based parent/child relationships - O(edges) not O(finished_nodes)
            # Only check edges incident to current node, not all finished nodes
            for edge in self.edges_by_node.get(current_node.address, []):
                if deleted_edges_tracker.get(edge, False):
                    continue

                # Find the other endpoint of this edge
                other_addr = (
                    edge.f2.collection_address()
                    if edge.f1.collection_address() == current_node.address
                    else edge.f1.collection_address()
                )

                # Only process if the other endpoint is already finished
                if other_addr in finished_nodes:
                    # IMPORTANT: Use edge.spans() to match original algorithm's deletion logic
                    # spans() is order-sensitive for regular Edge (not BidirectionalEdge)
                    # This allows cycles to work correctly by not deleting "backward" edges
                    if edge.spans(other_addr, current_node.address):
                        deleted_edges_tracker[edge] = True

                        # Determine parent/child relationship based on edge direction
                        if edge.ends_with_collection(current_node.address):
                            # Edge points TO current node: other is parent, current is child
                            finished_nodes[other_addr].add_child(current_node, edge)

            # Discover children via remaining edges
            edges_to_children = pydash.collections.filter_(
                [
                    e.split_by_address(current_node.address)
                    for e in self.edges_by_node.get(current_node.address, [])
                    if not deleted_edges_tracker.get(e, False)
                ]
            )

            if not edges_to_children:
                current_node.is_terminal_node = True

            # Add newly discovered children to ready or pending queue
            child_addresses = {
                a[1].collection_address() for a in edges_to_children if a
            }

            for child_addr in child_addresses:
                # Skip if already in discovered set AND not finished
                # (allow re-adding finished nodes for cycle handling)
                if child_addr.value in discovered and child_addr.value not in finished_str:
                    continue
                if child_addr not in self.traversal_node_dict:
                    continue

                # For finished nodes being re-discovered (cycles), add directly to ready queue
                if child_addr.value in finished_str:
                    # Re-process this node to handle the cycle
                    ready_queue.append(self.traversal_node_dict[child_addr])
                    continue

                discovered.add(child_addr.value)
                child_node = self.traversal_node_dict[child_addr]

                # Check if this node is ready (no unfinished 'after' deps)
                if blocked_by.get(child_addr.value, 0) == 0:
                    ready_queue.append(child_node)
                else:
                    pending[child_addr.value] = child_node

        # Check for unvisited nodes (same as original)
        remaining_node_keys = {
            key
            for key in self.traversal_node_dict.keys()
            if key not in finished_nodes
            and not self.should_exclude_node(self.traversal_node_dict[key])
        }

        if remaining_node_keys:
            logger.error(
                "Some nodes were not reachable: {}",
                ", ".join([str(x) for x in remaining_node_keys]),
            )
            raise UnreachableNodesError(
                f"Some nodes were not reachable: {', '.join([str(x) for x in remaining_node_keys])}",
                [key.value for key in remaining_node_keys],
            )

        # Check for unvisited edges
        remaining_edges = set()
        for node_key in remaining_node_keys:
            for edge in self.edges_by_node.get(node_key, []):
                if not deleted_edges_tracker.get(edge, False):
                    if (
                        edge.f1.collection_address() in remaining_node_keys
                        and edge.f2.collection_address() in remaining_node_keys
                    ):
                        remaining_edges.add(edge)

        if remaining_edges:
            logger.error(
                "Some edges were not reachable: {}",
                ", ".join([str(x) for x in remaining_edges]),
            )
            raise UnreachableEdgesError(
                f"Some edges were not reachable: {', '.join([str(x) for x in remaining_edges])}",
                [f"{edge}" for edge in remaining_edges],
            )

        end_nodes = [
            tn.address for tn in finished_nodes.values() if tn.is_terminal_node
        ]
        if environment:
            logger.debug("Found {} end nodes: {}", len(end_nodes), end_nodes)
        return end_nodes

    def _traverse_legacy(  # pylint: disable=R0914
        self,
        environment: Dict[CollectionAddress, Any],
        node_run_fn: Callable[[TraversalNode, Dict[CollectionAddress, Any]], None],
    ) -> List[CollectionAddress]:
        """Legacy O(N²) traverse implementation using MatchingQueue.

        Kept for reference. The new traverse() method uses In-Degree Tracking
        (Kahn's Algorithm variant) for O(N+E) complexity.

        This implementation scans the queue for eligible nodes on each iteration,
        which is O(N) per node = O(N²) total.
        """
        if environment:
            logger.info(
                "Starting traversal (legacy)",
            )

        # Use string sets instead of CollectionAddress sets
        # This avoids expensive hash operations
        remaining_node_keys_str: Set[str] = {
            addr.value for addr in self.traversal_node_dict.keys()
        }
        finished_nodes: dict[CollectionAddress, TraversalNode] = {}
        running_node_queue: MatchingQueue[TraversalNode] = MatchingQueue(self.root_node)

        # Instead of copying entire edge set, use a more efficient approach
        # We'll simulate Edge.delete_edges behavior without the expensive set operations
        deleted_edges_tracker: Dict[Edge, bool] = {}

        while not running_node_queue.is_empty():
            # this is to support the "run traversal_node A AFTER traversal_node B functionality:"
            n = running_node_queue.pop_first_match(
                lambda x: x.can_run_given_str(
                    remaining_node_keys_str, self.node_after_str, self.dataset_after_str
                )
            )

            if n:
                node_run_fn(n, environment)
                # delete all edges between the traversal_node that's just run and any completed nodes
                for finished_node_address, finished_node in finished_nodes.items():
                    # Find edges to delete manually instead of using Edge.delete_edges
                    completed_edges: Set[Edge] = set()

                    # Only check edges connected to the relevant nodes
                    relevant_edges = set()
                    relevant_edges.update(
                        self.edges_by_node.get(finished_node_address, [])
                    )
                    relevant_edges.update(self.edges_by_node.get(n.address, []))

                    for edge in relevant_edges:
                        # Skip if already deleted
                        if deleted_edges_tracker.get(edge, False):
                            continue

                        # Check if this edge spans between the two nodes (bidirectional check)
                        if edge.spans(
                            finished_node_address,
                            cast(TraversalNode, n).address,  # type: ignore[redundant-cast]
                        ):
                            completed_edges.add(edge)
                            deleted_edges_tracker[edge] = True

                    def edge_ends_with_collection(_edge: Edge) -> bool:
                        # append edges that end in this traversal_node
                        return _edge.ends_with_collection(
                            cast(TraversalNode, n).address  # type: ignore[redundant-cast]
                        )

                    for edge in filter(edge_ends_with_collection, completed_edges):
                        # note, this will not work for self-reference
                        finished_node.add_child(n, edge)

                # next edges = take all edges including n that are _not_ in edges_from_completed_nodes
                # in the form (field_address_this, field_address_foreign)

                # Use pre-indexed edges instead of iterating through all edges
                edges_to_children = pydash.collections.filter_(
                    [
                        e.split_by_address(cast(TraversalNode, n).address)  # type: ignore[redundant-cast]
                        for e in self.edges_by_node[n.address]
                        if not deleted_edges_tracker.get(e, False)
                    ]
                )
                if not edges_to_children:
                    n.is_terminal_node = True

                # child traversal_node addresses are the address portion of the above
                child_node_addresses = {
                    a[1].collection_address() for a in edges_to_children if a
                }
                for nxt_address in child_node_addresses:
                    # only add the next traversal_node to the queue if it is not already there (no duplicates)
                    running_node_queue.push_if_new(
                        self.traversal_node_dict[nxt_address]
                    )
                finished_nodes[n.address] = n
                remaining_node_keys_str.discard(n.address.value)  # Use string value
            else:
                # traversal traversal_node dict diff finished nodes
                logger.error(
                    "Node could not be reached given specified ordering [{}]",
                    ", ".join([str(tn.address) for tn in running_node_queue.data]),
                )
                raise TraversalError(
                    f"""Node could not be reached given the specified ordering:
                    [{", ".join([str(tn.address) for tn in running_node_queue.data])}]""",
                )

        # Convert back to CollectionAddress set for filtering
        remaining_node_keys = {
            key
            for key in self.traversal_node_dict.keys()
            if key.value in remaining_node_keys_str
            and not self.should_exclude_node(self.traversal_node_dict[key])
        }

        # Update string set after filtering
        remaining_node_keys_str = {key.value for key in remaining_node_keys}

        # error if there are nodes that have not been visited
        if remaining_node_keys:
            logger.error(
                "Some nodes were not reachable: {}",
                ", ".join([str(x) for x in remaining_node_keys]),
            )
            raise UnreachableNodesError(
                f"Some nodes were not reachable: {', '.join([str(x) for x in remaining_node_keys])}",
                [key.value for key in remaining_node_keys],
            )

        # filter out remaining_edges if the nodes they link are allowed to remain unreachable
        remaining_edges = set()
        for node_key in remaining_node_keys:
            for edge in self.edges_by_node.get(node_key, []):
                if not deleted_edges_tracker.get(edge, False):
                    # Check if both ends of the edge are in remaining nodes
                    if (
                        edge.f1.collection_address() in remaining_node_keys
                        and edge.f2.collection_address() in remaining_node_keys
                    ):
                        remaining_edges.add(edge)

        # error if there are edges that have not been visited
        if remaining_edges:
            logger.error(
                "Some edges were not reachable: {}",
                ", ".join([str(x) for x in remaining_edges]),
            )
            raise UnreachableEdgesError(
                f"Some edges were not reachable: {', '.join([str(x) for x in remaining_edges])}",
                [f"{edge}" for edge in remaining_edges],
            )

        end_nodes = [
            tn.address for tn in finished_nodes.values() if tn.is_terminal_node
        ]
        if environment:
            logger.debug("Found {} end nodes: {}", len(end_nodes), end_nodes)
        return end_nodes

    @property
    def skipped_nodes(self) -> Dict[str, str]:
        """
        Returns a dictionary of node addresses to skip reasons from all node filters.
        """
        result = {}
        for node_filter in self.node_filters:
            result.update(node_filter.skipped_nodes)
        return result


class Traversal(BaseTraversal):
    """Handling for a single reified traversal of a graph based on input (seed) data."""

    def __init__(
        self,
        graph: DatasetGraph,
        data: Dict[str, Any],
        *,
        policy: Optional[Policy] = None,
        node_filters: Optional[List[NodeFilter]] = None,
    ):
        filters = node_filters or []

        filters.append(CustomRequestFieldFilter())
        filters.append(OptionalIdentityFilter(graph, data))
        if policy:
            filters.append(PolicyDataCategoryFilter(policy))

        super().__init__(graph, data, policy=policy, node_filters=filters)


def log_traversal_error_and_update_privacy_request(
    privacy_request: PrivacyRequest, session: Session, err: TraversalError
) -> None:
    """
    Logs the provided traversal error with the privacy request id, creates the corresponding
    ExecutionLog instances, and marks the privacy request as errored.

    If the error is a generic TraversalError, a generic error execution log is created.
    If the error is an UnreachableNodesError or UnreachableEdgesError, an execution log is created
    for each node / edge on the "errors" list of the exception.
    """
    logger.error(
        "TraversalError encountered for privacy request. Error: {}",
        err,
    )

    # For generic TraversalErrors, we log a generic error execution log
    if not isinstance(err, UnreachableNodesError) and not isinstance(
        err, UnreachableEdgesError
    ):
        privacy_request.add_error_execution_log(
            session,
            connection_key=None,
            dataset_name="Dataset traversal",
            collection_name=None,
            message=str(err),
            action_type=ActionType.access,
        )

    # For specific ones, we iterate over each unreachable node key in the list
    for error in err.errors:
        dataset, collection = (
            error.split(":")
            if isinstance(
                err, UnreachableNodesError
            )  # For unreachable nodes, we can get the dataset and collection from the node
            else (None, None)  # But not for edges
        )
        message = f"{'Node' if isinstance(err, UnreachableNodesError) else 'Edge'} {error} is not reachable"
        privacy_request.add_error_execution_log(
            session,
            connection_key=None,
            dataset_name="Dataset traversal",
            collection_name=f"{dataset}.{collection}",
            message=message,
            action_type=ActionType.access,
        )
    privacy_request.error_processing(session)


class TraversalNode(Contextualizable):
    """Traversal_node type. This type is used for building the graph, not for executing the graph."""

    def __init__(self, node: Node):
        self.node = node
        self.address = node.address
        # address to a child that holds both a traversal_node and all possible paths
        # from this traversal_node to it: {address -> [(traversal_node, from_field, to_field)}
        self.children: Dict[
            CollectionAddress, List[Tuple[TraversalNode, FieldPath, FieldPath]]
        ] = {}
        self.parents: Dict[
            CollectionAddress, List[Tuple[TraversalNode, FieldPath, FieldPath]]
        ] = {}
        self.is_terminal_node = False

    def add_child(self, child_node: TraversalNode, edge: Edge) -> None:
        """Add other as a child to this traversal_node along the provided edge."""
        addresses = edge.split_by_address(self.address)  # (traversal_node -> other)
        if addresses:
            self_field_address, other_field_address = addresses
            append(
                self.children,
                other_field_address.collection_address(),
                (
                    child_node,
                    self_field_address.field_path,
                    other_field_address.field_path,
                ),
            )
            append(
                child_node.parents,
                self_field_address.collection_address(),
                (self, self_field_address.field_path, other_field_address.field_path),
            )

    def incoming_edges(self) -> Set[Edge]:
        """Return the incoming edges to this traversal_node,in (other.address -> self.address) order."""
        return {
            Edge(
                p_collection_address.field_address(parent_field_path),
                self.address.field_address(self_field_path),
            )
            for p_collection_address, tuples in self.parents.items()
            for _, parent_field_path, self_field_path in tuples
        }

    def outgoing_edges(self) -> Set[Edge]:
        """Return the outgoing edges to this traversal_node,in (self.address -> other.address) order."""
        return {
            Edge(
                self.address.field_address(self_field_path),
                c_collection_address.field_address(child_field_path),
            )
            for c_collection_address, tuples in self.children.items()
            for _, self_field_path, child_field_path in tuples
        }

    def incoming_edges_by_collection(self) -> Dict[CollectionAddress, List[Edge]]:
        return partition(self.incoming_edges(), lambda e: e.f1.collection_address())

    def input_keys(self) -> List[CollectionAddress]:
        """Returns the inputs to the current node that are data dependencies
        This is copied and saved to the RequestTask and used to maintain a consistent order
        for passing in data for an access task
        """
        return sorted(self.incoming_edges_by_collection().keys())

    def can_run_given(self, remaining_node_keys: Set[CollectionAddress]) -> bool:
        """True if finished_node_keys covers all the nodes that this traversal_node is waiting for.  If
        all nodes this traversal_node is waiting for have finished, it's ok for this traversal_node to run.

        NOTE: "After" functionality may not work as expected.
        """
        if self.node.collection.after.intersection(
            remaining_node_keys
        ) or self.node.dataset.after.intersection(
            {k.dataset for k in remaining_node_keys}
        ):
            return False
        return True

    def can_run_given_str(
        self,
        remaining_node_keys_str: Set[str],
        node_after_str: Dict[str, Set[str]],
        dataset_after_str: Dict[str, Set[str]],
    ) -> bool:
        """Optimized version using pre-computed string sets to avoid expensive hash operations."""
        # Check collection-level dependencies
        node_deps = node_after_str.get(self.address.value, set())
        if node_deps & remaining_node_keys_str:
            return False
        # Check dataset-level dependencies
        dataset_deps = dataset_after_str.get(self.address.value, set())
        if dataset_deps & remaining_node_keys_str:
            return False
        return True

    def is_root_node(self) -> bool:
        """This traversal_node is the defined traversal start"""
        return self.address == ROOT_COLLECTION_ADDRESS

    def debug(self) -> Dict[str, Any]:
        """Generate debug descriptive output of the traversal."""
        _from: Dict[str, Set[str]] = {}

        for edge in self.incoming_edges():
            foreign = edge.f1
            local = edge.f2
            # if we have a bidirectional edge, make sure that we correctly label
            # which edge is foreign.
            if foreign.collection_address() == self.address:
                foreign, local = local, foreign
            key = str(foreign.collection_address())
            val = f"{foreign.field_path.string_path} -> {local.field_path.string_path}"
            if key in _from:
                _from[key].add(val)
            else:
                _from[key] = {val}
        to: Dict[str, Set[str]] = {}
        for k, v in self.children.items():
            to[str(k)] = {f"{f[1].string_path} -> {f[2].string_path}" for f in v}
        return {
            "from": {k: set(v) for k, v in _from.items()},
            "to": {k: set(v) for k, v in to.items()},
        }

    def get_log_context(self) -> Dict[LoggerContextKeys, Any]:
        return {LoggerContextKeys.collection: self.node.collection.name}

    def format_traversal_details_for_save(self) -> Dict:
        """Convert key traversal details from the TraversalNode for save on the RequestTask.

        The RequestTask will be retrieved from the database and the traversal details
        used to build the ExecutionNode for DSR 3.0.
        """

        connection_key: FidesKey = self.node.dataset.connection_key

        return TraversalDetails(
            dataset_connection_key=connection_key,
            incoming_edges=[
                [edge.f1.value, edge.f2.value] for edge in self.incoming_edges()
            ],
            outgoing_edges=[
                [edge.f1.value, edge.f2.value] for edge in self.outgoing_edges()
            ],
            input_keys=[tn.value for tn in self.input_keys()],
        ).model_dump(mode="json")

    def to_mock_request_task(self) -> RequestTask:
        """Converts a portion of the TraversalNode into a RequestTask - used in building
        dry run queries or for supporting Deprecated DSR 2.0. Request Tasks were introduced in DSR 3.0
        """
        collection_data = json.loads(
            # Serializes with duck-typing behavior, no longer the default in Pydantic v2
            # Needed for serializing nested collection fields
            self.node.collection.model_dump_json(serialize_as_any=True)
        )
        return RequestTask(  # Mock a RequestTask object in memory
            collection_address=self.node.address.value,
            dataset_name=self.node.address.dataset,
            collection_name=self.node.address.collection,
            collection=collection_data,
            traversal_details=self.format_traversal_details_for_save(),
        )

    def to_mock_execution_node(self) -> ExecutionNode:
        """Converts a TraversalNode into an ExecutionNode - used for supporting DSR 2.0, to convert
        Traversal Nodes into the Execution Node format which is needed for executing the graph in
        DSR 3.0

        DSR 3.0 on the other hand, creates ExecutionNodes from data on the RequestTask.
        """
        request_task: RequestTask = self.to_mock_request_task()
        return ExecutionNode(request_task)

    def get_data_categories(self) -> Set[str]:
        """
        Returns a set of unique data categories across the collection and child fields.
        """
        collection = self.node.collection

        return set(
            chain(
                collection.data_categories,
                *[
                    field.data_categories or []
                    for field in collection.field_dict.values()
                ],
            )
        )

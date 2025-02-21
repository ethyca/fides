from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

import pydash.collections
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
    GraphDataset,
)
from fides.api.graph.graph import DatasetGraph, Edge, Node
from fides.api.graph.node_filters import (
    CustomRequestFieldFilter,
    NodeFilter,
    PolicyDataCategoryFilter,
)
from fides.api.graph.traversal_node import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.util.collection_util import Row
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


class Traversal:
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
        policy: Optional[Policy] = None,
        node_filters: Optional[List[NodeFilter]] = None,
    ):
        self.graph = graph
        self.seed_data = data
        self.policy = policy

        # Node filters are used to allow unreachable nodes to be ignored
        # if they don't apply to the given scenario
        self.node_filters = node_filters or []
        self.node_filters.append(CustomRequestFieldFilter())
        if policy:
            self.node_filters.append(PolicyDataCategoryFilter(policy))

        self.traversal_node_dict = {k: TraversalNode(v) for k, v in graph.nodes.items()}
        self.edges: Set[Edge] = graph.edges.copy()
        self.root_node = artificial_traversal_node(ROOT_COLLECTION_ADDRESS)
        for (
            start_field_address,
            seed_key,
        ) in self.extract_seed_field_addresses().items():
            self.edges.add(
                Edge(
                    FieldAddress(
                        ROOT_COLLECTION_ADDRESS.dataset,
                        ROOT_COLLECTION_ADDRESS.collection,
                        seed_key,
                    ),
                    start_field_address,
                )
            )

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
        """Traverse and call run() on each traversal_node in turn. T represents an environment that
        can provide or collect values as each traversal_node is run.

        Returns a list of termination traversal_node addresses so that we can take action on completed
        traversal.

        We define the root traversal_node as a traversal_node whose children are any nodes that have identity (seed)
        data.
        We start with
        - a queue holding only the root traversal_node.
        - a (copied) set of all of the edges in the graph.

        - Pop the first eligible traversal_node from the queue.
        - call the passed in callable node_run_function on this traversal_node. Mark this traversal_node as "finished"
        - Delete all edges from any finished nodes to this traversal_node.
        - put all of this nodes children in the queue.

        Some nodes have conditions, like "don't run me until after traversal_node X". When we pop a value from
        the queue, we are taking this into account. If the queue contains nodes, but none of them are
        eligible (e.g. Node A can't run until after B, and traversal_node B that can't run until after A)
        raise a TraversalError.

        We also raise a TraversalError if the queue is empty but some nodes have not been visited. In
        that case they are unreachable.

        """
        if environment:
            logger.info(
                "Starting traversal",
            )
        remaining_node_keys: Set[CollectionAddress] = set(
            self.traversal_node_dict.keys()
        )
        finished_nodes: dict[CollectionAddress, TraversalNode] = {}
        running_node_queue: MatchingQueue[TraversalNode] = MatchingQueue(self.root_node)
        remaining_edges: Set[Edge] = self.edges.copy()
        while not running_node_queue.is_empty():
            # this is to support the "run traversal_node A AFTER traversal_node B functionality:"
            n = running_node_queue.pop_first_match(
                lambda x: x.can_run_given(remaining_node_keys)
            )

            if n:
                node_run_fn(n, environment)
                # delete all edges between the traversal_node that's just run and any completed nodes
                for finished_node_address, finished_node in finished_nodes.items():
                    completed_edges: Set[Edge] = Edge.delete_edges(
                        remaining_edges,
                        finished_node_address,
                        cast(TraversalNode, n).address,  # type: ignore[redundant-cast]
                    )

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

                edges_to_children = pydash.collections.filter_(
                    [
                        e.split_by_address(cast(TraversalNode, n).address)  # type: ignore[redundant-cast]
                        for e in remaining_edges
                        if e.contains(n.address)
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
                remaining_node_keys.difference_update({n.address})
            else:
                # traversal traversal_node dict diff finished nodes
                logger.error(
                    "Node could not be reached given specified ordering [{}]",
                    ", ".join([str(tn.address) for tn in running_node_queue.data]),
                )
                raise TraversalError(
                    f"""Node could not be reached given the specified ordering:
                    [{', '.join([str(tn.address) for tn in running_node_queue.data])}]""",
                )

        remaining_node_keys = {
            key
            for key in remaining_node_keys
            if not self.should_exclude_node(self.traversal_node_dict[key])
        }

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

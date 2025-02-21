from __future__ import annotations

import json
from itertools import chain
from typing import Any, Dict, List, Set, Tuple

from fideslang.validation import FidesKey

from fides.api.graph.config import ROOT_COLLECTION_ADDRESS, CollectionAddress, FieldPath
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import Edge, Node
from fides.api.models.privacy_request import RequestTask, TraversalDetails
from fides.api.util.collection_util import append, partition
from fides.api.util.logger_context_utils import Contextualizable, LoggerContextKeys


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

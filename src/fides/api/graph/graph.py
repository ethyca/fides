from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from fideslang.validation import FidesKey
from loguru import logger

from fides.api.common_exceptions import ValidationError
from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    EdgeDirection,
    FieldAddress,
    FieldPath,
    GraphDataset,
    SeedAddress,
)

DataCategoryFieldMapping = Dict[CollectionAddress, Dict[FidesKey, List[FieldPath]]]


class Node:
    """A traversal_node represents a single collection as a graph traversal_node.
    Note that a traversal_node is simply a store of a graph location and connections and does not imply ordering.

    An actual traversal is made up of Traversal nodes, which can be thought of as a reified instance of
    this graph encoding a specific traversal.

    Node children are any nodes that are reachable via this traversal_node.
    """

    def __init__(self, dataset: GraphDataset, collection: Collection):
        self.address = CollectionAddress(dataset.name, collection.name)
        self.dataset = dataset
        self.collection = collection

    def __repr__(self) -> str:
        return f"Node({self.address})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False
        return other.address == self.address

    def __hash__(self) -> int:
        return hash(self.address)


class Edge:
    """A graph link uniquely defined by a pair of keys and a direction from f1->f2.
    Undirected edges are treated as a pair of f1->f2, f2->f2."""

    def __init__(self, f1: FieldAddress, f2: FieldAddress) -> None:
        if f1.collection_address() == f2.collection_address():
            raise ValidationError(f"collection self-reference not allowed {f1}<-->{f2}")
        self.f1 = f1
        self.f2 = f2

    def __repr__(self) -> str:
        return f"{self.f1}->{self.f2}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return False
        return other.f1 == self.f1 and other.f2 == self.f2

    def __hash__(self) -> int:
        return hash((self.f1, self.f2))

    def contains(self, node_address: CollectionAddress) -> bool:
        """The collection address is a prefix to either one of the endpoints."""
        return (
            self.f1.collection_address() == node_address
            or self.f2.collection_address() == node_address
        )

    def spans(self, addr_1: CollectionAddress, addr_2: CollectionAddress) -> bool:
        """True if the 2 provided addresses span the edge endpoints"""
        ds1 = self.f1.collection_address()
        ds2 = self.f2.collection_address()
        return ds1 == addr_1 and ds2 == addr_2

    def split_by_address(
        self, node_address: CollectionAddress
    ) -> Optional[Tuple[FieldAddress, FieldAddress]]:
        """Given the input traversal_node address, return the ends of this edge as an ordered pair (address, other) where
        the first element points to the input address and the second to the opposite side.
        """
        if self.f1.collection_address() == node_address:
            return self.f1, self.f2
        return None

    def ends_with_collection(self, addr: CollectionAddress) -> bool:
        """The far end of this edge points to the provided collection address"""
        return self.f2.collection_address() == addr

    @classmethod
    def delete_edges(
        cls,
        edges: Set[Edge],
        from_address: CollectionAddress,
        to_address: CollectionAddress,
    ) -> Set[Edge]:
        """Delete all edges between traversal_node address 1 and traversal_node address 2 and return the deleted edges."""
        to_delete = set(filter(lambda e: e.spans(from_address, to_address), edges))
        edges.difference_update(to_delete)
        return to_delete

    @classmethod
    def create_edge(
        cls,
        addr_1: FieldAddress,
        addr_2: FieldAddress,
        direction: Optional[EdgeDirection] = None,
    ) -> Edge:
        """Create an edge from addr_1 to addr_2 with the given direction."""
        if direction == "from":
            return Edge(addr_2, addr_1)
        if direction == "to":
            return Edge(addr_1, addr_2)
        return BidirectionalEdge(addr_1, addr_2)


class BidirectionalEdge(Edge):
    """A graph link whose direction is unspecified"""

    def __init__(self, f1: FieldAddress, f2: FieldAddress) -> None:
        super().__init__(f1, f2)
        if self.f2 < self.f1:
            self.f1, self.f2 = self.f2, self.f1

    def __repr__(self) -> str:
        return f"{self.f1}<->{self.f2}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BidirectionalEdge):
            return False
        return (other.f1 == self.f1 and other.f2 == self.f2) or (
            other.f1 == self.f2 and other.f2 == self.f1
        )

    def __hash__(self) -> int:
        return hash((self.f1, self.f2, True))

    def spans(self, addr_1: CollectionAddress, addr_2: CollectionAddress) -> bool:
        """True if the 2 provided addresses span the edge endpoints"""
        ds1 = self.f1.collection_address()
        ds2 = self.f2.collection_address()
        return (ds1 == addr_1 and ds2 == addr_2) or (ds1 == addr_2 and ds2 == addr_1)

    def split_by_address(
        self, node_address: CollectionAddress
    ) -> Optional[Tuple[FieldAddress, FieldAddress]]:
        """Given the input traversal_node address, return the ends of this edge as an ordered pair (address, other) where
        the first element points to the input address and the second to the opposite side.
        """
        if self.f1.collection_address() == node_address:
            return self.f1, self.f2
        if self.f2.collection_address() == node_address:
            return self.f2, self.f1
        return None

    def ends_with_collection(self, addr: CollectionAddress) -> bool:
        """The far end of this edge points to the provided collection address"""
        return self.contains(addr)


class DatasetGraph:
    """Graph representing the entirety of all addressable datasets.

    A graph holds a collection of nodes and an abstract graph. A reified traversal is
    generated only in reference to a specific seed, since the seeds determine which traversal_node
    (or nodes) represent the start nodes.
    """

    def __init__(self, *datasets: GraphDataset) -> None:
        """We create all edges based on field specifications.
        We also add child references to nodes. Note that this means that
        this is a destructive operation on the input datasets, as it
        will alter references within them"""

        # build nodes
        nodes = [Node(dr, ds) for dr in datasets for ds in dr.collections]
        self.nodes: dict[CollectionAddress, Node] = {
            node.address: node for node in nodes
        }

        # build links
        self.edges: Set[Edge] = set()

        for node_address, node in self.nodes.items():
            for field_path, ref_list in node.collection.references().items():
                source_field_address: FieldAddress = FieldAddress(
                    node_address.dataset, node_address.collection, *field_path.levels
                )
                for dest_field_address, direction in ref_list:
                    if dest_field_address.collection_address() not in self.nodes:
                        logger.warning(
                            "Referenced object {} does not exist", dest_field_address
                        )
                        raise ValidationError(
                            f"Referred to object {dest_field_address} does not exist"
                        )
                    self.edges.add(
                        Edge.create_edge(
                            source_field_address, dest_field_address, direction
                        )
                    )

        # collect all seed references
        self.identity_keys: dict[FieldAddress, SeedAddress] = {
            FieldAddress(
                node.address.dataset,
                node.address.collection,
                *field_path.levels,
            ): seed_address
            for node in nodes
            for field_path, seed_address in node.collection.identities().items()
        }

    @property
    def data_category_field_mapping(
        self,
    ) -> DataCategoryFieldMapping:
        """
        Maps the data_categories for each traversal_node to a list of field paths that have that
        same data category.

        For example:
        {
            "postgres_example_test_dataset:address": {
                "user.contact.address.city": [FieldPath("city")],
                "user.contact.address.street": [FieldPath("house"), FieldPath("street")],
                "system.operations": [FieldPath("id")],
                "user.contact.address.state": [FieldPath("state"]),
                "user.contact.address.postal_code": [FieldPath("zip")]
            }
        }

        """
        mapping: Dict[CollectionAddress, Dict[FidesKey, List[FieldPath]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for node_address, node in self.nodes.items():
            mapping[node_address] = node.collection.field_paths_by_category
        return mapping

    def __repr__(self) -> str:
        return f"Graph: nodes = {self.nodes.keys()}"

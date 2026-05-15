"""Test validation of erase_after references during erasure graph construction.

When a collection's erase_after references a collection that doesn't exist in
the DatasetGraph (e.g. the referenced integration was deleted), the graph
builder must reject it upfront with a clear error rather than allowing phantom
nodes to silently enter the graph and corrupt task creation.
"""

import pytest

from fides.api.common_exceptions import TraversalError
from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    GraphDataset,
    ScalarField,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.task.create_request_tasks import (
    build_erasure_networkx_digraph,
    collect_tasks_fn,
    persist_initial_erasure_request_tasks,
)


def _identity_field(name: str) -> ScalarField:
    """Create a scalar field marked as an identity seed."""
    f = ScalarField(name=name, primary_key=True)
    f.identity = "email"
    return f


def _build_graph_with_dangling_erase_after():
    """Build a DatasetGraph where one collection has erase_after pointing to
    a collection that does not exist in the graph.

    Graph layout:
        active_api (connection: active_conn)
            └── users  (identity: email, erase_after: [deleted_api.users])

    deleted_api does NOT exist in the DatasetGraph.
    """
    active_collection = Collection(
        name="users",
        fields=[_identity_field("email"), ScalarField(name="name")],
        erase_after={CollectionAddress("deleted_api", "users")},
    )

    active_dataset = GraphDataset(
        name="active_api",
        collections=[active_collection],
        connection_key="active_conn",
    )

    return DatasetGraph(active_dataset)


class TestDanglingEraseAfterReference:
    """Verify that erase_after referencing a non-existent collection is caught
    before it can corrupt erasure task creation."""

    def test_build_erasure_graph_rejects_dangling_erase_after(self):
        """build_erasure_networkx_digraph should validate that all erase_after
        references point to collections that exist in the traversal before
        building the graph. A clear error upfront prevents partial task
        creation and unrecoverable state.
        """
        dataset_graph = _build_graph_with_dangling_erase_after()

        identity = {"email": "test@example.com"}
        traversal = Traversal(dataset_graph, identity)

        traversal_nodes: dict[CollectionAddress, TraversalNode] = {}
        traversal.traverse(traversal_nodes, collect_tasks_fn)

        erasure_end_nodes = list(dataset_graph.nodes.keys())

        with pytest.raises(TraversalError, match="deleted_api:users"):
            build_erasure_networkx_digraph(traversal_nodes, erasure_end_nodes)

    def test_persist_erasure_tasks_rejects_dangling_erase_after(
        self, db, privacy_request
    ):
        """persist_initial_erasure_request_tasks should raise TraversalError
        before creating any tasks when a dangling erase_after is detected.
        """
        dataset_graph = _build_graph_with_dangling_erase_after()

        identity = {"email": "test@example.com"}
        traversal = Traversal(dataset_graph, identity)

        traversal_nodes: dict[CollectionAddress, TraversalNode] = {}
        traversal.traverse(traversal_nodes, collect_tasks_fn)

        erasure_end_nodes = list(dataset_graph.nodes.keys())

        with pytest.raises(TraversalError, match="deleted_api:users"):
            persist_initial_erasure_request_tasks(
                db,
                privacy_request,
                traversal_nodes,
                erasure_end_nodes,
                dataset_graph,
            )

        # No erasure tasks should have been created
        assert privacy_request.erasure_tasks.count() == 0

    def test_valid_erase_after_still_works(self):
        """erase_after referencing a collection that exists in the graph
        should continue to work normally.
        """
        users_collection = Collection(
            name="users",
            fields=[_identity_field("email"), ScalarField(name="name")],
        )
        orders_collection = Collection(
            name="orders",
            fields=[_identity_field("email"), ScalarField(name="total")],
            erase_after={CollectionAddress("test_dataset", "users")},
        )

        dataset = GraphDataset(
            name="test_dataset",
            collections=[users_collection, orders_collection],
            connection_key="test_conn",
        )
        dataset_graph = DatasetGraph(dataset)

        identity = {"email": "test@example.com"}
        traversal = Traversal(dataset_graph, identity)

        traversal_nodes: dict[CollectionAddress, TraversalNode] = {}
        traversal.traverse(traversal_nodes, collect_tasks_fn)

        erasure_end_nodes = list(dataset_graph.nodes.keys())

        # Should not raise
        erasure_graph = build_erasure_networkx_digraph(
            traversal_nodes, erasure_end_nodes
        )

        # orders should depend on users, not ROOT
        users_addr = CollectionAddress("test_dataset", "users")
        orders_addr = CollectionAddress("test_dataset", "orders")
        assert orders_addr in erasure_graph.successors(users_addr)

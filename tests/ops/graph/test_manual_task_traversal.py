import pytest

from fides.api.graph.config import (
    Collection,
    FieldAddress,
    FieldPath,
    GraphDataset,
    ScalarField,
    ROOT_COLLECTION_ADDRESS,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.task.manual.manual_task_utils import ManualTaskAddress


@pytest.fixture
def manual_graph() -> DatasetGraph:
    """Return a minimal graph containing a synthetic manual_data collection."""
    # Manual task synthetic dataset/collection
    manual_collection = Collection(
        name="manual_data",
        fields=[ScalarField(name="id", primary_key=True)],
        after=set(),
    )
    manual_dataset = GraphDataset(
        name="manual_connection",
        collections=[manual_collection],
        connection_key="manual_connection",
        after=set(),
    )

    # Down-stream dataset that references manual_data.id so manual node has a child
    orders_collection = Collection(
        name="orders",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(
                name="manual_id",
                references=[
                    (
                        FieldAddress("manual_connection", "manual_data", "id"),
                        None,
                    )
                ],
            ),
        ],
        after=set(),
    )
    orders_dataset = GraphDataset(
        name="orders_conn",
        collections=[orders_collection],
        connection_key="orders_conn",
        after=set(),
    )

    return DatasetGraph(manual_dataset, orders_dataset)


def build_traversal(graph: DatasetGraph) -> Traversal:
    """Helper to instantiate a Traversal for provided graph."""
    # Seed data can be empty – manual tasks don't depend on identity values
    return Traversal(graph, data={})


def test_manual_node_present(manual_graph):
    """The traversal should contain the synthetic manual_data node."""
    traversal = build_traversal(manual_graph)

    manual_addr = ManualTaskAddress.create("manual_connection")
    assert manual_addr in traversal.traversal_node_dict, "manual_data node missing from traversal"


def test_root_edge_to_manual_node(manual_graph):
    """Traversal edges should include ROOT.id -> manual_data.id link."""
    traversal = build_traversal(manual_graph)

    manual_addr = ManualTaskAddress.create("manual_connection")
    expected_src = FieldAddress(
        ROOT_COLLECTION_ADDRESS.dataset, ROOT_COLLECTION_ADDRESS.collection, "id"
    )
    expected_dst = manual_addr.field_address(FieldPath("id"))

    assert any(
        edge.f1 == expected_src and edge.f2 == expected_dst for edge in traversal.edges
    ), "ROOT -> manual_data edge not found in traversal"


def test_manual_graph_is_traversable(manual_graph):
    """Building a Traversal should not raise a reachability error."""
    Traversal(manual_graph, data={}) 
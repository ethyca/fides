from fides.api.graph.config import CollectionAddress, FieldAddress, FieldPath
from fides.api.graph.graph import Edge
from fides.api.graph.traversal import TraversalNode

from .test_graph_traversal import generate_node


class TestTraversalNode:
    def test_add_child(self) -> None:
        tn = TraversalNode(generate_node("a", "b", "c", "c2"))
        child_1 = TraversalNode(generate_node("d", "e", "f", "f2"))
        tn.add_child(
            child_1, Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))
        )
        assert tn.children == {
            CollectionAddress("d", "e"): [(child_1, FieldPath("c"), FieldPath("f"))]
        }
        assert child_1.parents == {
            CollectionAddress("a", "b"): [(tn, FieldPath("c"), FieldPath("f"))]
        }

        tn.add_child(
            child_1,
            Edge(FieldAddress("a", "b", "c", "c2"), FieldAddress("d", "e", "f", "f2")),
        )
        assert tn.children == {
            CollectionAddress("d", "e"): [
                (child_1, FieldPath("c"), FieldPath("f")),
                (child_1, FieldPath("c", "c2"), FieldPath("f", "f2")),
            ]
        }
        assert child_1.parents == {
            CollectionAddress("a", "b"): [
                (tn, FieldPath("c"), FieldPath("f")),
                (tn, FieldPath("c", "c2"), FieldPath("f", "f2")),
            ]
        }

        child_2 = TraversalNode(generate_node("h", "i", "j"))
        tn.add_child(
            child_2,
            Edge(FieldAddress("a", "b", "c", "c2"), FieldAddress("h", "i", "j")),
        )
        assert tn.children == {
            CollectionAddress("d", "e"): [
                (child_1, FieldPath("c"), FieldPath("f")),
                (child_1, FieldPath("c", "c2"), FieldPath("f", "f2")),
            ],
            CollectionAddress("h", "i"): [
                (child_2, FieldPath("c", "c2"), FieldPath("j"))
            ],
        }
        assert child_2.parents == {
            CollectionAddress("a", "b"): [(tn, FieldPath("c", "c2"), FieldPath("j"))]
        }

        assert tn.outgoing_edges() == {
            Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f")),
            Edge(FieldAddress("a", "b", "c", "c2"), FieldAddress("d", "e", "f", "f2")),
            Edge(FieldAddress("a", "b", "c", "c2"), FieldAddress("h", "i", "j")),
        }

        assert tn.incoming_edges() == set()

        assert child_1.outgoing_edges() == set()

        assert child_1.incoming_edges() == {
            Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f")),
            Edge(FieldAddress("a", "b", "c", "c2"), FieldAddress("d", "e", "f", "f2")),
        }

    def test_can_run_given(self) -> None:
        tn = TraversalNode(generate_node("a", "b", "c"))
        tn.node.dataset.after.update(["f1", "f2"])
        tn.node.collection.after.update(
            [CollectionAddress("x", "y"), CollectionAddress("z", "z1")]
        )

        # data dataset run after
        assert (
            tn.can_run_given(
                {CollectionAddress("f1", "_"), CollectionAddress("_", "_")}
            )
            is False
        )
        assert (
            tn.can_run_given({CollectionAddress("_", "_"), CollectionAddress("_", "_")})
            is True
        )

        # data set run after
        assert tn.can_run_given({CollectionAddress("x", "_")}) is True
        assert (
            tn.can_run_given({CollectionAddress("x", "y"), CollectionAddress("_", "_")})
            is False
        )
        assert (
            tn.can_run_given(
                {CollectionAddress("z", "z1"), CollectionAddress("_", "_")}
            )
            is False
        )
        assert (
            tn.can_run_given(
                {CollectionAddress("z", "z2"), CollectionAddress("_", "_")}
            )
            is True
        )

    def test_is_root_node(self):
        tn = TraversalNode(generate_node("__ROOT__", "__ROOT__"))
        assert tn.is_root_node()

        tn = TraversalNode(generate_node("a", "b", "c", "c2"))
        assert not tn.is_root_node()

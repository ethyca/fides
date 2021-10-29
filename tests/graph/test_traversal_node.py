from fidesops.graph.traversal import *
from .test_graph_traversal import generate_node


def test_add_child() -> None:
    def field_tuples(tn: TraversalNode, da: CollectionAddress):
        return {(t[1], t[2]) for t in tn.children[da]}

    tn = TraversalNode(generate_node("a", "b", "c", "c2"))
    child_1 = TraversalNode(generate_node("d", "e", "f", "f2"))
    tn.add_child(
        child_1, Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))
    )
    assert tn.children == {CollectionAddress("d", "e"): [(child_1, "c", "f")]}
    tn.add_child(
        child_1, Edge(FieldAddress("a", "b", "c2"), FieldAddress("d", "e", "f2"))
    )
    assert tn.children == {
        CollectionAddress("d", "e"): [(child_1, "c", "f"), (child_1, "c2", "f2")]
    }
    child_2 = TraversalNode(generate_node("h", "i", "j"))
    tn.add_child(
        child_2, Edge(FieldAddress("a", "b", "c2"), FieldAddress("h", "i", "j"))
    )
    assert tn.children == {
        CollectionAddress("d", "e"): [(child_1, "c", "f"), (child_1, "c2", "f2")],
        CollectionAddress("h", "i"): [(child_2, "c2", "j")],
    }


def test_can_run_given() -> None:
    tn = TraversalNode(generate_node("a", "b", "c"))
    tn.node.dataset.after.update(["f1", "f2"])
    tn.node.collection.after.update(
        [CollectionAddress("x", "y"), CollectionAddress("z", "z1")]
    )

    # data dataset run after
    assert (
        tn.can_run_given({CollectionAddress("f1", "_"), CollectionAddress("_", "_")})
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
        tn.can_run_given({CollectionAddress("z", "z1"), CollectionAddress("_", "_")})
        is False
    )
    assert (
        tn.can_run_given({CollectionAddress("z", "z2"), CollectionAddress("_", "_")})
        is True
    )

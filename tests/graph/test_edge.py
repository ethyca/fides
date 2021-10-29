from fidesops.graph.graph import *
from fidesops.common_exceptions import ValidationError
import pytest


def test_contains() -> None:
    edge = Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))
    assert edge.contains(CollectionAddress("a", "b"))
    assert edge.contains(CollectionAddress("d", "e"))
    assert not edge.contains(CollectionAddress("b", "c"))
    assert not edge.contains(CollectionAddress("x", "y"))


def test_split_by_address() -> None:
    edge = Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))
    assert edge.split_by_address(CollectionAddress("a", "b")) == (
        FieldAddress("a", "b", "c"),
        FieldAddress("d", "e", "f"),
    )
    assert edge.split_by_address(CollectionAddress("d", "e")) is None
    assert edge.split_by_address(CollectionAddress("e", "f")) is None

    b_edge = BidirectionalEdge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))

    assert b_edge.split_by_address(CollectionAddress("a", "b")) == (
        FieldAddress("a", "b", "c"),
        FieldAddress("d", "e", "f"),
    )
    assert b_edge.split_by_address(CollectionAddress("d", "e")) == (
        FieldAddress("d", "e", "f"),
        FieldAddress("a", "b", "c"),
    )

    assert b_edge.split_by_address(CollectionAddress("x", "y")) == None


def test_spans() -> None:
    edge = Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))
    assert edge.spans(CollectionAddress("a", "b"), CollectionAddress("d", "e"))
    assert not edge.spans(CollectionAddress("d", "e"), CollectionAddress("a", "b"))
    assert not edge.spans(CollectionAddress("a", "b"), CollectionAddress("a", "b"))


def test_delete_edges() -> None:
    edges = {
        Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f")),
        Edge(FieldAddress("a", "b", "c"), FieldAddress("a", "b1", "d")),
    }
    assert Edge.delete_edges(
        edges, CollectionAddress("a", "b"), CollectionAddress("a", "b1")
    ) == {Edge(FieldAddress("a", "b", "c"), FieldAddress("a", "b1", "d"))}

    assert edges == {Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))}
    assert (
        Edge.delete_edges(
            edges, CollectionAddress("x", "x"), CollectionAddress("a", "b")
        )
        == set()
    )


def test_disallow_self_reference() -> None:
    with pytest.raises(ValidationError):
        Edge(FieldAddress("a", "b", "c"), FieldAddress("a", "b", "f"))


def test_eq() -> None:
    f1 = FieldAddress("A", "B", "C")
    f2 = FieldAddress("D", "E", "F")
    assert Edge(f1, f2) == Edge(f1, f2)
    assert Edge(f1, f2) != Edge(f2, f1)
    assert Edge(f1, f2) != BidirectionalEdge(f2, f1)
    assert BidirectionalEdge(f1, f2) == BidirectionalEdge(f2, f1)

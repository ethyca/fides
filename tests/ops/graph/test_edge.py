import pytest
from fidesops.ops.common_exceptions import ValidationError
from fidesops.ops.graph.graph import *


class TestEdge:
    def test_eq(self) -> None:
        f1 = FieldAddress("A", "B", "C")
        f2 = FieldAddress("D", "E", "F")
        assert Edge(f1, f2) == Edge(f1, f2)
        assert Edge(f1, f2) != Edge(f2, f1)
        assert Edge(f1, f2) != BidirectionalEdge(f2, f1)
        assert BidirectionalEdge(f1, f2) == BidirectionalEdge(f2, f1)

        f3 = FieldAddress("D", "E", "F", "G")  # Nested field address
        assert Edge(f1, f3) == Edge(f1, f3)
        assert Edge(f3, f1) != Edge(f1, f3)
        assert BidirectionalEdge(f1, f3) == BidirectionalEdge(f3, f1)

    def test_contains(self) -> None:
        edge = Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f", "g"))
        assert edge.contains(CollectionAddress("a", "b"))
        assert edge.contains(CollectionAddress("d", "e"))
        assert not edge.contains(CollectionAddress("b", "c"))
        assert not edge.contains(CollectionAddress("x", "y"))

    def test_spans(self) -> None:
        edge = Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))
        assert edge.spans(CollectionAddress("a", "b"), CollectionAddress("d", "e"))
        assert not edge.spans(CollectionAddress("d", "e"), CollectionAddress("a", "b"))
        assert not edge.spans(CollectionAddress("a", "b"), CollectionAddress("a", "b"))

        bid_edge = BidirectionalEdge(
            FieldAddress("a", "b", "c", "d"), FieldAddress("d", "e", "f")
        )
        assert bid_edge.spans(CollectionAddress("a", "b"), CollectionAddress("d", "e"))
        assert bid_edge.spans(
            CollectionAddress("d", "e"), CollectionAddress("a", "b")
        )  # Checked going both ways!
        assert not bid_edge.spans(
            CollectionAddress("a", "b"), CollectionAddress("a", "b")
        )

    def test_split_by_address(self) -> None:
        edge = Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f", "g"))
        assert edge.split_by_address(CollectionAddress("a", "b")) == (
            FieldAddress("a", "b", "c"),
            FieldAddress("d", "e", "f", "g"),
        )
        assert edge.split_by_address(CollectionAddress("d", "e")) is None
        assert edge.split_by_address(CollectionAddress("e", "f")) is None

        b_edge = BidirectionalEdge(
            FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f", "g")
        )

        assert b_edge.split_by_address(CollectionAddress("a", "b")) == (
            FieldAddress("a", "b", "c"),
            FieldAddress("d", "e", "f", "g"),
        )
        assert b_edge.split_by_address(CollectionAddress("d", "e")) == (
            FieldAddress("d", "e", "f", "g"),
            FieldAddress("a", "b", "c"),
        )

        assert b_edge.split_by_address(CollectionAddress("x", "y")) is None

    def test_ends_with_collection(self):
        edge = Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f", "g"))
        assert edge.ends_with_collection(CollectionAddress("d", "e"))
        assert not edge.ends_with_collection(CollectionAddress("a", "b"))

        edge = BidirectionalEdge(
            FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f", "g")
        )
        assert edge.ends_with_collection(CollectionAddress("d", "e"))
        assert edge.ends_with_collection(CollectionAddress("a", "b"))

    def test_delete_edges(self) -> None:
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

        assert edges == {Edge(FieldAddress("a", "b", "c"), FieldAddress("d", "e", "f"))}
        assert (
            Edge.delete_edges(
                edges, CollectionAddress("d", "e"), CollectionAddress("a", "b")
            )
            == set()
        )

    def test_disallow_self_reference(self) -> None:
        with pytest.raises(ValidationError):
            Edge(FieldAddress("a", "b", "c"), FieldAddress("a", "b", "f"))

    def test_create_edge(self):
        f1 = FieldAddress("a", "b", "c")
        f2 = FieldAddress("d", "e", "f", "g")
        assert Edge.create_edge(f1, f2) == BidirectionalEdge(f1, f2)

        assert Edge.create_edge(f1, f2, "from") == Edge(f2, f1)
        assert Edge.create_edge(f1, f2, "to") == Edge(f1, f2)

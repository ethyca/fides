import pytest

from fidesops.graph.config import *


def test_collection_address_compare() -> None:
    assert CollectionAddress("A", "B") == CollectionAddress("A", "B")
    assert not CollectionAddress("A", "B") == 1
    assert CollectionAddress("A", "B") < CollectionAddress("C", "D")


def test_field_address_compare() -> None:
    assert FieldAddress("A", "B", "C") == FieldAddress("A", "B", "C")
    assert not FieldAddress("A", "B", "C") == 1
    assert FieldAddress("A", "B", "C") < FieldAddress("C", "D", "E")


def test_field_address_member_odf() -> None:
    f = FieldAddress("A", "B", "C")
    assert f.is_member_of(CollectionAddress("A", "B"))
    assert not f.is_member_of(CollectionAddress("B", "A"))
    f.is_member_of(CollectionAddress("X", "Y"))


def test_collection_address_to_string():
    addr = CollectionAddress("A", "B")
    assert CollectionAddress.from_string(str(addr)) == addr
    assert CollectionAddress.from_string(
        "postgres_example:customer"
    ) == CollectionAddress("postgres_example", "customer")
    with pytest.raises(FidesopsException):
        CollectionAddress.from_string("A")
    with pytest.raises(FidesopsException):
        CollectionAddress.from_string("A:B:C")


def test_collection_identities() -> None:
    ds = Collection(
        name="t3",
        fields=[
            Field(name="f1", identity="email"),
            Field(name="f2", identity="id"),
            Field(name="f3"),
        ],
    )
    assert ds.identities() == {"f1": "email", "f2": "id"}


def test_collection_references() -> None:
    ds = Collection(
        name="t3",
        fields=[
            Field(
                name="f1",
                references=[
                    (FieldAddress("a", "b", "c"), None),
                    (FieldAddress("a", "b", "d"), None),
                ],
            ),
            Field(name="f2", references=[(FieldAddress("d", "e", "f"), None)]),
            Field(name="f3"),
        ],
    )
    assert ds.references() == {
        "f1": [
            (FieldAddress("a", "b", "c"), None),
            (FieldAddress("a", "b", "d"), None),
        ],
        "f2": [(FieldAddress("d", "e", "f"), None)],
    }


def test_directional_references() -> None:
    ds = Collection(
        name="t3",
        fields=[
            Field(
                name="f1",
                references=[
                    (FieldAddress("a", "b", "c"), "from"),
                    (FieldAddress("a", "b", "d"), "to"),
                ],
            ),
            Field(name="f2", references=[(FieldAddress("d", "e", "f"), None)]),
            Field(name="f3"),
        ],
    )
    assert ds.references() == {
        "f1": [
            (FieldAddress("a", "b", "c"), "from"),
            (FieldAddress("a", "b", "d"), "to"),
        ],
        "f2": [(FieldAddress("d", "e", "f"), None)],
    }

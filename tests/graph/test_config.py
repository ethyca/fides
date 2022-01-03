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


def test_collection_field_map():
    c = Collection(
        name="t3",
        fields=[ScalarField(name="f1")],
    )
    assert c.field("f1").name == "f1"
    assert c.field("not found") is None


def test_collection_identities() -> None:
    ds = Collection(
        name="t3",
        fields=[
            ScalarField(name="f1", identity="email"),
            ScalarField(name="f2", identity="id"),
            ScalarField(name="f3"),
        ],
    )
    assert ds.identities() == {"f1": "email", "f2": "id"}


def test_collection_references() -> None:
    ds = Collection(
        name="t3",
        fields=[
            ScalarField(
                name="f1",
                references=[
                    (FieldAddress("a", "b", "c"), None),
                    (FieldAddress("a", "b", "d"), None),
                ],
            ),
            ScalarField(name="f2", references=[(FieldAddress("d", "e", "f"), None)]),
            ScalarField(name="f3"),
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
            ScalarField(
                name="f1",
                references=[
                    (FieldAddress("a", "b", "c"), "from"),
                    (FieldAddress("a", "b", "d"), "to"),
                ],
            ),
            ScalarField(name="f2", references=[(FieldAddress("d", "e", "f"), None)]),
            ScalarField(name="f3"),
        ],
    )
    assert ds.references() == {
        "f1": [
            (FieldAddress("a", "b", "c"), "from"),
            (FieldAddress("a", "b", "d"), "to"),
        ],
        "f2": [(FieldAddress("d", "e", "f"), None)],
    }


def test_generate_field() -> None:
    def _is_string_field(f: Field):
        return isinstance(f, ScalarField) and f.data_type_converter.name == "string"

    string_field = generate_field(
        name="str",
        data_categories=["category"],
        identity="identity",
        data_type_name="string",
        references=[],
        is_pk=False,
        length=0,
        is_array=False,
        sub_fields=[],
    )
    array_field = generate_field(
        name="arr",
        data_categories=["category"],
        identity="identity",
        data_type_name="string",
        references=[],
        is_pk=False,
        length=0,
        is_array=True,
        sub_fields=[],
    )
    object_field = generate_field(
        name="obj",
        data_categories=["category"],
        identity="identity",
        data_type_name="object",
        references=[],
        is_pk=False,
        length=0,
        is_array=False,
        sub_fields=[string_field, array_field],
    )
    object_array_field = generate_field(
        name="obj_a",
        data_categories=["category"],
        identity="identity",
        data_type_name="string",
        references=[],
        is_pk=False,
        length=0,
        is_array=True,
        sub_fields=[string_field, object_field],
    )

    assert _is_string_field(string_field)
    assert isinstance(array_field, ScalarField) and array_field.is_array
    assert isinstance(object_field, ObjectField) and _is_string_field(
        object_field.fields["str"]
    )
    assert (
        isinstance(object_field.fields["arr"], ScalarField)
        and object_field.fields["arr"].is_array
        and _is_string_field(object_field.fields["str"])
    )
    assert isinstance(object_array_field, ObjectField) and object_array_field.is_array
    assert object_array_field.fields["obj"] == object_field

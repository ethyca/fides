import pydantic
import pytest

from fidesops.common_exceptions import ValidationError
from fidesops.graph.config import *
from fidesops.graph.data_type import (
    IntTypeConverter,
    StringTypeConverter,
    BooleanTypeConverter,
    NoOpTypeConverter,
    ObjectTypeConverter,
)


class TestCollectionAddress:
    def test_collection_address_value(self):
        assert CollectionAddress("A", "B").value == "A:B"

    def test_collection_address_compare(self) -> None:
        assert CollectionAddress("A", "B") == CollectionAddress("A", "B")
        assert not CollectionAddress("A", "B") == 1
        assert CollectionAddress("A", "B") < CollectionAddress("C", "D")

    def test_field_address(self):
        collection_addr = CollectionAddress("A", "B")
        assert collection_addr.field_address(FieldPath("C")) == FieldAddress(
            "A", "B", "C"
        )

        assert collection_addr.field_address(
            FieldPath("C", "D", "E", "F")
        ) == FieldAddress("A", "B", "C", "D", "E", "F")

    def test_collection_address_from_string(self):
        address = CollectionAddress("A", "B")
        assert CollectionAddress.from_string("A:B") == address
        assert CollectionAddress.from_string(
            "postgres_example:customer"
        ) == CollectionAddress("postgres_example", "customer")
        with pytest.raises(FidesopsException):
            CollectionAddress.from_string("A")
        with pytest.raises(FidesopsException):
            CollectionAddress.from_string("A:B:C")


class TestFieldAddress:
    def test_field_path_attr(self):
        assert FieldAddress("A", "B", "C").field_path == FieldPath("C")
        assert FieldAddress("A", "B", "C").value == "A:B:C"

        assert FieldAddress("A", "B", "C", "D", "E").field_path == FieldPath(
            "C", "D", "E"
        )
        assert FieldAddress("A", "B", "C", "D", "E").value == "A:B:C.D.E"

        assert FieldAddress("A", "B").field_path == FieldPath()

    def test_field_address_compare(self) -> None:
        assert FieldAddress("A", "B", "C") == FieldAddress("A", "B", "C")
        assert FieldAddress("A", "B", "C") < FieldAddress("C", "D", "E")
        assert FieldAddress("A", "B", "C", "D") < FieldAddress("C", "D", "D", "E")

    def test_field_address_member_of(self) -> None:
        f = FieldAddress("A", "B", "C")
        assert f.is_member_of(CollectionAddress("A", "B"))
        assert not f.is_member_of(CollectionAddress("B", "A"))
        assert not f.is_member_of(CollectionAddress("X", "Y"))

    def test_field_address_collection_address(self):
        assert FieldAddress("A", "B", "C").collection_address() == CollectionAddress(
            "A", "B"
        )
        assert FieldAddress(
            "A", "B", "C", "D", "E"
        ).collection_address() == CollectionAddress("A", "B")


class TestCollection:
    def test_collection_field_dict(self):
        """Property maps FieldPaths to Fields"""
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
                ScalarField(
                    name="f2", references=[(FieldAddress("d", "e", "f"), None)]
                ),
                ScalarField(name="f3"),
                ObjectField(name="f4", fields={"f5": ScalarField(name="f5")}),
            ],
        )

        assert ds.field_dict == {
            FieldPath("f1"): ds.fields[0],
            FieldPath("f2"): ds.fields[1],
            FieldPath("f3"): ds.fields[2],
            FieldPath("f4"): ds.fields[3],
            FieldPath("f4", "f5"): ds.fields[3].fields["f5"],
        }

        assert ds.top_level_field_dict == {
            FieldPath("f1"): ds.fields[0],
            FieldPath("f2"): ds.fields[1],
            FieldPath("f3"): ds.fields[2],
            FieldPath("f4"): ds.fields[3],
        }

    def test_collection_field(self):
        c = Collection(
            name="t3",
            fields=[ScalarField(name="f1")],
        )
        assert c.field(field_path=FieldPath("f1")).name == "f1"
        assert c.field(FieldPath("not found")) is None

    def test_collection_identities(self) -> None:
        ds = Collection(
            name="t3",
            fields=[
                ScalarField(name="f1", identity="email"),
                ScalarField(name="f2", identity="id"),
                ScalarField(name="f3"),
                ObjectField(
                    name="f4", fields={"f5": ScalarField(name="f5", identity="ssn")}
                ),
            ],
        )
        assert ds.identities() == {
            FieldPath("f1"): "email",
            FieldPath("f2"): "id",
            FieldPath("f4", "f5"): "ssn",
        }

    def test_collection_references(self) -> None:
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
                ScalarField(
                    name="f2", references=[(FieldAddress("d", "e", "f"), None)]
                ),
                ScalarField(name="f3"),
                ObjectField(
                    name="f4",
                    fields={
                        "f5": ScalarField(
                            name="f5",
                            references=[
                                (FieldAddress("g", "h", "i", "j"), None),
                            ],
                        )
                    },
                ),
            ],
        )
        assert ds.references() == {
            FieldPath("f1"): [
                (FieldAddress("a", "b", "c"), None),
                (FieldAddress("a", "b", "d"), None),
            ],
            FieldPath("f2"): [(FieldAddress("d", "e", "f"), None)],
            FieldPath("f4", "f5"): [(FieldAddress("g", "h", "i", "j"), None)],
        }

    def test_directional_references(self) -> None:
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
                ScalarField(
                    name="f2", references=[(FieldAddress("d", "e", "f"), None)]
                ),
                ScalarField(name="f3"),
            ],
        )
        assert ds.references() == {
            FieldPath("f1"): [
                (FieldAddress("a", "b", "c"), "from"),
                (FieldAddress("a", "b", "d"), "to"),
            ],
            FieldPath("f2"): [(FieldAddress("d", "e", "f"), None)],
        }

    def test_field_paths_by_category(self):
        ds = Collection(
            name="t3",
            fields=[
                ScalarField(
                    name="f1",
                    references=[
                        (FieldAddress("a", "b", "c"), None),
                        (FieldAddress("a", "b", "d"), None),
                    ],
                    data_categories=["test_category_apple"],
                ),
                ScalarField(name="f3", data_categories=["test_category_apple"]),
                ObjectField(
                    name="f4",
                    fields={
                        "f2": ScalarField(
                            name="f2",
                            data_categories=["test_category_banana"],
                            references=[(FieldAddress("d", "e", "f"), None)],
                        )
                    },
                ),
            ],
        )

        assert ds.field_paths_by_category == {
            "test_category_apple": [
                FieldPath("f1"),
                FieldPath("f3"),
            ],  # Applies to two separate fields
            "test_category_banana": [
                FieldPath("f4", "f2")
            ],  # Applies to a nested field
        }


class TestField:
    def test_generate_field(self) -> None:
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
            return_all_elements=None,
            read_only=None,
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
            return_all_elements=True,
            read_only=None,
        )
        object_field = generate_field(
            name="obj",
            data_categories=[],
            identity="identity",
            data_type_name="object",
            references=[],
            is_pk=False,
            length=0,
            is_array=False,
            sub_fields=[string_field, array_field],
            return_all_elements=None,
            read_only=None,
        )
        object_array_field = generate_field(
            name="obj_a",
            data_categories=[],
            identity="identity",
            data_type_name="string",
            references=[],
            is_pk=False,
            length=0,
            is_array=True,
            sub_fields=[string_field, object_field],
            return_all_elements=None,
            read_only=None,
        )

        assert _is_string_field(string_field)
        assert isinstance(array_field, ScalarField) and array_field.is_array
        assert array_field.return_all_elements
        assert isinstance(object_field, ObjectField) and _is_string_field(
            object_field.fields["str"]
        )
        assert (
            isinstance(object_field.fields["arr"], ScalarField)
            and object_field.fields["arr"].is_array
            and _is_string_field(object_field.fields["str"])
        )
        assert (
            isinstance(object_array_field, ObjectField) and object_array_field.is_array
        )
        assert object_array_field.fields["obj"] == object_field

    def test_field_data_type(self):
        field = ScalarField(
            name="string test", data_type_converter=StringTypeConverter()
        )
        assert field.data_type() == "string"

        field = ScalarField(name="integer test", data_type_converter=IntTypeConverter())
        assert field.data_type() == "integer"

        field = ScalarField(
            name="integer test", data_type_converter=NoOpTypeConverter()
        )
        assert field.data_type() == "None"

        field = ObjectField(
            name="integer test", data_type_converter=ObjectTypeConverter(), fields=[]
        )
        assert field.data_type() == "object"

    def test_field_collect_matching(self):
        """Creates a deeply nested (3 levels) object field.
        Runs collect_matching on the object field, looking for data categories that exist at every level,
        and verifying all three levels are returned
        """
        apt_no_sub_field = ScalarField(
            name="apartment_no",
            primary_key=False,
            data_type_converter=IntTypeConverter(),
            data_categories=["user.provided.identifiable.contact.street"],
        )
        street_address_sub_field = ScalarField(
            name="street_address",
            primary_key=False,
            data_type_converter=StringTypeConverter(),
            data_categories=["user.provided.identifiable.contact.street"],
        )
        is_apartment_sub_field = ScalarField(
            name="is_apartment",
            primary_key=False,
            data_type_converter=BooleanTypeConverter(),
        )

        street_field = ObjectField(
            name="street",
            data_categories=[],
            primary_key=False,
            fields={
                "street_address": street_address_sub_field,
                "apt_no": apt_no_sub_field,
                "is_apartment": is_apartment_sub_field,
            },
        )

        contact_info_field = ObjectField(
            name="contact",
            data_categories=[],
            fields={"address": street_field},
        )

        def is_street_category(field):
            return "user.provided.identifiable.contact.street" in (
                field.data_categories or []
            )

        # ObjectField collect_matching - nested fields selected.
        results = contact_info_field.collect_matching(is_street_category)
        assert results == {
            FieldPath("contact", "street", "street_address"): street_address_sub_field,
            FieldPath("contact", "street", "apartment_no"): apt_no_sub_field,
        }

        # ScalarField collect_matching
        assert is_apartment_sub_field.collect_matching(is_street_category) == {}
        assert apt_no_sub_field.collect_matching(is_street_category) == {
            FieldPath("apartment_no"): apt_no_sub_field
        }

    def test_generate_object_field_with_data_categories(self):
        apt_no_sub_field = ScalarField(
            name="apartment_no",
            primary_key=False,
            data_type_converter=IntTypeConverter(),
            data_categories=["user.provided.identifiable.contact.street"],
        )

        with pytest.raises(pydantic.error_wrappers.ValidationError):
            generate_field(
                name="obj",
                data_categories=["A.B.C"],
                identity="identity",
                data_type_name="object",
                references=[],
                is_pk=False,
                length=0,
                is_array=False,
                sub_fields=[apt_no_sub_field],
                return_all_elements=None,
                read_only=False,
            )

    def test_generate_read_only_scalar_field(self):
        field = generate_field(
            name="id",
            data_categories=["A.B.C"],
            identity=None,
            data_type_name="string",
            references=[],
            is_pk=False,
            length=0,
            is_array=False,
            sub_fields=[],
            return_all_elements=None,
            read_only=True,
        )
        assert isinstance(field, ScalarField)
        assert field.read_only


class TestFieldPath:
    def test_init(self):
        assert FieldPath("a", "b").string_path == "a.b"
        assert FieldPath("a").string_path == "a"

        assert FieldPath("a", "b", "c", "d").levels == ("a", "b", "c", "d")
        assert FieldPath("a").levels == ("a",)

    def test_comparison(self):
        assert FieldPath("a", "b") == FieldPath("a", "b")
        assert FieldPath("a", "b") != FieldPath("b", "a")

        assert FieldPath("a", "b") < FieldPath("a", "c")
        assert FieldPath("a", "b") < FieldPath("a", "c", "d")
        assert FieldPath("a", "b") < FieldPath("b", "a")

    def test_prepend(self):
        assert FieldPath("a").prepend("b") == FieldPath("b", "a")
        assert FieldPath("a", "b", "c", "d").prepend("e") == FieldPath(
            "e", "a", "b", "c", "d"
        )

    def test_parse(self):
        assert FieldPath.parse("a") == FieldPath("a")
        assert FieldPath.parse("a.b.c.d.e") == FieldPath("a", "b", "c", "d", "e")

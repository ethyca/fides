"""
 These objects correspond to the structure of the configurations that will form nodes from dataset and collection
 representations.

  The language here is intended to be more general than SQL-specific language, since the intention here is to be able to
  reference many different kinds of data resources. If we think of a traditional SQL database as composed of
 Schemas, Tables, and Fields, in this nomenclature
 Schema == Dataset: any abstract data source that may contain multiple data sets
 Table == Collection:  a set of identifiable fields (e.g. rows of data)
 Field == Field : a single field in a collection, addressable by name

Some examples:
 For a mongo db, Dataset/Collection/Field == Database/collection/field.
 For an API dataset,  Dataset/Collection/Field == API/endpoint/json response member

 In any case we will form a graph of nodes, where each traversal_node corresponds to a single collection in a single dataset, and
 connections can be made between any field in any one dataset to any other (with the exception of self-references, which
 are currently disallowed in this implementation).

 Each of these objects is identified by a unique string key/name ,and so a collection, belonging to a Dataset,
 can be identified by the unique tuple

 (data dataset name, data set name),

 referred to as a Collection Address. Similarly each field has a field address of the form
 (data dataset name, data set name, field name)

  uniquely identifying it in the graph. Since connections are field address <---> field address, we store a set of references on each field of their destinations.


After specifications:
 Both collections and Datasets support the specification of "after" addresses, to support manually tweaked iteration order.
 A Dataset "after" points to another data dataset. It means that any collection in this traversal_node will not be traversed until every traversal_node
 in the "after traversal_node is traversed.

 A collection "after" points to another collection. It means that this collection will not be traversed until after the traversal_node specified
 in the after Collection Address list is traversed.

 If this reordering cannot be satisfied it is an error condition (unreachable traversal_node).


Field identities:
 Field identities are pointers to seed values. They indicate that this field can be populated with seed values, and so are
 eligible as traversal start nodes.

 If the indicated seed value is not present the traversal_node will not be chosen as a start traversal_node. This means that different seed values
 may generate different traversal orderings.

 For example,
   Dataset(
            name="mysql",
            after="mysql2"
            collections=[ Collection( name="users", after=("mysql","addresses")
                fields=[
                    Field(name="id"),
                    Field(name="email", identity= "email",
                    Field(name="name", references=[(("mongo", "users", "username")),"to")]),
        ],
    )

   means
 - create a traversal_node ("mysql", "users")
 - this traversal_node will not run until all nodes in the data dataset "mysql2" have run
 - this nodes "name" field references "mongo.users.username".
 - this traversal_node will starting with the seed value {"email":"test@test.com", "id":1} will be populated with
 email == test@test.com
 - this traversal_node will not be run until after ("mysql", "addresses")

 a traversal beginning with this traversal_node would then look like
  - select all values in mysql.users where email == "test@test.com"
  - select all values in mongo.users where the username is in (any of the "name" fields in the rows found in the previous step.

  Note that this makes no statements about _how_ this data is to be retrieved. In particular many data stores will need special
  instructions (such as json paths) to extract data.


"""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from re import match, search
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Tuple, Union

from fideslang.models import FieldMaskingStrategyOverride, MaskingStrategyOverride
from fideslang.validation import FidesKey
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from fides.api.common_exceptions import FidesopsException
from fides.api.graph.data_type import (
    DataType,
    DataTypeConverter,
    get_data_type_converter,
)
from fides.api.schemas.partitioning import TimeBasedPartitioning
from fides.api.schemas.partitioning.time_based_partitioning import (
    validate_partitioning_list,
)
from fides.api.util.collection_util import merge_dicts
from fides.api.util.querytoken import QueryToken

DatasetAddress = str
SeedAddress = str
EdgeDirection = Literal["from", "to"]


class CollectionAddress:
    """The representation of a collection in the graph, specified by
    (data dataset name, collection name)"""

    def __init__(self, dataset: str, collection: str):
        self.dataset = dataset
        self.collection = collection
        self.value: str = ":".join((dataset, collection))

    def __repr__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CollectionAddress):
            return False
        return other.value == self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: CollectionAddress) -> bool:
        return self.value < other.value

    @staticmethod
    def from_string(address_str: str) -> CollectionAddress:
        """Generate a collection address from a string of the form 'dataset:collection'
        (that is, the form generated by Collection.__repr__)"""
        try:
            return CollectionAddress(*address_str.split(":"))
        except Exception:
            raise FidesopsException(
                f"'{address_str}' is not a valid collection address"
            )

    def field_address(self, field_path: FieldPath) -> FieldAddress:
        """Create a field address appended to this collection address.

        collection_address.field_address(FieldPath('a', 'b', 'c', 'd')) = dataset_name:collection_name:a.b.c.d
        """
        return FieldAddress(self.dataset, self.collection, *field_path.levels)


ROOT_COLLECTION_ADDRESS: CollectionAddress = CollectionAddress("__ROOT__", "__ROOT__")
"""Define a start traversal_node that all seed nodes begin from"""
TERMINATOR_ADDRESS = CollectionAddress("__TERMINATE__", "__TERMINATE__")
"""An address that corresponds to traversal termination"""


class FieldPath:
    """Fields are addressable by a (possibly) nested name. This key
    represents a field name held as a tuple of possibly descending levels.
    A scalar field is represented as a single-element tuple.

    Examples:
    FieldPath('a', 'b', 'c', 'd').levels = ('a', 'b', 'c', 'd')
    FieldPath('a', 'b', 'c', 'd').string_path = 'a.b.c.d'

    FieldPath('a').levels = ('a',)
    FieldPath('a').string_path = 'a'
    """

    def __init__(self, *names: str):
        self.levels: Tuple[str, ...] = tuple(names)
        self.string_path: str = ".".join(self.levels)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FieldPath):
            return False
        return other.levels == self.levels

    def __hash__(self) -> int:
        return hash(self.string_path)

    def __repr__(self) -> str:
        return f"FieldPath{self.levels}"

    def __lt__(self, other: "FieldPath") -> bool:
        return self.string_path < other.string_path

    def prepend(self, prefix: str) -> "FieldPath":
        """Return a new FieldPath with the prefix prepended."""
        return FieldPath(*((prefix,) + self.levels))

    @staticmethod
    def parse(path_str: str) -> FieldPath:
        """Create a FieldPath from a dot-separated input string"""
        return FieldPath(*path_str.split("."))


class FieldAddress:
    """The representation of a field location in the graph, specified by
    (data dataset name, collection name, field name, subfield name, ... )

    All values after the second are grouped to provide a FieldPath object.
    Additional values are understood to refer to nested field values.
    e.g. ("dataset", "collection", "a", "b", "c") creates a reference to
    dataset:collection:a.b.c
    """

    def __init__(self, dataset: str, collection: str, *fields: str):
        self.dataset = dataset
        self.collection = collection
        self.field_path: FieldPath = FieldPath(*fields)
        self.value: str = ":".join((dataset, collection, self.field_path.string_path))

    def is_member_of(self, collection_address: CollectionAddress) -> bool:
        """True if this field represents a field in the given collection address."""
        return (
            self.dataset == collection_address.dataset
            and self.collection == collection_address.collection
        )

    def collection_address(self) -> CollectionAddress:
        """Return the collection prefix of this field address."""
        return CollectionAddress(self.dataset, self.collection)

    @staticmethod
    def from_string(field_address_string: str) -> FieldAddress:
        """Creates a Field Address from a string - especially useful for instantiating
        Fields in Collections that are built from data in RequestTask.collection"""
        try:
            split_string = field_address_string.split(":")
            dataset = split_string[0]
            collection = split_string[1]
            fields = split_string[2]
            split_fields = fields.split(".")
            return FieldAddress(dataset, collection, *split_fields)
        except Exception:
            raise FidesopsException(
                f"'{field_address_string}' is not a valid field address"
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FieldAddress):
            return False
        return other.value == self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return self.value

    def __lt__(self, other: FieldAddress) -> bool:
        return self.value < other.value


class Field(BaseModel, ABC):
    """A single piece of data"""

    name: str
    primary_key: bool = False
    references: List[Tuple[FieldAddress, Optional[EdgeDirection]]] = []
    """references to other fields in any other datasets"""
    identity: Optional[SeedAddress] = None
    """an optional pointer to an arbitrary key in an expected json package provided as a seed value"""
    data_categories: Optional[List[FidesKey]] = None
    data_type_converter: DataTypeConverter = DataType.no_op.value
    return_all_elements: Optional[bool] = None
    masking_strategy_override: Optional[FieldMaskingStrategyOverride] = None
    # Should field be returned by query if it is in an entrypoint array field, or just if it matches query?
    custom_request_field: Optional[str] = None

    """Known type of held data"""
    length: Optional[int] = None
    """Known length of held data"""

    is_array: bool = False

    read_only: Optional[bool] = None
    """Optionally specify if a field is read-only, meaning it can't be updated or deleted. """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("data_type_converter")
    def serialize_data_type_converter(
        self, data_type_converter: DataTypeConverter
    ) -> Optional[str]:
        """Help Pydantic V2 serialize this unknown type"""
        return data_type_converter.name if data_type_converter.name else None

    @field_serializer("references")
    def serialize_references(
        self, references: List[Tuple[FieldAddress, Optional[EdgeDirection]]]
    ) -> List[Tuple[str, Optional[str]]]:
        """Help Pydantic V2 serialize this unknown type"""
        return [(ref[0].value, ref[1] if ref else None) for ref in references]

    @abstractmethod
    def cast(self, value: Any) -> Optional[Any]:
        """Cast the input value into the form represented by data_type."""

    def data_type(self) -> str:
        """return the data type name"""
        return self.data_type_converter.name

    @abstractmethod
    def collect_matching(self, func: Callable[[Field], bool]) -> Dict[FieldPath, Field]:
        """Find fields or subfields satisfying the input function"""

    def __repr__(self) -> str:
        """Overrides print method to be more succinct"""
        return f"{self.__class__.__name__}(name='{self.name}', data_type='{self.data_type()}', is_array={self.is_array})"


class ScalarField(Field):
    """A field that represents a simple value. Most fields will be scalar fields."""

    def cast(self, value: Any) -> Optional[Any]:
        """Cast the input value into the form represented by data_type.

        - If the data_type is None, then it has not been specified, so just return the input value.
        - Return either a cast value or None"""
        if not isinstance(value, QueryToken):
            return self.data_type_converter.to_value(value)

        return value

    def collect_matching(self, func: Callable[[Field], bool]) -> Dict[FieldPath, Field]:
        """Returns the field if it satisfies the input function"""
        if func(self):
            return {FieldPath(self.name): self}  # pylint: disable=no-member
        return {}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScalarField):
            return False

        return self.__dict__ == other.__dict__


class ObjectField(Field):
    """A field that represents a json dict structure."""

    fields: Dict[str, Field]

    def cast(self, value: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cast the input value into the form represented by data_type."""

        return {
            field.name: field.cast(value[field.name])  # pylint: disable=no-member
            for field in self.fields.values()
            if field.name in value
        }

    def collect_matching(self, func: Callable[[Field], bool]) -> Dict[FieldPath, Field]:
        """Find fields or subfields satisfying the input function

        Object fields will continue to call collect_matching until we get to the base case,
        which is a ScalarField.
        """
        base = (
            {FieldPath(self.name): self}  # pylint: disable=no-member
            if func(self)
            else {}
        )
        child_dicts = merge_dicts(
            *[field.collect_matching(func) for field in self.fields.values()]
        )
        return merge_dicts(
            base,  # type: ignore
            {
                field_path.prepend(self.name): field  # pylint: disable=no-member
                for field_path, field in child_dicts.items()
            },
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ObjectField):
            return False

        print(f"{self.__dict__=}")
        print(f"{other.__dict__=}")

        return self.__dict__ == other.__dict__


# pylint: disable=too-many-arguments
def generate_field(
    name: str,
    data_categories: Optional[List[FidesKey]],
    identity: Optional[str],
    data_type_name: str,
    references: List[Tuple[FieldAddress, Optional[EdgeDirection]]],
    is_pk: bool,
    length: Optional[int],
    is_array: bool,
    sub_fields: List[Field],
    return_all_elements: Optional[bool],
    read_only: Optional[bool],
    custom_request_field: Optional[str],
    masking_strategy_override: Optional[FieldMaskingStrategyOverride],
) -> Field:
    """Generate a graph field."""

    if sub_fields:
        return ObjectField(
            name=name,
            data_categories=data_categories,
            is_array=is_array,
            fields={f.name: f for f in sub_fields},
            data_type_converter=DataType.object.value,
            return_all_elements=return_all_elements,
        )
    return ScalarField(
        name=name,
        data_categories=data_categories,
        identity=identity,
        data_type_converter=get_data_type_converter(data_type_name),
        references=references,
        primary_key=is_pk,
        length=length,
        is_array=is_array,
        return_all_elements=return_all_elements,
        read_only=read_only,
        custom_request_field=custom_request_field,
        masking_strategy_override=masking_strategy_override,
    )


@dataclass
class MaskingTruncation:
    """Data class to store truncation params related to data masking"""

    data_type_converter: Optional[DataTypeConverter]
    length: Optional[int]


# for now, we only support BQ partitioning, so the clause pattern we expect is BQ-specific
BIGQUERY_PARTITION_CLAUSE_PATTERN = r"^`(?P<field_1>[a-zA-Z0-9_]*)` ([<|>][=]?) (?P<operand_1>[a-zA-Z0-9_\s(),\.\"\'\-]*)(\sAND `(?P<field_2>[a-zA-Z0-9_]*)` ([<|>][=]?) (?P<operand_2>[a-zA-Z0-9_\s(),\.\"\'\-]*))?$"
# protected keywords that are _not_ allowed in the operands, to avoid any potential malicious execution.
PROHIBITED_KEYWORDS = [
    "UNION",
    "INSERT",
    "UPDATE",
    "CREATE",
    "DROP",
    "SELECT",
    "CHAR",
    "HAVING",
    "EXEC",
]


class Collection(BaseModel):
    """A single grouping of individual data points that are accessed together"""

    name: str
    skip_processing: Optional[bool] = False
    fields: List[Field]
    # an optional list of collections that this collection must run after
    after: Set[CollectionAddress] = set()
    erase_after: Set[CollectionAddress] = set()
    # An optional set of dependent fields that need to be queried together
    grouped_inputs: Set[str] = set()
    data_categories: Set[FidesKey] = set()
    masking_strategy_override: Optional[MaskingStrategyOverride] = None
    partitioning: Optional[Union[List[TimeBasedPartitioning], Dict[str, Any]]] = None

    @property
    def field_dict(self) -> Dict[FieldPath, Field]:
        """Maps FieldPaths to Fields

        Flattens all the Fields so they are on one level: all nested fields are brought to the top.
        """
        return self.recursively_collect_matches(lambda f: True)

    @property
    def top_level_field_dict(self) -> Dict[FieldPath, Field]:
        """Returns a map of top-level FieldPaths mapped to fields"""
        return {FieldPath(field.name): field for field in self.fields}

    def recursively_collect_matches(
        self, func: Callable[[Field], bool]
    ) -> Dict[FieldPath, Field]:
        """Recurse through fields and subfields, creating a flattened dictionary
        of field paths mapped to fields where the function is satisfied"""
        matches = [field.collect_matching(func) for field in self.fields]
        return merge_dicts(*matches)

    def references(
        self,
    ) -> Dict[FieldPath, List[Tuple[FieldAddress, Optional[EdgeDirection]]]]:
        """return references from fields in this collection to fields in any other collection

        A nested field can be a reference.
        """
        return {
            field_path: field.references
            for field_path, field in self.field_dict.items()
            if field.references
        }

    def identities(self) -> Dict[FieldPath, str]:
        """return identity pointers included in the table"""
        return {
            field_path: field.identity  # type: ignore
            for field_path, field in self.field_dict.items()
            if field.identity
        }

    def custom_request_fields(self) -> Dict[FieldPath, str]:
        """
        Return custom request fields included in the table,
        i.e fields whose values may come in a custom request field on a DSR.

        E.g if the collection is defined like:
        - name: publishers
        - fields:
            - name: id
              fides_meta:
                identity: true
            - name: site_id
              fides_meta:
                custom_request_field: tenant_id

        Then this returns a dictionary of the form {FieldPath("site_id"): "tenant_id"}
        """
        return {
            field_path: field.custom_request_field
            for field_path, field in self.field_dict.items()
            if field.custom_request_field
        }

    def field(self, field_path: FieldPath) -> Optional[Field]:
        """Return Field (looked up by FieldPath) if on Collection or None if not found"""
        return self.field_dict[field_path] if field_path in self.field_dict else None

    @property
    def field_paths_by_category(self) -> Dict[FidesKey, List[FieldPath]]:
        """Returns mapping of data categories to a list of FieldPaths, flips FieldPaths -> categories
        to be categories -> FieldPaths.

        Example:
            {
                "user.contact.address.city": [FieldPath("city")],
                "user.contact.address.street": [FieldPath("house"), FieldPath("street")],
                "system.operations": ["id"],
                "user.contact.address.state": [FieldPath("state", "code"),FieldPath("state", "full_name"), ],
                "user.contact.address.postal_code": ["zip"]
            }
        """
        categories = defaultdict(list)
        for field_path, field in self.field_dict.items():
            for category in field.data_categories or []:
                categories[category].append(field_path)
        return categories

    def contains_field(self, func: Callable[[Field], bool]) -> bool:
        """True if any field in this collection matches the condition of the callable

        Currently used to assert at least one field in the collection contains a primary
        key before erasing
        """
        return any(self.recursively_collect_matches(func))

    @classmethod
    def parse_from_request_task(cls, data: Dict) -> Collection:
        """
        Take raw collection data saved on RequestTask.collection and converts it back into a Collection.

        See Config > json_encoders for some of the fields that needed special handling for serialization for
        database storage.
        """
        data = copy.deepcopy(data)

        def build_field(serialized_field: dict) -> Field:
            """Convert a serialized field on RequestTask.collection.fields into a Scalar Field
            or Object Field"""
            converted_references: List[Tuple[FieldAddress, Optional[EdgeDirection]]] = (
                []
            )
            for reference in serialized_field.pop("references", []):
                field_address: str = reference[0]
                edge_direction: Optional[str] = reference[1]
                converted_references.append(
                    (FieldAddress.from_string(field_address), edge_direction)  # type: ignore
                )

            data_type_converter: DataTypeConverter = get_data_type_converter(
                serialized_field.pop("data_type_converter")
            )

            # We can't convert the fields to abstract class Field - they need to be proper
            # Scalar or ObjectFields
            converted: Union[ObjectField, ScalarField]
            if serialized_field.get("fields"):
                # Recursively build nested fields under Object field
                serialized_field["fields"] = {
                    field_name: build_field(fld)
                    for field_name, fld in serialized_field["fields"].items()
                }
                converted = ObjectField.model_validate(serialized_field)
                converted.references = converted_references
                converted.data_type_converter = data_type_converter
                return converted

            converted = ScalarField.model_validate(serialized_field)
            converted.references = converted_references
            converted.data_type_converter = data_type_converter
            return converted

        converted_fields = []
        for field in data.pop("fields"):
            converted_fields.append(build_field(field))

        data["fields"] = converted_fields
        data["after"] = {
            CollectionAddress.from_string(addr_string)
            for addr_string in data.get("after", [])
        }
        data["erase_after"] = {
            CollectionAddress.from_string(addr_string)
            for addr_string in data.get("erase_after", [])
        }
        data["partitioning"] = data.get("partitioning")

        return Collection.model_validate(data)

    @field_serializer("data_type_converter", check_fields=False)
    def serialize_data_type_converter(
        self, data_type_converter: DataTypeConverter
    ) -> Optional[str]:
        """Help Pydantic V2 serialize this unknown type"""
        return data_type_converter.name if data_type_converter.name else None

    @field_serializer("after")
    def serialize_after(self, after: Set[CollectionAddress]) -> Set[str]:
        """Help Pydantic V2 serialize this unknown type"""
        return {aft.value for aft in after}

    @field_serializer("erase_after")
    def serialize_erase_after(self, erase_after: Set[CollectionAddress]) -> Set[str]:
        """Help Pydantic V2 serialize this unknown type"""
        return {aft.value for aft in erase_after}

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        # This supports running Collection.json() to serialize less standard
        # types so it can be saved to the database under RequestTask.collection
        json_encoders={
            Set: lambda val: list(  # pylint: disable=unhashable-member,unnecessary-lambda
                val
            ),
            DataTypeConverter: lambda dtc: dtc.name if dtc.name else None,
            FieldAddress: lambda fa: fa.value,
            CollectionAddress: lambda ca: ca.value,
        },
    )

    @field_validator("partitioning")
    @classmethod
    def validate_partitioning(
        cls, partitioning: Optional[Union[List[TimeBasedPartitioning], Dict[str, Any]]]
    ) -> Optional[Union[List[TimeBasedPartitioning], Dict[str, Any]]]:
        """
        Validates the `partitioning` field, which may be either a single dict
        or a list of dicts.  Each dict must describe either legacy
        `where_clauses` or the required keys for time-based partitioning.

        The string values are validated to ensure they match the expected syntax, which
        is strictly prescribed. The string values MUST be a valid SQL clause that defines
        a partition window, with the form:

        ```
        `column_1` >(=) [some value] AND `column_1` <(=) [some value]
        ```

        To be clear, some notable constraints on the input:
        - the clause string must begin by referencing a column name wrapped by backticks (`)
        - the clause string must compare that first column with a `<>(=)` operator, and may
        include at most one other conditional with a `<>(=)` operator that's joined to the first
        conditional via an AND operator
        - if the clause string contains a second conditional, it must reference the same column name
        as the first conditional, also wrapped by backticks
        - column names (wrapped by backticks) must always be on the _left_ side of the `<>(=)`operator
        in its conditional

        """

        if partitioning is None:
            return partitioning

        if isinstance(partitioning, list):
            validate_partitioning_list(partitioning)
            return partitioning

        # NOTE: when we deprecate `where_clause` partitioning in favor of a more proper partitioning DSL,
        # we should be sure to still support the existing `where_clause` partition definition on
        # any in-progress DSRs so that they can run through to completion.
        if where_clauses := partitioning.get("where_clauses"):
            if not isinstance(where_clauses, List) or not all(
                isinstance(where_clause, str) for where_clause in where_clauses
            ):
                raise ValueError("`where_clauses` must be a list of strings!")
            for partition_clause in where_clauses:
                if matching := match(
                    BIGQUERY_PARTITION_CLAUSE_PATTERN, partition_clause
                ):
                    # check that if there are two field comparison sub-clauses, they reference the same field, e.g.:
                    # "`my_field_1` > 5 AND `my_field_1` <= 10", not "`my_field_1` > 5 AND `my_field_1` <= 10"
                    if matching["field_2"] is not None and (
                        matching["field_1"] != matching["field_2"]
                    ):
                        raise ValueError(
                            f"Partition clause must have matching fields. Identified non-matching field references '{matching['field_1']}' and '{matching['field_2']}"
                        )

                    for prohibited_keyword in PROHIBITED_KEYWORDS:
                        search_str = prohibited_keyword.lower() + r"\s"
                        if search(search_str, partition_clause.lower()):
                            raise ValueError(
                                "Prohibited keyword referenced in partition clause"
                            )
                else:
                    raise ValueError("Unsupported partition clause format")
            return partitioning
        raise ValueError(
            "`where_clauses` must be specified in `partitioning` specification!"
        )


class GraphDataset(BaseModel):
    """Master collection of collections that are accessed in a common way"""

    name: str
    collections: List[Collection]
    # an optional list of datasets that this dataset must run after
    after: Set[DatasetAddress] = set()
    # ConnectionConfig key
    connection_key: FidesKey

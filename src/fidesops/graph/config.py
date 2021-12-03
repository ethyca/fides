"""
 These objects correspond to the structure of the configurations that will form nodes from dataset and collection
 representations.

  The language here is intended to be more general than SQL-specific language, since the intention here is to be able to
  reference many different kinds of data resources. If we think of a traditionql SQL database as composed of
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

  Note that this makes no statements about _how_ this data is to be retrieved. In particular many datastores will need special
  instructions (such as json paths) to extract data.


"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Tuple, Set, Dict, Literal, Any

from pydantic import BaseModel

from fidesops.common_exceptions import FidesopsException
from fidesops.graph.data_type import DataTypeConverter, DataType
from fidesops.util.querytoken import QueryToken
from fidesops.schemas.shared_schemas import FidesOpsKey

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

    def field_address(self, field: str) -> FieldAddress:
        """Create a field address appended to this collection address."""
        return FieldAddress(self.dataset, self.collection, field)


ROOT_COLLECTION_ADDRESS: CollectionAddress = CollectionAddress("__ROOT__", "__ROOT__")
"""Define a start traversal_node that all seed nodes begin from"""
TERMINATOR_ADDRESS = CollectionAddress("__TERMINATE__", "__TERMINATE__")
"""An address that corresponds to traversal termination"""


class FieldAddress:
    """The representation of a field location in the graph, specified by
    (data dataset name, collection name, field name)"""

    def __init__(self, dataset: str, collection: str, field: str):
        self.dataset = dataset
        self.collection = collection
        self.field = field
        self.value: str = ":".join((dataset, collection, field))

    def is_member_of(self, collection_address: CollectionAddress) -> bool:
        """True if this field represents a field in the given collection address."""
        return (
            self.dataset == collection_address.dataset
            and self.collection == collection_address.collection
        )

    def collection_address(self) -> CollectionAddress:
        """Return the collection prefix of this field address."""
        return CollectionAddress(self.dataset, self.collection)

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

    def display_name(self) -> str:
        """Displayable name"""
        if (
            self.dataset == ROOT_COLLECTION_ADDRESS.dataset
            and self.collection == ROOT_COLLECTION_ADDRESS.collection
        ):
            return f"identity:{self.field}"
        return self.__repr__()


class Field(BaseModel):
    """A single piece of data"""

    name: str
    primary_key: bool = False
    references: List[Tuple[FieldAddress, Optional[EdgeDirection]]] = []
    """references to other fields in any other datasets"""
    identity: Optional[SeedAddress] = None
    """an optional pointer to an arbitrary key in an expected json package provided as a seed value"""
    data_categories: Optional[List[FidesOpsKey]]
    """annotated data categories for the field used for policy actions"""
    data_type: Optional[DataType]
    """Known type of held data"""
    length: Optional[int]
    """Known length of held data"""

    class Config:
        """for pydantic incorporation of custom non-pydantic types"""

        arbitrary_types_allowed = True

    def cast(self, value: Any) -> Optional[Any]:
        """Cast the input value into the form represented by data_type.

        - If the data_type is None, then it has not been specified, so just return the input value.
        - Return either a cast value or None"""

        if self.data_type:
            # if no data type is specified just return the input value.
            # Skip conversions for query tokens, which are only for display output
            if not isinstance(value, QueryToken):
                converter: DataTypeConverter = self.data_type.value
                return converter.to_value(value)

        return value


@dataclass
class MaskingOverride:
    """Data class to store override params related to data masking"""

    data_type: Optional[DataType]
    length: Optional[int]


class Collection(BaseModel):
    """A single grouping of individual data points that are accessed together"""

    name: str
    fields: List[Field]
    # an optional list of collections that this collection must run after
    after: Set[CollectionAddress] = set()
    field_dict: Dict[str, Field] = {}

    def __init__(self, **kwargs: dict) -> None:
        super().__init__(**kwargs)
        self.field_dict = {f.name: f for f in self.fields}

    def references(
        self,
    ) -> Dict[str, List[Tuple[FieldAddress, Optional[EdgeDirection]]]]:
        """return references from fields in this collection to fields in any other"""
        flds_w_ref = filter(lambda f: f.references, self.fields)
        return {f.name: f.references for f in flds_w_ref}

    def identities(self) -> Dict[str, Tuple[str, ...]]:
        """return identity pointers included in the table"""
        flds_w_ident = filter(lambda f: f.identity, self.fields)
        return {f.name: f.identity for f in flds_w_ident}

    def field(self, name: str) -> Optional[Field]:
        """return field by name, or None if not found"""
        return self.field_dict[name] if name in self.field_dict else None

    @property
    def fields_by_category(self) -> Dict[str, List]:
        """Returns mapping of data categories to fields, flips fields -> categories
        to be categories -> fields.

        Example:
            {
                "user.provided.identifiable.contact.city": ["city"],
                "user.provided.identifiable.contact.street": ["house", "street"],
                "system.operations": ["id"],
                "user.provided.identifiable.contact.state": ["state"],
                "user.provided.identifiable.contact.postal_code": ["zip"]
            }
        """
        categories = defaultdict(list)
        for field in self.fields:
            for category in field.data_categories or []:
                categories[category].append(field.name)
        return categories

    class Config:
        """for pydantic incorporation of custom non-pydantic types"""

        arbitrary_types_allowed = True


class Dataset(BaseModel):
    """Master collection of collections that are accessed in a common way"""

    name: str
    collections: List[Collection]
    # an optional list of datasets that this dataset must run after
    after: Set[DatasetAddress] = set()
    # ConnectionConfig key
    connection_key: FidesOpsKey

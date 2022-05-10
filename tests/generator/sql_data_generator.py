import random
from typing import Dict, List, Any

from faker import Faker
from sqlalchemy import Column, String, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base

from fidesops.db.session import ENGINE
from fidesops.graph.config import (
    Collection,
    CollectionAddress,
    Field,
    FieldAddress,
    ScalarField,
)
from fidesops.graph.data_type import DataType
from fidesops.graph.graph import Edge, BidirectionalEdge, DatasetGraph
from fidesops.graph.traversal import Traversal, TraversalNode, Row
from tests.graph.graph_test_util import generate_graph_resources, field
from string import ascii_letters, digits

Base = declarative_base()

faker = Faker(use_weighting=False)

from faker.providers.lorem.en_US import Provider as lorem
from faker.providers import address

faker.add_provider(address)
faker.add_provider(lorem)


class DataGeneratorFunctions:

    faker = Faker(use_weighting=False)

    def name(cls):
        return cls.faker.name()

    def string(cls):
        return "".join(random.choices(ascii_letters, k=10))

    def integer(cls):
        return random.randint(0, 1000000)

    def street(cls):
        return cls.faker.street_address()

    def city(cls):
        return cls.faker.city()

    def zip(cls):
        return cls.faker.postcode()


def sqlalchemy_datatype(fides_data_type: DataType, **kwargs):
    return {
        DataType.string: Column(String(**kwargs)),
        DataType.integer: Column(Integer(**kwargs)),
        DataType.float: Column(Float(**kwargs)),
        DataType.boolean: Column(Boolean(**kwargs)),
        DataType.object_id: None,  # not a sqlalchemy supported type
    }[fides_data_type]


def create_sample_value(field: Field):
    def get_function_name(field) -> str:
        names = {
            s for s in DataGeneratorFunctions().__dir__() if not s.startswith("__")
        }
        if field.name in names:
            return field.name
        if (
            isinstance(field, ScalarField)
            and field.data_type_converter == DataType.integer.value
        ):
            return "integer"
        return "string"

    return getattr(DataGeneratorFunctions, get_function_name(field))(
        DataGeneratorFunctions
    )


def generate_data_for_traversal(
    traversal: Traversal, ct: int
) -> Dict[CollectionAddress, List[int]]:
    def generate_data(f: Field):
        return create_sample_value(f)

    def traversal_collection_fn(
        tn: TraversalNode, data: Dict[CollectionAddress, List[Row]]
    ) -> None:
        incoming_values = {}
        for edge in tn.incoming_edges():
            if edge.f1.collection_address() in data:
                collection_data = data[edge.f1.collection_address()]
                incoming_values[edge.f2.field_path] = (
                    edge.f1.field_path in collection_data
                    and collection_data[edge.f1.field_path]
                    or []
                )  # for row in collection_data]

        for fk, f in tn.node.collection.field_dict.items():
            name = fk.string_path
            if not name in incoming_values or len(incoming_values[name]) == 0:
                incoming_values[name] = [generate_data(f) for i in range(ct)]

        data[tn.address] = incoming_values

    env: Dict[CollectionAddress, List[int]] = {}
    traversal.traverse(env, traversal_collection_fn)
    return env

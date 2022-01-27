from typing import Optional, Tuple

from fidesops.graph.config import (
    Collection,
    ScalarField,
    FieldAddress,
    CollectionAddress,
    Dataset, ObjectField,
)
from fidesops.graph.data_type import DataType
from fidesops.graph.graph import DatasetGraph
from fidesops.graph.traversal import Traversal
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.schemas.shared_schemas import FidesOpsKey

str_converter = DataType.string.value
bool_converter = DataType.boolean.value
obj_converter = DataType.object.value
int_converter = DataType.integer.value


def integration_db_mongo_graph(
    db_name: str, connection_key: FidesOpsKey
) -> Tuple[Dataset, DatasetGraph]:
    dataset = integration_db_dataset(db_name, connection_key)
    for coll in dataset.collections:
        id_field = next(f for f in coll.fields if f.name == "id")
        id_field.primary_key = False
        coll.fields.append(
            ScalarField(
                name="_id",
                data_type_converter=DataType.object_id.value,
                primary_key=True,
            )
        )
    return dataset, DatasetGraph(dataset)


def combined_mongo_postgresql_graph(
    postgres_config: ConnectionConfig, mongo_config: ConnectionConfig
) -> Tuple[Dataset, Dataset]:
    postgres_dataset = integration_db_dataset("postgres_example", postgres_config.key)

    mongo_addresses = Collection(
        name="address",
        fields=[
            ScalarField(name="_id", primary_key=True),
            ScalarField(
                name="id",
                references=[
                    (FieldAddress("postgres_example", "customer", "address_id"), "from")
                ],
            ),
            ScalarField(name="street", data_type_converter=str_converter),
            ScalarField(name="city", data_type_converter=str_converter),
            ScalarField(name="state", data_type_converter=str_converter),
            ScalarField(name="zip", data_type_converter=str_converter),
        ],
    )
    mongo_orders = Collection(
        name="orders",
        fields=[
            ScalarField(name="_id", primary_key=True),
            ScalarField(
                name="customer_id",
                references=[
                    (FieldAddress("postgres_example", "customer", "id"), "from")
                ],
            ),
            ScalarField(
                name="payment_card_id",
                data_type_converter=str_converter,
            ),
        ],
    )

    mongo_customer_details = Collection(
        name="customer_details",
        fields=[
            ScalarField(name="_id", primary_key=True),
            ScalarField(
                name="customer_id",
                references=[
                    (FieldAddress("postgres_example", "customer", "id"), "from")
                ],
            ),
            ScalarField(name="gender", data_type_converter=str_converter),
            ScalarField(name="birthday", data_type_converter=str_converter),
            ObjectField(name="workplace_info", data_type_converter=obj_converter, fields={
                "employer": ScalarField(name="employer", data_type_converter=str_converter),
                "position": ScalarField(name="position", data_type_converter=str_converter)
            }),
        ]
    )

    mongo_customer_feedback = Collection(
        name="customer_feedback",
        fields=[
            ScalarField(name="_id", primary_key=True),
            ObjectField(name="customer_information", data_type_converter=obj_converter, fields={
                "email": ScalarField(name="email", data_type_converter=str_converter, identity="email"),
                "phone": ScalarField(name="phone", data_type_converter=str_converter),
                "internal_customer_id": ScalarField(name="internal_customer_id", data_type_converter=str_converter)
            }),
            ScalarField(name="rating", data_type_converter=int_converter),
            ScalarField(name="date", data_type_converter=str_converter),
            ScalarField(name="message", data_type_converter=str_converter),
        ]
    )

    mongo_internal_customer_profile = Collection(
        name="internal_customer_profile",
        fields=[
            ScalarField(name="_id", primary_key=True),
            ObjectField(name="customer_identifiers", data_type_converter=obj_converter, fields={
                "internal_id": ScalarField(name="internal_id", data_type_converter=str_converter, references=[
                    (FieldAddress("mongo_test", "customer_feedback", "customer_information", "internal_customer_id"), "from")
                ],),
            }),
            ScalarField(name="derived_interests", data_type_converter=str_converter),
    ]
    )

    mongo_dataset = Dataset(
        name="mongo_test",
        collections=[mongo_addresses, mongo_orders, mongo_customer_details, mongo_customer_feedback, mongo_internal_customer_profile],
        connection_key=mongo_config.key,
    )

    return mongo_dataset, postgres_dataset


def integration_db_dataset(db_name: str, connection_key: FidesOpsKey) -> Dataset:
    """A traversal that maps tables in the postgresql test database"""
    customers = Collection(
        name="customer",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(name="name", data_type_converter=str_converter),
            ScalarField(
                name="email", identity="email", data_type_converter=str_converter
            ),
            ScalarField(
                name="address_id",
                references=[(FieldAddress(db_name, "address", "id"), "to")],
            ),
        ],
    )
    addresses = Collection(
        name="address",
        after={
            CollectionAddress(db_name, "Customer"),
            CollectionAddress(db_name, "orders"),
        },
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(name="street", data_type_converter=str_converter),
            ScalarField(name="city", data_type_converter=str_converter),
            ScalarField(name="state", data_type_converter=str_converter),
            ScalarField(name="zip", data_type_converter=str_converter),
        ],
    )
    orders = Collection(
        name="orders",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(
                name="customer_id",
                references=[(FieldAddress(db_name, "customer", "id"), "from")],
            ),
            ScalarField(
                name="shipping_address_id",
                references=[(FieldAddress(db_name, "address", "id"), "to")],
            ),
            ScalarField(
                name="payment_card_id",
                references=[(FieldAddress(db_name, "payment_card", "id"), "to")],
                data_type_converter=str_converter,
            ),
        ],
    )
    payment_cards = Collection(
        name="payment_card",
        fields=[
            ScalarField(name="id", data_type_converter=str_converter, primary_key=True),
            ScalarField(name="name", data_type_converter=str_converter),
            ScalarField(name="ccn"),
            ScalarField(
                name="customer_id",
                references=[(FieldAddress(db_name, "customer", "id"), "from")],
            ),
            ScalarField(
                name="billing_address_id",
                references=[(FieldAddress(db_name, "address", "id"), "to")],
            ),
        ],
    )
    return Dataset(
        name=db_name,
        collections=[customers, addresses, orders, payment_cards],
        connection_key=connection_key,
    )


def integration_db_graph(
    db_name: str, connection_key: Optional[FidesOpsKey] = None
) -> DatasetGraph:
    """A traversal that maps tables in the postgresql test database"""
    if not connection_key:
        connection_key = db_name
    return DatasetGraph(integration_db_dataset(db_name, connection_key))


def sample_traversal() -> Traversal:
    """A traversal that covers multiple data sources, modelled after atlas multi-table
    examples"""
    customers = Collection(
        name="Customer",
        fields=[
            ScalarField(name="customer_id"),
            ScalarField(name="name"),
            ScalarField(name="email", identity="email"),
            ScalarField(
                name="contact_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to"),
                            (FieldAddress("mssql", "Address", "id"), "to")],
            ),
        ],
    )
    addresses = Collection(
        name="Address",
        after={
            CollectionAddress("mysql", "Customer"),
            CollectionAddress("postgres", "Order"),
        },
        fields=[
            ScalarField(name="id"),
            ScalarField(name="street"),
            ScalarField(name="city"),
            ScalarField(name="state"),
            ScalarField(name="zip"),
        ],
    )
    orders = Collection(
        name="Order",
        fields=[
            ScalarField(name="order_id"),
            ScalarField(
                name="customer_id",
                references=[(FieldAddress("mysql", "Customer", "customer_id"), "from")],
            ),
            ScalarField(
                name="shipping_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to")],
            ),
            ScalarField(
                name="billing_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to")],
            ),
        ],
    )
    users = Collection(
        name="User",
        fields=[
            ScalarField(name="id"),
            ScalarField(name="user_id", identity="user_id"),
            ScalarField(name="name"),
        ],
    )
    mysql = Dataset(
        name="mysql", collections=[customers, addresses, users], connection_key="mysql"
    )
    postgres = Dataset(name="postgres", collections=[orders], connection_key="postgres")
    mssql = Dataset(name="mssql", collections=[addresses], connection_key="mssql")

    graph = DatasetGraph(mysql, postgres, mssql)
    identity = {"email": "email@gmail.com", "user_id": "1"}
    return Traversal(graph, identity)

from typing import Optional, Tuple

from fidesops.graph.config import (
    Collection,
    Field,
    FieldAddress,
    CollectionAddress,
    Dataset,
)
from fidesops.graph.data_type import DataType
from fidesops.graph.graph import DatasetGraph
from fidesops.graph.traversal import Traversal
from fidesops.models.connectionconfig import ConnectionConfig


def integration_db_mongo_graph(
    db_name: str, connection_key: str
) -> Tuple[Dataset, DatasetGraph]:
    dataset = integration_db_dataset(db_name, connection_key)
    for coll in dataset.collections:
        id_field = next(f for f in coll.fields if f.name == "id")
        id_field.primary_key = False
        coll.fields.append(
            Field(name="_id", data_type=DataType.object_id, primary_key=True)
        )
    return dataset, DatasetGraph(dataset)


def combined_mongo_posgresql_graph(
    postgres_config: ConnectionConfig, mongo_config: ConnectionConfig
) -> Tuple[Dataset, Dataset]:
    postgres_dataset = integration_db_dataset("postgres_example", postgres_config.key)

    mongo_addresses = Collection(
        name="address",
        fields=[
            Field(name="_id", primary_key=True),
            Field(
                name="id",
                references=[
                    (FieldAddress("postgres_example", "customer", "address_id"), "from")
                ],
            ),
            Field(name="street", data_type=DataType.string),
            Field(name="city", data_type=DataType.string),
            Field(name="state", data_type=DataType.string),
            Field(name="zip", data_type=DataType.string),
        ],
    )
    mongo_orders = Collection(
        name="orders",
        fields=[
            Field(name="_id", primary_key=True),
            Field(
                name="customer_id",
                references=[
                    (FieldAddress("postgres_example", "customer", "id"), "from")
                ],
            ),
            Field(
                name="payment_card_id",
                data_type=DataType.string,
            ),
        ],
    )
    mongo_dataset = Dataset(
        name="mongo_test",
        collections=[mongo_addresses, mongo_orders],
        connection_key=mongo_config.key,
    )

    return mongo_dataset, postgres_dataset


def integration_db_dataset(db_name: str, connection_key: str) -> Dataset:
    """A traversal that maps tables in the postgresql test database"""
    customers = Collection(
        name="customer",
        fields=[
            Field(name="id", primary_key=True),
            Field(name="name", data_type=DataType.string),
            Field(name="email", identity="email", data_type=DataType.string),
            Field(
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
            Field(name="id", primary_key=True),
            Field(name="street", data_type=DataType.string),
            Field(name="city", data_type=DataType.string),
            Field(name="state", data_type=DataType.string),
            Field(name="zip", data_type=DataType.string),
        ],
    )
    orders = Collection(
        name="orders",
        fields=[
            Field(name="id", primary_key=True),
            Field(
                name="customer_id",
                references=[(FieldAddress(db_name, "customer", "id"), "from")],
            ),
            Field(
                name="shipping_address_id",
                references=[(FieldAddress(db_name, "address", "id"), "to")],
            ),
            Field(
                name="payment_card_id",
                references=[(FieldAddress(db_name, "payment_card", "id"), "to")],
                data_type=DataType.string,
            ),
        ],
    )
    payment_cards = Collection(
        name="payment_card",
        fields=[
            Field(name="id", data_type=DataType.string, primary_key=True),
            Field(name="name", data_type=DataType.string),
            Field(name="ccn"),
            Field(
                name="customer_id",
                references=[(FieldAddress(db_name, "customer", "id"), "from")],
            ),
            Field(
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
    db_name: str, connection_key: Optional[str] = None
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
            Field(name="customer_id"),
            Field(name="name"),
            Field(name="email", identity="email"),
            Field(
                name="contact_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to")],
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
            Field(name="id"),
            Field(name="street"),
            Field(name="city"),
            Field(name="state"),
            Field(name="zip"),
        ],
    )
    orders = Collection(
        name="Order",
        fields=[
            Field(name="order_id"),
            Field(
                name="customer_id",
                references=[(FieldAddress("mysql", "Customer", "customer_id"), "from")],
            ),
            Field(
                name="shipping_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to")],
            ),
            Field(
                name="billing_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to")],
            ),
        ],
    )
    users = Collection(
        name="User",
        fields=[
            Field(name="id"),
            Field(name="user_id", identity="user_id"),
            Field(name="name"),
        ],
    )
    mysql = Dataset(
        name="mysql", collections=[customers, addresses, users], connection_key="mysql"
    )
    postgres = Dataset(name="postgres", collections=[orders], connection_key="postgres")

    graph = DatasetGraph(mysql, postgres)
    identity = {"email": "email@gmail.com", "user_id": "1"}
    return Traversal(graph, identity)

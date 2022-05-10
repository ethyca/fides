from typing import Optional, Tuple

from fidesops.graph.config import (
    Collection,
    ScalarField,
    FieldAddress,
    CollectionAddress,
    Dataset,
    ObjectField,
)
from fidesops.graph.data_type import (
    DataType,
    IntTypeConverter,
    StringTypeConverter,
    ObjectIdTypeConverter,
    ObjectTypeConverter,
    NoOpTypeConverter,
)
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

    aircraft = Collection(
        name="aircraft",
        fields=[
            ScalarField(
                name="_id",
                data_type_converter=ObjectIdTypeConverter(),
                is_array=False,
                primary_key=True,
            ),
            ScalarField(
                name="model",
                data_type_converter=StringTypeConverter(),
                is_array=False,
            ),
            ScalarField(
                name="planes",
                data_type_converter=StringTypeConverter(),
                is_array=True,
                references=[(FieldAddress("mongo_test", "flights", "plane"), "from")],
            ),
        ],
        after=set(),
    )

    conversations = Collection(
        name="conversations",
        fields=[
            ScalarField(
                name="_id",
                data_type_converter=ObjectIdTypeConverter(),
                is_array=False,
                primary_key=True,
            ),
            ObjectField(
                name="thread",
                data_type_converter=ObjectTypeConverter(),
                is_array=False,
                fields={
                    "comment": ScalarField(
                        name="comment",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                    "message": ScalarField(
                        name="message",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                    "chat_name": ScalarField(
                        name="chat_name",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                    "ccn": ScalarField(
                        name="ccn",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                },
            ),
        ],
        after=set(),
    )

    customer_details = Collection(
        name="customer_details",
        fields=[
            ScalarField(
                name="_id",
                data_type_converter=NoOpTypeConverter(),
                is_array=False,
                primary_key=True,
            ),
            ScalarField(
                name="birthday",
                data_type_converter=StringTypeConverter(),
                is_array=False,
            ),
            ScalarField(
                name="children",
                data_type_converter=StringTypeConverter(),
                is_array=True,
            ),
            ObjectField(
                name="comments",
                data_type_converter=ObjectTypeConverter(),
                is_array=True,
                fields={
                    "name": ScalarField(
                        name="comment_id",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                        references=[
                            (
                                FieldAddress(
                                    "mongo_test", "conversations", "thread", "comment"
                                ),
                                "to",
                            )
                        ],
                    )
                },
            ),
            ScalarField(
                name="customer_id",
                data_type_converter=NoOpTypeConverter(),
                is_array=False,
                references=[
                    (
                        FieldAddress("postgres_example", "customer", "id"),
                        "from",
                    )
                ],
            ),
            ObjectField(
                name="emergency_contacts",
                data_type_converter=ObjectTypeConverter(),
                is_array=True,
                fields={
                    "name": ScalarField(
                        name="name",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                    "relationship": ScalarField(
                        name="relationship",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                    "phone": ScalarField(
                        name="phone",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                },
            ),
            ScalarField(
                name="gender",
                data_type_converter=StringTypeConverter(),
                is_array=False,
            ),
            ScalarField(
                name="travel_identifiers",
                data_type_converter=StringTypeConverter(),
                is_array=True,
            ),
            ObjectField(
                name="workplace_info",
                data_type_converter=ObjectTypeConverter(),
                is_array=False,
                fields={
                    "employer": ScalarField(
                        name="employer",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                    "position": ScalarField(
                        name="position",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                    "direct_reports": ScalarField(
                        name="direct_reports",
                        data_type_converter=StringTypeConverter(),
                        is_array=True,
                    ),
                },
            ),
        ],
        after=set(),
    )
    customer_feedback = Collection(
        name="customer_feedback",
        fields=[
            ScalarField(
                name="_id",
                data_type_converter=ObjectIdTypeConverter(),
                is_array=False,
                primary_key=True,
            ),
            ObjectField(
                name="customer_information",
                data_type_converter=ObjectTypeConverter(),
                is_array=False,
                fields={
                    "email": ScalarField(
                        name="email",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                        identity="email",
                    ),
                    "phone": ScalarField(
                        name="phone",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                    "internal_customer_id": ScalarField(
                        name="internal_customer_id",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                },
            ),
            ScalarField(
                name="date",
                data_type_converter=StringTypeConverter(),
                is_array=False,
            ),
            ScalarField(
                name="message",
                data_type_converter=StringTypeConverter(),
                is_array=False,
            ),
            ScalarField(
                name="rating",
                data_type_converter=IntTypeConverter(),
                is_array=False,
            ),
        ],
        after=set(),
    )
    employee = Collection(
        name="employee",
        fields=[
            ScalarField(
                name="_id",
                data_type_converter=ObjectIdTypeConverter(),
                is_array=False,
                primary_key=True,
            ),
            ScalarField(
                name="email",
                data_type_converter=StringTypeConverter(),
                is_array=False,
                identity="email",
            ),
            ScalarField(
                name="id",
                data_type_converter=NoOpTypeConverter(),
                is_array=False,
                references=[(FieldAddress("mongo_test", "flights", "pilots"), "from")],
                primary_key=True,
            ),
            ScalarField(
                name="name",
                data_type_converter=StringTypeConverter(),
                is_array=False,
            ),
        ],
        after=set(),
    )
    flights = Collection(
        name="flights",
        fields=[
            ScalarField(
                name="_id",
                data_type_converter=ObjectIdTypeConverter(),
                is_array=False,
                primary_key=True,
            ),
            ScalarField(
                name="date", data_type_converter=NoOpTypeConverter(), is_array=False
            ),
            ScalarField(
                name="flight_no",
                data_type_converter=NoOpTypeConverter(),
                is_array=False,
            ),
            ObjectField(
                name="passenger_information",
                data_type_converter=ObjectTypeConverter(),
                is_array=False,
                fields={
                    "passenger_ids": ScalarField(
                        name="passenger_ids",
                        data_type_converter=StringTypeConverter(),
                        is_array=True,
                        references=[
                            (
                                FieldAddress(
                                    "mongo_test",
                                    "customer_details",
                                    "travel_identifiers",
                                ),
                                "from",
                            )
                        ],
                    ),
                    "full_name": ScalarField(
                        name="full_name",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                    ),
                },
            ),
            ScalarField(
                name="pilots",
                data_type_converter=StringTypeConverter(),
                is_array=True,
            ),
            ScalarField(
                name="plane", data_type_converter=IntTypeConverter(), is_array=False
            ),
        ],
        after=set(),
    )
    internal_customer_profile = Collection(
        name="internal_customer_profile",
        fields=[
            ScalarField(
                name="_id",
                data_type_converter=ObjectIdTypeConverter(),
                is_array=False,
                primary_key=True,
            ),
            ObjectField(
                name="customer_identifiers",
                data_type_converter=ObjectTypeConverter(),
                is_array=False,
                fields={
                    "internal_id": ScalarField(
                        name="internal_id",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                        references=[
                            (
                                FieldAddress(
                                    "mongo_test",
                                    "customer_feedback",
                                    "customer_information",
                                    "internal_customer_id",
                                ),
                                "from",
                            )
                        ],
                    ),
                    "derived_emails": ScalarField(
                        name="derived_emails",
                        data_type_converter=StringTypeConverter(),
                        is_array=True,
                        identity="email",
                    ),
                    "derived_phone": ScalarField(
                        name="derived_phone",
                        data_type_converter=StringTypeConverter(),
                        is_array=True,
                        identity="phone_number",
                        return_all_elements=True,
                    ),
                },
            ),
            ScalarField(
                name="derived_interests",
                data_type_converter=StringTypeConverter(),
                is_array=True,
            ),
        ],
        after=set(),
    )
    rewards = Collection(
        name="rewards",
        fields=[
            ScalarField(
                name="_id",
                data_type_converter=ObjectIdTypeConverter(),
                is_array=False,
                primary_key=True,
            ),
            ObjectField(
                name="owner",
                data_type_converter=StringTypeConverter(),
                is_array=True,
                identity="email",
                return_all_elements=True,
                fields={
                    "phone": ScalarField(
                        return_all_elements=True,
                        name="phone",
                        data_type_converter=StringTypeConverter(),
                        is_array=False,
                        references=[
                            (
                                FieldAddress(
                                    "mongo_test",
                                    "internal_customer_profile",
                                    "customer_identifiers",
                                    "derived_phone",
                                ),
                                "from",
                            )
                        ],
                    ),
                    "shopper_name": ScalarField(
                        return_all_elements=True,
                        name="shopper_name",
                        data_type_converter=NoOpTypeConverter(),
                        is_array=False,
                    ),
                },
            ),
            ScalarField(
                name="points",
                data_type_converter=StringTypeConverter(),
                is_array=False,
            ),
            ScalarField(
                name="expiration_date",
                data_type_converter=NoOpTypeConverter(),
                is_array=False,
            ),
        ],
        after=set(),
    )

    mongo_dataset = Dataset(
        name="mongo_test",
        collections=[
            mongo_addresses,
            mongo_orders,
            aircraft,
            conversations,
            customer_details,
            customer_feedback,
            employee,
            flights,
            internal_customer_profile,
            rewards,
        ],
        connection_key=mongo_config.key,
    )

    return mongo_dataset, postgres_dataset


def integration_db_dataset(db_name: str, connection_key: FidesOpsKey) -> Dataset:
    """A traversal that maps tables in the postgresql test database"""
    customers = Collection(
        name="customer",
        fields=[
            ScalarField(name="id", primary_key=True, data_type_converter=int_converter),
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


def traversal_paired_dependency() -> Traversal:
    """Build a traversal that has grouped inputs"""
    projects = Collection(
        name="Project",
        fields=[
            ScalarField(name="project_id"),
            ScalarField(name="organization_id"),
            ScalarField(name="org_leader_email", identity="email"),
            ScalarField(name="project_name"),
        ],
    )
    users = Collection(
        name="User",
        after={
            CollectionAddress("mysql", "Project"),
        },
        fields=[
            ScalarField(
                name="project",
                references=[(FieldAddress("mysql", "Project", "project_id"), "from")],
            ),
            ScalarField(
                name="organization",
                references=[
                    (FieldAddress("mysql", "Project", "organization_id"), "from")
                ],
            ),
            ScalarField(name="username"),
            ScalarField(name="email", identity="email"),
            ScalarField(name="position"),
        ],
        grouped_inputs={"project", "organization", "email"},
    )

    mysql = Dataset(name="mysql", collections=[projects, users], connection_key="mysql")

    graph = DatasetGraph(mysql)
    identity = {"email": "email@gmail.com"}
    return Traversal(graph, identity)


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
                references=[
                    (FieldAddress("mysql", "Address", "id"), "to"),
                    (FieldAddress("mssql", "Address", "id"), "to"),
                ],
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

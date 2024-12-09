from typing import Any, Dict, Optional, Tuple

from fideslang.models import Dataset
from fideslang.validation import FidesKey

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    FieldAddress,
    GraphDataset,
    ScalarField,
)
from fides.api.graph.data_type import DataType
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import convert_dataset_to_graph

str_converter = DataType.string.value
bool_converter = DataType.boolean.value
obj_converter = DataType.object.value
int_converter = DataType.integer.value


def postgres_dataset_dict(db_name: str) -> Dict[str, Any]:
    """Returns a dictionary representing a sample Postgres dataset"""
    return {
        "fides_key": db_name,
        "name": db_name,
        "collections": [
            {
                "name": "customer",
                "fields": [
                    {
                        "name": "id",
                        "fides_meta": {"data_type": "integer"},
                    },
                    {"name": "name", "fides_meta": {"data_type": "string"}},
                    {
                        "name": "email",
                        "fides_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "address_id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "address.id",
                                    "direction": "to",
                                }
                            ]
                        },
                    },
                ],
            },
            {
                "name": "address",
                "after": [f"{db_name}.customer", f"{db_name}.orders"],
                "fields": [
                    {"name": "id"},
                    {"name": "street", "fides_meta": {"data_type": "string"}},
                    {"name": "city", "fides_meta": {"data_type": "string"}},
                    {"name": "state", "fides_meta": {"data_type": "string"}},
                    {"name": "zip", "fides_meta": {"data_type": "string"}},
                ],
            },
            {
                "name": "orders",
                "fields": [
                    {"name": "id"},
                    {
                        "name": "customer_id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "customer.id",
                                    "direction": "from",
                                }
                            ]
                        },
                    },
                    {
                        "name": "shipping_address_id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "address.id",
                                    "direction": "to",
                                }
                            ]
                        },
                    },
                    {
                        "name": "payment_card_id",
                        "fides_meta": {
                            "data_type": "string",
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "payment_card.id",
                                    "direction": "to",
                                }
                            ],
                        },
                    },
                ],
            },
            {
                "name": "payment_card",
                "fields": [
                    {
                        "name": "id",
                        "fides_meta": {"data_type": "string"},
                    },
                    {"name": "name", "fides_meta": {"data_type": "string"}},
                    {"name": "ccn"},
                    {
                        "name": "customer_id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "customer.id",
                                    "direction": "from",
                                }
                            ]
                        },
                    },
                    {
                        "name": "billing_address_id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "address.id",
                                    "direction": "to",
                                }
                            ]
                        },
                    },
                ],
            },
        ],
    }


def mongo_dataset_dict(mongo_db_name: str, postgres_db_name: str) -> GraphDataset:
    """Returns a dictionary representing a sample MongoDB dataset"""
    return {
        "fides_key": mongo_db_name,
        "name": mongo_db_name,
        "collections": [
            {
                "name": "address",
                "fields": [
                    {"name": "_id"},
                    {
                        "name": "id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": postgres_db_name,
                                    "field": "customer.address_id",
                                    "direction": "from",
                                }
                            ]
                        },
                    },
                    {"name": "street", "fides_meta": {"data_type": "string"}},
                    {"name": "city", "fides_meta": {"data_type": "string"}},
                    {"name": "state", "fides_meta": {"data_type": "string"}},
                    {"name": "zip", "fides_meta": {"data_type": "string"}},
                ],
            },
            {
                "name": "orders",
                "fields": [
                    {"name": "_id"},
                    {
                        "name": "customer_id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": postgres_db_name,
                                    "field": "customer.id",
                                    "direction": "from",
                                }
                            ]
                        },
                    },
                    {"name": "payment_card_id", "fides_meta": {"data_type": "string"}},
                ],
            },
            {
                "name": "aircraft",
                "fields": [
                    {
                        "name": "_id",
                        "fides_meta": {
                            "data_type": "object_id",
                        },
                    },
                    {
                        "name": "model",
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "planes",
                        "fides_meta": {
                            "data_type": "string[]",
                            "references": [
                                {
                                    "dataset": mongo_db_name,
                                    "field": "flights.plane",
                                    "direction": "from",
                                }
                            ],
                        },
                    },
                ],
            },
            {
                "name": "conversations",
                "fields": [
                    {
                        "name": "_id",
                        "fides_meta": {
                            "data_type": "object_id",
                        },
                    },
                    {
                        "name": "thread",
                        "fides_meta": {"data_type": "object"},
                        "fields": [
                            {
                                "name": "comment",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                            {
                                "name": "message",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                            {
                                "name": "chat_name",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                            {
                                "name": "ccn",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                        ],
                    },
                ],
            },
            {
                "name": "customer_details",
                "fields": [
                    {
                        "name": "_id",
                    },
                    {
                        "name": "birthday",
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "children",
                        "fides_meta": {"data_type": "string[]"},
                    },
                    {
                        "name": "comments",
                        "fides_meta": {"data_type": "object[]"},
                        "fields": [
                            {
                                "name": "comment_id",
                                "fides_meta": {
                                    "data_type": "string",
                                    "references": [
                                        {
                                            "dataset": mongo_db_name,
                                            "field": "conversations.thread.comment",
                                            "direction": "to",
                                        }
                                    ],
                                },
                            }
                        ],
                    },
                    {
                        "name": "customer_id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": "postgres_example",
                                    "field": "customer.id",
                                    "direction": "from",
                                }
                            ],
                        },
                    },
                    {
                        "name": "emergency_contacts",
                        "fides_meta": {"data_type": "object[]"},
                        "fields": [
                            {
                                "name": "name",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                            {
                                "name": "relationship",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                            {
                                "name": "phone",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                        ],
                    },
                    {
                        "name": "gender",
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "travel_identifiers",
                        "fides_meta": {"data_type": "string[]"},
                    },
                    {
                        "name": "workplace_info",
                        "fides_meta": {"data_type": "object"},
                        "fields": [
                            {
                                "name": "employer",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                            {
                                "name": "position",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                            {
                                "name": "direct_reports",
                                "fides_meta": {"data_type": "string[]"},
                            },
                        ],
                    },
                ],
            },
            {
                "name": "customer_feedback",
                "fields": [
                    {
                        "name": "_id",
                        "fides_meta": {
                            "data_type": "object_id",
                        },
                    },
                    {
                        "name": "customer_information",
                        "fides_meta": {"data_type": "object"},
                        "fields": [
                            {
                                "name": "email",
                                "fides_meta": {
                                    "data_type": "string"
                                    "identity": "email",
                                },
                            },
                            {
                                "name": "phone",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                            {
                                "name": "internal_customer_id",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                        ],
                    },
                    {
                        "name": "date",
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "message",
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "rating",
                        "fides_meta": {"data_type": "integer"},
                    },
                ],
            },
            {
                "name": "employee",
                "fields": [
                    {
                        "name": "_id",
                        "fides_meta": {
                            "data_type": "object_id",
                        },
                    },
                    {
                        "name": "email",
                        "fides_meta": {
                            "data_type": "string",
                            "identity": "email",
                        },
                    },
                    {
                        "name": "id",
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": mongo_db_name,
                                    "field": "flights.pilots",
                                    "direction": "from",
                                }
                            ],
                        },
                    },
                    {
                        "name": "name",
                        "fides_meta": {"data_type": "string"},
                    },
                ],
            },
            {
                "name": "flights",
                "fields": [
                    {
                        "name": "_id",
                        "fides_meta": {"data_type": "object_id"},
                    },
                    {
                        "name": "date",
                    },
                    {
                        "name": "flight_no",
                    },
                    {
                        "name": "passenger_information",
                        "fides_meta": {"data_type": "object"},
                        "fields": [
                            {
                                "name": "passenger_ids",
                                "fides_meta": {
                                    "data_type": "string[]",
                                    "references": [
                                        {
                                            "dataset": "mongo_test",
                                            "field": "customer_details.travel_identifiers",
                                            "direction": "from",
                                        }
                                    ],
                                },
                            },
                            {
                                "name": "full_name",
                                "fides_meta": {
                                    "data_type": "string"
                                },
                            },
                        ],
                    },
                    {
                        "name": "pilots",
                        "fides_meta": {"data_type": "string[]"},
                    },
                    {
                        "name": "plane",
                        "fides_meta": {"data_type": "integer"},
                    },
                ],
            },
            {
                "name": "internal_customer_profile",
                "fields": [
                    {
                        "name": "_id",
                        "fides_meta": {"data_type": "object_id"},
                    },
                    {
                        "name": "customer_identifiers",
                        "fides_meta": {"data_type": "object"},
                        "fields": [
                            {
                                "name": "internal_id",
                                "fides_meta": {
                                    "data_type": "string",
                                    "references": [
                                        {
                                            "dataset": mongo_db_name,
                                            "field": "customer_feedback.customer_information.internal_customer_id",
                                            "direction": "from",
                                        }
                                    ],
                                },
                            },
                            {
                                "name": "derived_emails",
                                "fides_meta": {
                                    "data_type": "string[]",
                                    "identity": "email",
                                },
                            },
                            {
                                "name": "derived_phone",
                                "fides_meta": {
                                    "data_type": "string[]",
                                    "identity": "phone_number",
                                    "return_all_elements": True,
                                },
                            },
                        ],
                    },
                    {
                        "name": "derived_interests",
                        "fides_meta": {"data_type": "string[]"},
                    },
                ],
            },
            {
                "name": "rewards",
                "fields": [
                    {
                        "name": "_id",
                        "fides_meta": {"data_type": "object_id"},
                    },
                    {
                        "name": "owner",
                        "fides_meta": {
                            "data_type": "object[]",
                            "identity": "email",
                            "return_all_elements": True,
                        },
                        "fields": [
                            {
                                "name": "phone",
                                "fides_meta": {
                                    "data_type": "string[]",
                                    "references": [
                                        {
                                            "dataset": mongo_db_name,
                                            "field": "internal_customer_profile.customer_identifiers.derived_phone",
                                            "direction": "from",
                                        }
                                    ],
                                },
                            },
                            {"name": "shopper_name"},
                        ],
                    },
                    {
                        "name": "points",
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "expiration_date",
                    },
                ],
            },
        ],
    }


def scylladb_dataset_dict(db_name: str) -> Dict[str, Any]:
    return {
        "fides_key": db_name,
        "data_categories": [],
        "description": "ScyllaDB dataset containing a users table and user_activity table.",
        "name": db_name,
        "collections": [
            {
                "name": "users",
                "fields": [
                    {
                        "name": "age",
                        "data_categories": ["user.demographic.age_range"],
                        "fides_meta": {"data_type": "integer"},
                    },
                    {
                        "name": "alternative_contacts",
                        "data_categories": ["user.contact.email"],
                    },
                    {"name": "ascii_data", "data_categories": ["system"]},
                    {"name": "big_int_data", "data_categories": ["system"]},
                    {"name": "do_not_contact", "data_categories": ["user.contact"]},
                    {
                        "name": "double_data",
                        "data_categories": ["user.location.imprecise"],
                    },
                    {"name": "duration", "data_categories": ["system"]},
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fides_meta": {"identity": "email", "data_type": "string"},
                    },
                    {
                        "name": "float_data",
                        "data_categories": ["user.location.imprecise"],
                        "fides_meta": {"data_type": "float"},
                    },
                    {"name": "last_contacted", "data_categories": ["user.contact.url"]},
                    {
                        "name": "logins",
                        "data_categories": ["system"],
                    },
                    {
                        "name": "name",
                        "data_categories": ["user.name"],
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "states_lived",
                        "data_categories": ["user.contact.address"],
                    },
                    {"name": "timestamp", "data_categories": ["system"]},
                    {
                        "name": "user_id",
                        "data_categories": ["user.unique_id"],
                        "fides_meta": {"data_type": "integer"},
                    },
                    {"name": "uuid", "data_categories": ["user.government_id"]},
                ],
            },
            {
                "name": "user_activity",
                "fields": [
                    {
                        "name": "user_id",
                        "data_categories": ["user.unique_id"],
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "users.user_id",
                                    "direction": "from",
                                }
                            ],
                            "data_type": "integer",
                        },
                    },
                    {
                        "name": "timestamp",
                        "data_categories": ["user.behavior"],
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "user_agent",
                        "data_categories": ["user.device"],
                        "fides_meta": {"data_type": "string"},
                    },
                    {
                        "name": "activity_type",
                        "data_categories": ["user.behavior"],
                        "fides_meta": {"data_type": "string"},
                    },
                ],
            },
            {
                "name": "payment_methods",
                "fields": [
                    {
                        "name": "payment_method_id",
                        "data_categories": ["system.operations"],
                        "fides_meta": {"data_type": "integer"},
                    },
                    {
                        "name": "user_id",
                        "data_categories": ["user.unique_id"],
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "users.user_id",
                                    "direction": "from",
                                }
                            ],
                            "data_type": "integer",
                        },
                    },
                    {
                        "name": "card_number",
                        "data_categories": ["user.payment"],
                        "fides_meta": {"data_type": "integer"},
                    },
                    {"name": "expiration_date", "data_categories": ["user.payment"]},
                ],
            },
            {
                "name": "orders",
                "fields": [
                    {
                        "name": "order_id",
                        "data_categories": ["system.operations"],
                        "fides_meta": {"data_type": "integer"},
                    },
                    {
                        "name": "payment_method_id",
                        "data_categories": ["system.operations"],
                        "fides_meta": {
                            "data_type": "integer",
                            "references": [
                                {
                                    "dataset": db_name,
                                    "field": "payment_methods.payment_method_id",
                                    "direction": "from",
                                }
                            ],
                        },
                    },
                    {
                        "name": "order_amount",
                        "data_categories": ["user.behavior.purchase_history"],
                        "fides_meta": {"data_type": "integer"},
                    },
                    {
                        "name": "order_date",
                        "data_categories": ["user.behavior.purchase_history"],
                    },
                    {
                        "name": "order_description",
                        "data_categories": ["user.behavior.purchase_history"],
                        "fides_meta": {"data_type": "string"},
                    },
                ],
            },
        ],
    }


def postgres_db_graph_dataset(db_name: str, connection_key) -> GraphDataset:
    dataset = postgres_dataset_dict(db_name)
    return convert_dataset_to_graph(Dataset.model_validate(dataset), connection_key)


def scylla_db_graph_dataset(db_name: str) -> GraphDataset:
    dataset = scylladb_dataset_dict(db_name)
    return convert_dataset_to_graph(Dataset.model_validate(dataset), db_name)


def mongo_db_graph_dataset(
    mongo_db_name: str, postgres_db_name: str, connection_key: str
) -> GraphDataset:
    dataset = mongo_dataset_dict(mongo_db_name, postgres_db_name)
    return convert_dataset_to_graph(Dataset.model_validate(dataset), connection_key)


def integration_db_mongo_graph(
    db_name: str, connection_key: FidesKey
) -> Tuple[GraphDataset, DatasetGraph]:
    dataset = postgres_db_graph_dataset(db_name, connection_key)
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


def integration_scylladb_graph(db_name: str) -> DatasetGraph:
    dataset = scylla_db_graph_dataset(db_name)
    return DatasetGraph(dataset)


def combined_mongo_postgresql_graph(
    postgres_config: ConnectionConfig, mongo_config: ConnectionConfig
) -> Tuple[GraphDataset, GraphDataset]:
    postgres_dataset = postgres_db_graph_dataset(
        "postgres_example", postgres_config.key
    )
    mongo_dataset = mongo_db_graph_dataset(
        "mongo_test", "postgres_example", mongo_config.key
    )
    return mongo_dataset, postgres_dataset


def manual_graph_dataset(db_name: str, postgres_db_name) -> GraphDataset:
    """Manual GraphDataset depending on upstream postgres collection and pointing to a node in a downstream
    postgres collection"""
    filing_cabinet = Collection(
        name="filing_cabinet",
        fields=[
            ScalarField(name="id", primary_key=True, data_type_converter=int_converter),
            ScalarField(
                name="authorized_user",
                data_type_converter=str_converter,
                data_categories=["user"],
            ),
            ScalarField(
                name="customer_id",
                references=[(FieldAddress(postgres_db_name, "customer", "id"), "from")],
            ),
            ScalarField(
                name="payment_card_id",
                references=[
                    (FieldAddress(postgres_db_name, "payment_card", "id"), "to")
                ],
            ),
        ],
    )
    storage_unit = Collection(
        name="storage_unit",
        fields=[
            ScalarField(
                name="box_id", primary_key=True, data_type_converter=int_converter
            ),
            ScalarField(
                name="email",
                identity="email",
                data_type_converter=str_converter,
                data_categories=["user"],
            ),
        ],
    )
    return GraphDataset(
        name=db_name,
        collections=[filing_cabinet, storage_unit],
        connection_key=db_name,
    )


def postgres_and_manual_nodes(postgres_db_name: str, manual_db_name: str):
    postgres_db = postgres_db_graph_dataset(postgres_db_name, postgres_db_name)
    manual_db = manual_graph_dataset(manual_db_name, postgres_db_name)
    return DatasetGraph(postgres_db, manual_db)


def integration_db_graph(
    db_name: str, connection_key: Optional[FidesKey] = None
) -> DatasetGraph:
    """A traversal that maps tables in the postgresql test database"""
    if not connection_key:
        connection_key = db_name
    return DatasetGraph(postgres_db_graph_dataset(db_name, connection_key))


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

    mysql = GraphDataset(
        name="mysql", collections=[projects, users], connection_key="mysql"
    )

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
    mysql = GraphDataset(
        name="mysql", collections=[customers, addresses, users], connection_key="mysql"
    )
    postgres = GraphDataset(
        name="postgres", collections=[orders], connection_key="postgres"
    )
    mssql = GraphDataset(name="mssql", collections=[addresses], connection_key="mssql")

    graph = DatasetGraph(mysql, postgres, mssql)
    identity = {"email": "email@gmail.com", "user_id": "1"}
    return Traversal(graph, identity)

import pytest

import dask
from bson import ObjectId

from fidesops.graph.config import (
    CollectionAddress,
)
from fidesops.graph.graph import DatasetGraph
from fidesops.graph.traversal import Traversal
from fidesops.models.connectionconfig import ConnectionConfig, ConnectionType
from fidesops.models.policy import Policy
from fidesops.task.graph_task import (
    collect_queries,
    TaskResources,
    EMPTY_REQUEST,
)
from .traversal_data import sample_traversal, combined_mongo_postgresql_graph
from ..graph.graph_test_util import (
    MockSqlTask,
    MockMongoTask,
)

dask.config.set(scheduler="processes")

connection_configs = [
    ConnectionConfig(key="mysql", connection_type=ConnectionType.postgres),
    ConnectionConfig(key="postgres", connection_type=ConnectionType.postgres),
    ConnectionConfig(key="mssql", connection_type=ConnectionType.mssql),
]


class TestToDaskInput:
    @pytest.fixture(scope="function")
    def combined_traversal_node_dict(
        self, integration_mongodb_config, integration_postgres_config
    ):
        mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
            integration_postgres_config, integration_mongodb_config
        )
        graph = DatasetGraph(mongo_dataset, postgres_dataset)
        identity = {"email": "customer-1@example.com"}
        combined_traversal = Traversal(graph, identity)
        return combined_traversal.traversal_node_dict

    @pytest.fixture(scope="function")
    def make_graph_task(self, integration_mongodb_config, integration_postgres_config):
        def task(node):
            return MockMongoTask(
                node,
                TaskResources(
                    EMPTY_REQUEST,
                    Policy(),
                    [integration_postgres_config, integration_mongodb_config],
                ),
            )

        return task

    def test_to_dask_input_data_scalar(self) -> None:
        t = sample_traversal()
        n = t.traversal_node_dict[CollectionAddress("mysql", "Address")]

        task = MockSqlTask(
            n, TaskResources(EMPTY_REQUEST, Policy(), connection_configs)
        )
        customers_data = [
            {"contact_address_id": 31, "foo": "X"},
            {"contact_address_id": 32, "foo": "Y"},
        ]
        orders_data = [
            {"billing_address_id": 1, "shipping_address_id": 2},
            {"billing_address_id": 11, "shipping_address_id": 22},
        ]
        v = task.to_dask_input_data(customers_data, orders_data)
        assert set(v["id"]) == {31, 32, 1, 2, 11, 22}

    def test_to_dask_input_nested_identity(
        self, combined_traversal_node_dict, make_graph_task
    ):
        """
        Identity data used to locate record on nested email

        Customer feedback node has one input:
        ROOT.email -> customer_feedback.customer_information.email
        """
        node = combined_traversal_node_dict[
            CollectionAddress("mongo_test", "customer_feedback")
        ]
        root_email_input = [{"email": "customer-1@example.com"}]
        assert make_graph_task(node).to_dask_input_data(root_email_input) == {
            "customer_information.email": ["customer-1@example.com"],
        }

    def test_to_dask_input_customer_feedback_collection(
        self, combined_traversal_node_dict, make_graph_task
    ):
        """
        Nested internal_customer_id used to locate record matching nested internal_id

        Internal customer profile node has two inputs:
        ROOT.email -> internal_customer_profile.derived_emails(string[])
        customer_feedback.customer_information.internal_customer_id -> internal_customer_profile.customer_identifiers.internal_id
        """
        node = combined_traversal_node_dict[
            CollectionAddress("mongo_test", "internal_customer_profile")
        ]
        internal_customer_profile_task = make_graph_task(node)
        root_email_input = [{"email": "customer-1@example.com"}]
        customer_feedback_input = [
            {
                "_id": ObjectId("61eb388ecfb4a3721238a39b"),
                "customer_information": {
                    "email": "customer-1@example.com",
                    "phone": "333-333-3333",
                    "internal_customer_id": "cust_001",
                },
            }
        ]

        assert internal_customer_profile_task.to_dask_input_data(
            root_email_input, customer_feedback_input
        ) == {
            "customer_identifiers.derived_emails": ["customer-1@example.com"],
            "customer_identifiers.internal_id": ["cust_001"],
        }

    def test_to_dask_input_flights_collection(
        self, make_graph_task, combined_traversal_node_dict
    ):
        """
        Array of strings used to locate record with matching value in nested array of strings

        Flights node has one input:
        mongo_test.customer_details.travel_identifiers -> mongo_test.passenger_information.passenger_ids
        """
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "flights")]
        task = make_graph_task(node)
        truncated_customer_details_output = [
            {
                "_id": ObjectId("61f422e0ddc2559e0c300e95"),
                "travel_identifiers": ["A111-11111", "B111-11111"],
            },
            {
                "_id": ObjectId("61f422e0ddc2559e0c300e95"),
                "travel_identifiers": ["C111-11111"],
            },
        ]
        assert task.to_dask_input_data(truncated_customer_details_output) == {
            "passenger_information.passenger_ids": [
                "A111-11111",
                "B111-11111",
                "C111-11111",
            ],
        }

    def test_to_dask_input_aircraft_collection(
        self, make_graph_task, combined_traversal_node_dict
    ):
        """
        Integer used to locate record with matching value in array of integers

        Aircraft node has one input:
        mongo_test:flights.plane -> mongo_test:aircraft.planes
        """
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "aircraft")]
        task = make_graph_task(node)
        truncated_flights_output = [
            {"pilots": ["1", "2"], "plane": 10002.0},
            {"pilots": ["3", "4"], "plane": 101010},
        ]
        assert task.to_dask_input_data(truncated_flights_output) == {
            "planes": [10002, 101010],
        }

    def test_to_dask_input_employee_collection(
        self, make_graph_task, combined_traversal_node_dict
    ):
        """
        Array of integers used to locate record with matching integer

        Mongo employee node has two inputs:
        root.email -> mongo_test.employee.email
        mongo_test.flights.pilots -> mongo_test.employee.id
        """
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "employee")]
        task = make_graph_task(node)
        root_email_input = [{"email": "customer-1@example.com"}]
        truncated_flights_output = [
            {"pilots": ["1", "2"], "plane": 10002.0},
            {"pilots": ["3", "4"], "plane": 101010},
        ]
        assert task.to_dask_input_data(root_email_input, truncated_flights_output) == {
            "id": ["1", "2", "3", "4"],
            "email": ["customer-1@example.com"],
        }

    def test_to_dask_input_conversation_collection(
        self, make_graph_task, combined_traversal_node_dict
    ):
        """
        Array of objects of strings used to locate record within array of objects of scalars

        Mongo conversation node has one input:
        mongo_test:customer_details.comments.comment_id -> mongo_test:conversations.thread.comment
        """
        node = combined_traversal_node_dict[
            CollectionAddress("mongo_test", "conversations")
        ]
        task = make_graph_task(node)
        truncated_customer_details_output = [
            {
                "comments": [
                    {"comment_id": "com_0001"},
                    {"comment_id": "com_0003"},
                    {"comment_id": "com_0005"},
                ]
            },
            {"comments": [{"comment_id": "com_0007"}]},
        ]

        assert task.to_dask_input_data(truncated_customer_details_output) == {
            "thread.comment": ["com_0001", "com_0003", "com_0005", "com_0007"],
        }


def test_sql_dry_run_queries() -> None:
    traversal = sample_traversal()
    env = collect_queries(
        traversal,
        TaskResources(EMPTY_REQUEST, Policy(), connection_configs),
    )

    assert (
        env[CollectionAddress("mysql", "Customer")]
        == "SELECT customer_id,name,email,contact_address_id FROM Customer WHERE email = ?"
    )

    assert (
        env[CollectionAddress("mysql", "User")]
        == "SELECT id,user_id,name FROM User WHERE user_id = ?"
    )

    assert (
        env[CollectionAddress("postgres", "Order")]
        == "SELECT order_id,customer_id,shipping_address_id,billing_address_id FROM Order WHERE customer_id IN (?, ?)"
    )

    assert (
        env[CollectionAddress("mysql", "Address")]
        == "SELECT id,street,city,state,zip FROM Address WHERE id IN (?, ?)"
    )

    assert (
        env[CollectionAddress("mssql", "Address")]
        == "SELECT id,street,city,state,zip FROM Address WHERE id IN (:id_in_stmt_generated_0, :id_in_stmt_generated_1)"
    )


def test_mongo_dry_run_queries() -> None:
    from .traversal_data import integration_db_graph

    traversal = Traversal(integration_db_graph("postgres"), {"email": ["x"]})
    env = collect_queries(
        traversal,
        TaskResources(
            EMPTY_REQUEST,
            Policy(),
            [
                ConnectionConfig(key="mysql", connection_type=ConnectionType.mongodb),
                ConnectionConfig(
                    key="postgres", connection_type=ConnectionType.mongodb
                ),
            ],
        ),
    )

    assert (
        env[CollectionAddress("postgres", "customer")]
        == "db.postgres.customer.find({'email': ?}, {'id': 1, 'name': 1, 'email': 1, 'address_id': 1})"
    )

    assert (
        env[CollectionAddress("postgres", "orders")]
        == "db.postgres.orders.find({'customer_id': {'$in': [?, ?]}}, {'id': 1, 'customer_id': 1, 'shipping_address_id': 1, 'payment_card_id': 1})"
    )

    assert (
        env[CollectionAddress("postgres", "address")]
        == "db.postgres.address.find({'id': {'$in': [?, ?]}}, {'id': 1, 'street': 1, 'city': 1, 'state': 1, 'zip': 1})"
    )

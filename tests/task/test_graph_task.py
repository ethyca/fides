import dask

from fidesops.graph.config import (
    CollectionAddress,
)
from fidesops.graph.traversal import Traversal
from fidesops.models.connectionconfig import ConnectionConfig, ConnectionType
from fidesops.models.policy import Policy
from fidesops.task.graph_task import collect_queries, TaskResources, EMPTY_REQUEST
from .traversal_data import sample_traversal
from ..graph.graph_test_util import (
    MockSqlTask,
)

dask.config.set(scheduler="processes")

connection_configs = [
    ConnectionConfig(key="mysql", connection_type=ConnectionType.postgres),
    ConnectionConfig(key="postgres", connection_type=ConnectionType.postgres),
    ConnectionConfig(key="mssql", connection_type=ConnectionType.mssql)
]


def test_to_dask_input_data() -> None:
    t = sample_traversal()
    n = t.traversal_node_dict[CollectionAddress("mysql", "Address")]

    task = MockSqlTask(n, TaskResources(EMPTY_REQUEST, Policy(), connection_configs))
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

from typing import Dict, Any, Set

from fidesops.graph.config import CollectionAddress
from fidesops.graph.graph import DatasetGraph
from fidesops.graph.traversal import Traversal, TraversalNode
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.service.connectors import PostgreSQLConnector
from fidesops.service.connectors.query_config import QueryConfig, SQLQueryConfig
from ...task.traversal_data import integration_db_graph


# customers -> address, order
# orders -> address, payment card
# payment card -> address
# address

# identities: customer.email

graph: DatasetGraph = integration_db_graph("postgres_example")
traversal = Traversal(graph, {"email": "X"})
traversal_nodes: Dict[CollectionAddress, TraversalNode] = traversal.traversal_node_dict
payment_card_node = traversal_nodes[
    CollectionAddress("postgres_example", "payment_card")
]


def test_extract_query_components():
    def found_query_keys(qconfig: QueryConfig, values: Dict[str, Any]) -> Set[str]:
        return set(qconfig.filter_values(values).keys())

    config = SQLQueryConfig(payment_card_node)
    assert config.fields == ["id", "name", "ccn", "customer_id", "billing_address_id"]
    assert config.query_keys == {"id", "customer_id"}

    # values exist for all query keys
    assert found_query_keys(
        config, {"id": ["A"], "customer_id": ["V"], "ignore_me": ["X"]}
    ) == {"id", "customer_id"}
    # with no values OR an empty set, these are omitted
    assert found_query_keys(
        config, {"id": ["A"], "customer_id": [], "ignore_me": ["X"]}
    ) == {"id"}
    assert found_query_keys(config, {"id": ["A"], "ignore_me": ["X"]}) == {"id"}
    assert found_query_keys(config, {"ignore_me": ["X"]}) == set()
    assert found_query_keys(config, {}) == set()


def test_filter_values():
    config = SQLQueryConfig(payment_card_node)
    assert config.filter_values(
        {"id": ["A"], "customer_id": ["V"], "ignore_me": ["X"]}
    ) == {"id": ["A"], "customer_id": ["V"]}

    assert config.filter_values(
        {"id": ["A"], "customer_id": [], "ignore_me": ["X"]}
    ) == {"id": ["A"]}

    assert config.filter_values({"id": ["A"], "ignore_me": ["X"]}) == {"id": ["A"]}

    assert config.filter_values({"id": [], "customer_id": ["V"]}) == {
        "customer_id": ["V"]
    }


def test_generated_sql_query():
    """Test that the generated query depends on the input set"""
    postgresql_connector = PostgreSQLConnector(ConnectionConfig())

    assert (
        str(
            SQLQueryConfig(payment_card_node).generate_query(
                {"id": ["A"], "customer_id": ["V"], "ignore_me": ["X"]}
            )
        )
        == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE id = :id OR customer_id = :customer_id"
    )

    assert (
        str(
            SQLQueryConfig(payment_card_node).generate_query(
                {"id": ["A"], "customer_id": [], "ignore_me": ["X"]}
            )
        )
        == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE id = :id"
    )

    assert (
        str(
            SQLQueryConfig(payment_card_node).generate_query(
                {"id": ["A"], "ignore_me": ["X"]}
            )
        )
        == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE id = :id"
    )

    assert (
        str(
            SQLQueryConfig(payment_card_node).generate_query(
                {"id": [], "customer_id": ["V"]}
            )
        )
        == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE customer_id = :customer_id"
    )

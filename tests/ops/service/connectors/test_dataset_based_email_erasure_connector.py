import pytest

from fides.api.ops.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    Collection,
    FieldAddress,
    GraphDataset,
    ScalarField,
)
from fides.api.ops.graph.graph import Edge, Node
from fides.api.ops.graph.traversal import TraversalNode, artificial_traversal_node
from fides.api.ops.models.privacy_request import ManualAction
from fides.api.ops.service.connectors.email_connector import EmailConnector

from ...graph.graph_test_util import erasure_policy


def generate_node_with_data_category(
    dr_name: str, ds_name: str, data_category, *field_names: str
) -> Node:
    ds = Collection(
        name=ds_name,
        fields=[
            ScalarField(name=s, data_categories=[data_category]) for s in field_names
        ],
    )
    dr = GraphDataset(
        name=dr_name,
        collections=[ds],
        connection_key=f"mock_connection_config_key_{dr_name}",
    )
    return Node(dr, ds)


class TestEmailConnector:
    @pytest.fixture(scope="session")
    def c_traversal_node(self):
        """
        Build a contrived graph that has postgres collection A, email collection B,
        and the root node all pointing to email collection C.
        Return the C Traversal Node

        Root -> A -> C
        Root -> B -> C
        Root -> C
        """
        a_tn = TraversalNode(
            generate_node_with_data_category(
                "postgres_db", "a_collection", "A", "id", "A_info", "email"
            )
        )

        b_tn = TraversalNode(
            generate_node_with_data_category(
                "email_db", "b_collection", "B", "id", "B_info", "upstream_id", "email"
            )
        )

        c_tn = TraversalNode(
            generate_node_with_data_category(
                "email_db", "c_collection", "A", "upstream_id", "C_info", "email", "id"
            )
        )

        root_node = artificial_traversal_node(ROOT_COLLECTION_ADDRESS)
        root_node.add_child(
            a_tn,
            Edge(
                FieldAddress(
                    ROOT_COLLECTION_ADDRESS.dataset,
                    ROOT_COLLECTION_ADDRESS.collection,
                    "email",
                ),
                FieldAddress("postgres_db", "a_collection", "email"),
            ),
        )

        root_node.add_child(
            b_tn,
            Edge(
                FieldAddress(
                    ROOT_COLLECTION_ADDRESS.dataset,
                    ROOT_COLLECTION_ADDRESS.collection,
                    "email",
                ),
                FieldAddress("email_db", "b_collection", "email"),
            ),
        )

        root_node.add_child(
            c_tn,
            Edge(
                FieldAddress(
                    ROOT_COLLECTION_ADDRESS.dataset,
                    ROOT_COLLECTION_ADDRESS.collection,
                    "email",
                ),
                FieldAddress("email_db", "c_collection", "email"),
            ),
        )

        a_tn.add_child(
            c_tn,
            Edge(
                FieldAddress("postgres_db", "a_collection", "id"),
                FieldAddress("email_db", "c_collection", "id"),
            ),
        )

        b_tn.add_child(
            c_tn,
            Edge(
                FieldAddress("email_db", "b_collection", "id"),
                FieldAddress("email_db", "c_collection", "id"),
            ),
        )
        return c_tn

    @pytest.fixture(scope="function")
    def email_connector(self, email_connection_config):
        return EmailConnector(email_connection_config)

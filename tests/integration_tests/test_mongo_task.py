import copy
import random
from datetime import datetime
from unittest import mock
from unittest.mock import Mock

import dask
import pytest
from bson import ObjectId

from fidesops.graph.config import FieldAddress, ScalarField, Collection, Dataset
from fidesops.graph.data_type import (
    IntTypeConverter,
    StringTypeConverter,
    ObjectIdTypeConverter,
)
from fidesops.graph.graph import DatasetGraph, Node, Edge
from fidesops.graph.traversal import TraversalNode
from fidesops.models.connectionconfig import (
    ConnectionConfig,
)
from fidesops.models.datasetconfig import convert_dataset_to_graph
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.dataset import FidesopsDataset
from fidesops.service.connectors import get_connector
from fidesops.task import graph_task
from fidesops.task.graph_task import filter_data_categories
from ..graph.graph_test_util import assert_rows_match, erasure_policy, field
from ..task.traversal_data import (
    integration_db_graph,
    integration_db_mongo_graph,
    combined_mongo_posgresql_graph,
)

dask.config.set(scheduler="processes")
policy = Policy()


@pytest.mark.integration
def test_combined_erasure_task(
    db,
    mongo_inserts,
    postgres_inserts,
    integration_mongodb_config,
    integration_postgres_config,
):
    policy = erasure_policy("A", "B")
    seed_email = postgres_inserts["customer"][0]["email"]
    privacy_request = PrivacyRequest(
        id=f"test_sql_erasure_task_{random.randint(0, 1000)}"
    )
    mongo_dataset, postgres_dataset = combined_mongo_posgresql_graph(
        integration_postgres_config, integration_mongodb_config
    )

    field(
        [postgres_dataset], ("postgres_example", "address", "city")
    ).data_categories = ["A"]
    field(
        [postgres_dataset], ("postgres_example", "address", "state")
    ).data_categories = ["B"]
    field(
        [postgres_dataset], ("postgres_example", "address", "zip")
    ).data_categories = ["C"]
    field(
        [postgres_dataset], ("postgres_example", "customer", "name")
    ).data_categories = ["A"]
    field([mongo_dataset], ("mongo_test", "address", "city")).data_categories = ["A"]
    field([mongo_dataset], ("mongo_test", "address", "state")).data_categories = ["B"]
    field([mongo_dataset], ("mongo_test", "address", "zip")).data_categories = ["C"]
    graph = DatasetGraph(mongo_dataset, postgres_dataset)

    access_request_data = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
    )

    x = graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
        access_request_data,
    )

    assert x == {
        "postgres_example:customer": 1,
        "postgres_example:orders": 0,
        "mongo_test:orders": 0,
        "postgres_example:address": 2,
        "mongo_test:address": 1,
        "postgres_example:payment_card": 0,
    }


@pytest.mark.integration
def test_mongo_erasure_task(db, mongo_inserts, integration_mongodb_config):
    policy = erasure_policy("A", "B")
    seed_email = mongo_inserts["customer"][0]["email"]
    privacy_request = PrivacyRequest(
        id=f"test_sql_erasure_task_{random.randint(0, 1000)}"
    )

    dataset, graph = integration_db_mongo_graph(
        "mongo_test", integration_mongodb_config.key
    )
    field([dataset], ("mongo_test", "address", "city")).data_categories = ["A"]
    field([dataset], ("mongo_test", "address", "state")).data_categories = ["B"]
    field([dataset], ("mongo_test", "address", "zip")).data_categories = ["C"]
    field([dataset], ("mongo_test", "customer", "name")).data_categories = ["A"]

    access_request_data = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config],
        {"email": seed_email},
    )
    v = graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config],
        {"email": seed_email},
        access_request_data,
    )

    assert v == {
        "mongo_test:customer": 1,
        "mongo_test:payment_card": 0,
        "mongo_test:orders": 0,
        "mongo_test:address": 2,
    }


@pytest.mark.integration
def test_dask_mongo_task(integration_mongodb_config: ConnectionConfig) -> None:
    privacy_request = PrivacyRequest(id=f"test_mongo_task_{random.randint(0,1000)}")

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        integration_db_graph("mongo_test", integration_mongodb_config.key),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    assert_rows_match(
        v["mongo_test:orders"],
        min_size=3,
        keys=["id", "customer_id", "payment_card_id"],
    )
    assert_rows_match(
        v["mongo_test:payment_card"],
        min_size=2,
        keys=["id", "name", "ccn", "customer_id"],
    )
    assert_rows_match(
        v["mongo_test:customer"],
        min_size=1,
        keys=["id", "name", "email"],
    )

    # links
    assert v["mongo_test:customer"][0]["email"] == "customer-1@example.com"


@pytest.mark.integration
def test_composite_key_erasure(
    db,
    integration_mongodb_config: ConnectionConfig,
) -> None:

    privacy_request = PrivacyRequest(id=f"test_mongo_task_{random.randint(0,1000)}")
    policy = erasure_policy("A")
    customer = Collection(
        name="customer",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(
                name="email",
                identity="email",
                data_type_converter=StringTypeConverter(),
            ),
        ],
    )

    composite_pk_test = Collection(
        name="composite_pk_test",
        fields=[
            ScalarField(
                name="id_a",
                primary_key=True,
                data_type_converter=IntTypeConverter(),
            ),
            ScalarField(
                name="id_b",
                primary_key=True,
                data_type_converter=IntTypeConverter(),
            ),
            ScalarField(
                name="description",
                data_type_converter=StringTypeConverter(),
                data_categories=["A"],
            ),
            ScalarField(
                name="customer_id",
                data_type_converter=StringTypeConverter(),
                references=[(FieldAddress("mongo_test", "customer", "id"), "from")],
            ),
        ],
    )

    dataset = Dataset(
        name="mongo_test",
        collections=[customer, composite_pk_test],
        connection_key=integration_mongodb_config.key,
    )

    access_request_data = graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    customer = access_request_data["mongo_test:customer"][0]
    composite_pk_test = access_request_data["mongo_test:composite_pk_test"][0]

    assert customer["id"] == "1"
    assert composite_pk_test["customer_id"] == "1"

    # erasure
    erasure = graph_task.run_erasure(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
        access_request_data,
    )

    assert erasure == {"mongo_test:customer": 0, "mongo_test:composite_pk_test": 1}

    # re-run access request. Description has been
    # nullified here.
    access_request_data = graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    assert access_request_data["mongo_test:composite_pk_test"][0]["description"] == None


@pytest.mark.integration
def test_access_erasure_type_conversion(
    db,
    integration_mongodb_config: ConnectionConfig,
) -> None:
    """Retrieve data from the type_link table. This requires retrieving data from
    the employee foreign_id field, which is an object_id stored as a string, and
    converting it into an object_id to query against the type_link_test._id field."""
    privacy_request = PrivacyRequest(id=f"test_mongo_task_{random.randint(0,1000)}")
    policy = erasure_policy("A")
    employee = Collection(
        name="employee",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(name="name", data_type_converter=StringTypeConverter()),
            ScalarField(
                name="email",
                identity="email",
                data_type_converter=StringTypeConverter(),
            ),
            ScalarField(name="foreign_id", data_type_converter=StringTypeConverter()),
        ],
    )

    type_link = Collection(
        name="type_link_test",
        fields=[
            ScalarField(
                name="_id",
                primary_key=True,
                data_type_converter=ObjectIdTypeConverter(),
                references=[
                    (FieldAddress("mongo_test", "employee", "foreign_id"), "from")
                ],
            ),
            ScalarField(
                name="name",
                data_type_converter=StringTypeConverter(),
                data_categories=["A"],
            ),
            ScalarField(name="key", data_type_converter=IntTypeConverter()),
        ],
    )

    dataset = Dataset(
        name="mongo_test",
        collections=[employee, type_link],
        connection_key=integration_mongodb_config.key,
    )

    access_request_data = graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
    )

    employee = access_request_data["mongo_test:employee"][0]
    link = access_request_data["mongo_test:type_link_test"][0]

    assert employee["foreign_id"] == "000000000000000000000001"
    assert link["_id"] == ObjectId("000000000000000000000001")

    # erasure
    erasure = graph_task.run_erasure(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
        access_request_data,
    )

    assert erasure == {"mongo_test:employee": 0, "mongo_test:type_link_test": 1}


@pytest.mark.integration
def test_filter_on_data_categories_mongo(
    db,
    privacy_request,
    example_datasets,
    policy,
    integration_mongodb_config,
    integration_postgres_config,
):

    postgres_config = copy.copy(integration_postgres_config)

    dataset_postgres = FidesopsDataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = FidesopsDataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])

    access_request_results = graph_task.run_access_request(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    target_categories = {
        "user.provided.identifiable.gender",
        "user.provided.identifiable.date_of_birth",
    }
    filtered_results = filter_data_categories(
        access_request_results, target_categories, dataset_graph
    )

    # Mongo results obtained via customer_id field from postgres_example_test_dataset.customer.id
    assert filtered_results == {
        "mongo_test:customer_details": [
            {"gender": "male", "birthday": datetime(1988, 1, 10, 0, 0)}
        ]
    }


class TestRetrievingDataMongo:
    @pytest.fixture
    def connector(self, integration_mongodb_config):
        return get_connector(integration_mongodb_config)

    @pytest.fixture
    def traversal_node(self, example_datasets, integration_mongodb_config):
        dataset = FidesopsDataset(**example_datasets[1])
        graph = convert_dataset_to_graph(dataset, integration_mongodb_config.key)
        node = Node(graph, graph.collections[0])  # customer collection
        traversal_node = TraversalNode(node)
        return traversal_node

    @pytest.mark.integration
    @mock.patch("fidesops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data(
        self,
        mock_incoming_edges: Mock,
        db,
        connector,
        traversal_node,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "id"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }

        results = connector.retrieve_data(
            traversal_node, Policy(), {"customer_id": [1]}
        )

        assert results[0]["customer_id"] == 1

    @pytest.mark.integration
    @mock.patch("fidesops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data_no_input(
        self,
        mock_incoming_edges: Mock,
        db,
        connector,
        traversal_node,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }
        results = connector.retrieve_data(traversal_node, Policy(), {"customer_id": []})
        assert results == []

        results = connector.retrieve_data(traversal_node, Policy(), {})
        assert results == []

        results = connector.retrieve_data(
            traversal_node, Policy(), {"bad_key": ["test"]}
        )
        assert results == []

        results = connector.retrieve_data(traversal_node, Policy(), {"email": [None]})
        assert results == []

        results = connector.retrieve_data(traversal_node, Policy(), {"email": None})
        assert results == []

    @pytest.mark.integration
    @mock.patch("fidesops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data_input_not_in_table(
        self,
        mock_incoming_edges: Mock,
        db,
        privacy_request,
        connection_config,
        example_datasets,
        connector,
        traversal_node,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }

        results = connector.retrieve_data(
            traversal_node, Policy(), {"customer_id": [5]}
        )

        assert results == []

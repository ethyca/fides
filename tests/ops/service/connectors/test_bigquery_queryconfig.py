from typing import Any, Dict, Generator, Set

import pytest
from fideslang.models import Dataset, MaskingStrategies
from pydantic import ValidationError

from fides.api.graph.config import CollectionAddress
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.schemas.namespace_meta.bigquery_namespace_meta import (
    BigQueryNamespaceMeta,
)
from fides.api.service.connectors import BigQueryConnector
from fides.api.service.connectors.query_config import BigQueryQueryConfig


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
class TestBigQueryQueryConfig:
    """
    Verify that the generate_query method of BigQueryQueryConfig correctly adjusts
    the table name based on the available namespace info in the dataset's fides_meta.
    """

    @pytest.fixture(scope="function")
    def bigquery_client(self, bigquery_connection_config):
        connector = BigQueryConnector(bigquery_connection_config)
        return connector.client()

    @pytest.fixture(scope="function")
    def dataset_graph(self, example_datasets, bigquery_connection_config):
        dataset = Dataset(**example_datasets[7])
        graph = convert_dataset_to_graph(dataset, bigquery_connection_config.key)
        return DatasetGraph(*[graph])

    @pytest.fixture(scope="function")
    def employee_node(self, dataset_graph):
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        return bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "employee")
        ].to_mock_execution_node()

    @pytest.fixture(scope="function")
    def address_node(self, dataset_graph):
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        return bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "address")
        ].to_mock_execution_node()

    @pytest.fixture
    def execution_node(
        self, bigquery_example_test_dataset_config_with_namespace_meta: DatasetConfig
    ) -> Generator:
        dataset_config = bigquery_example_test_dataset_config_with_namespace_meta
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        yield traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.mark.parametrize(
        "namespace_meta, expected_query",
        [
            (
                BigQueryNamespaceMeta(
                    project_id="cool_project", dataset_id="first_dataset"
                ),
                "SELECT address_id, created, custom_id, email, id, name FROM `cool_project.first_dataset.customer` WHERE (email = :email)",
            ),
            # Namespace meta will be a dict / JSON when retrieved from the DB
            (
                {"project_id": "cool_project", "dataset_id": "first_dataset"},
                "SELECT address_id, created, custom_id, email, id, name FROM `cool_project.first_dataset.customer` WHERE (email = :email)",
            ),
            (
                None,
                "SELECT address_id, created, custom_id, email, id, name FROM `customer` WHERE (email = :email)",
            ),
        ],
    )
    def test_generate_query_with_namespace_meta(
        self, execution_node: ExecutionNode, namespace_meta, expected_query
    ):
        query_config = BigQueryQueryConfig(execution_node, namespace_meta)
        assert (
            query_config.generate_query(
                input_data={"email": ["customer-1@example.com"]}
            ).text
            == expected_query
        )

    def test_generate_query_with_invalid_namespace_meta(
        self, execution_node: ExecutionNode
    ):
        with pytest.raises(ValidationError) as exc:
            BigQueryQueryConfig(
                execution_node, BigQueryNamespaceMeta(dataset_id="first_dataset")
            )
        assert "Field required" in str(exc)

    def test_generate_update_stmt(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test node uses typical policy-level masking strategies in an update statement
        """

        assert (
            dataset_graph.nodes[
                CollectionAddress("bigquery_example_test_dataset", "address")
            ].collection.masking_strategy_override
            is None
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmts = BigQueryQueryConfig(address_node).generate_masking_stmt(
            address_node,
            {
                "id": "1",
                "house": "222",
                "state": "TX",
                "city": "Houston",
                "street": "Water",
                "zip": "11111",
            },
            erasure_policy,
            privacy_request,
            bigquery_client,
        )
        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `address` SET `house`=%(house:STRING)s, `street`=%(street:STRING)s, `city`=%(city:STRING)s, `state`=%(state:STRING)s, `zip`=%(zip:STRING)s WHERE `address`.`id` = %(id_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_delete_stmt(
        self,
        db,
        employee_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test that collection-level masking strategy override takes precedence and a delete statement is issued
        instead
        """
        assert (
            dataset_graph.nodes[
                CollectionAddress("bigquery_example_test_dataset", "employee")
            ].collection.masking_strategy_override.strategy
            == MaskingStrategies.DELETE
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        delete_stmts = BigQueryQueryConfig(employee_node).generate_masking_stmt(
            employee_node,
            {
                "id": "2",
                "email": "employee-2@example.com",
                "name": "John Doe",
                "address_id": "3",
            },
            erasure_policy,
            privacy_request,
            bigquery_client,
        )
        stmts = set(str(stmt) for stmt in delete_stmts)
        expected_stmts = {
            "DELETE FROM `employee` WHERE `employee`.`id` = %(id_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_namespaced_update_stmt(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test node uses typical policy-level masking strategies in an update statement
        """

        assert (
            dataset_graph.nodes[
                CollectionAddress("bigquery_example_test_dataset", "address")
            ].collection.masking_strategy_override
            is None
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmts = BigQueryQueryConfig(
            address_node,
            BigQueryNamespaceMeta(
                project_id="silken-precinct-284918", dataset_id="fidesopstest"
            ),
        ).generate_masking_stmt(
            address_node,
            {
                "id": "1",
                "house": "222",
                "state": "TX",
                "city": "Houston",
                "street": "Water",
                "zip": "11111",
            },
            erasure_policy,
            privacy_request,
            bigquery_client,
        )
        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `silken-precinct-284918.fidesopstest.address` SET `house`=%(house:STRING)s, `street`=%(street:STRING)s, `city`=%(city:STRING)s, `state`=%(state:STRING)s, `zip`=%(zip:STRING)s WHERE `silken-precinct-284918.fidesopstest.address`.`id` = %(id_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_namespaced_delete_stmt(
        self,
        db,
        employee_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test that collection-level masking strategy override takes precedence and a delete statement is issued
        instead
        """
        assert (
            dataset_graph.nodes[
                CollectionAddress("bigquery_example_test_dataset", "employee")
            ].collection.masking_strategy_override.strategy
            == MaskingStrategies.DELETE
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        delete_stmts = BigQueryQueryConfig(
            employee_node,
            BigQueryNamespaceMeta(
                project_id="silken-precinct-284918", dataset_id="fidesopstest"
            ),
        ).generate_masking_stmt(
            employee_node,
            {
                "id": "2",
                "email": "employee-2@example.com",
                "name": "John Doe",
                "address_id": "3",
            },
            erasure_policy,
            privacy_request,
            bigquery_client,
        )
        stmts = set(str(stmt) for stmt in delete_stmts)
        expected_stmts = {
            "DELETE FROM `silken-precinct-284918.fidesopstest.employee` WHERE `silken-precinct-284918.fidesopstest.employee`.`id` = %(id_1:STRING)s"
        }
        assert stmts == expected_stmts

from typing import Generator

import pytest
from fideslang.models import Dataset
from pydantic import ValidationError

from fides.api.graph.config import CollectionAddress
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.schemas.namespace_meta.snowflake_namespace_meta import (
    SnowflakeNamespaceMeta,
)
from fides.api.service.connectors import SnowflakeConnector
from fides.api.service.connectors.query_configs.snowflake_query_config import (
    SnowflakeQueryConfig,
)


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
class TestSnowflakeQueryConfig:
    """
    Verify that the generate_query method of SnowflakeQueryConfig correctly adjusts
    the table name based on the available namespace info in the dataset's fides_meta.
    """

    @pytest.fixture(scope="function")
    def snowflake_client(self, snowflake_connection_config):
        connector = SnowflakeConnector(snowflake_connection_config)
        return connector.client()

    @pytest.fixture(scope="function")
    def dataset_graph(self, example_datasets, snowflake_connection_config):
        dataset = Dataset(**example_datasets[2])
        graph = convert_dataset_to_graph(dataset, snowflake_connection_config.key)
        return DatasetGraph(*[graph])

    @pytest.fixture(scope="function")
    def employee_node(self, dataset_graph):
        identity = {"email": "customer-1@example.com"}
        snowflake_traversal = Traversal(dataset_graph, identity)
        return snowflake_traversal.traversal_node_dict[
            CollectionAddress("snowflake_example_test_dataset", "employee")
        ].to_mock_execution_node()

    @pytest.fixture(scope="function")
    def address_node(self, dataset_graph):
        identity = {"email": "customer-1@example.com"}
        snowflake_traversal = Traversal(dataset_graph, identity)
        return snowflake_traversal.traversal_node_dict[
            CollectionAddress("snowflake_example_test_dataset", "address")
        ].to_mock_execution_node()

    @pytest.fixture
    def execution_node(
        self, snowflake_example_test_dataset_config_with_namespace_meta: DatasetConfig
    ) -> Generator:
        dataset_config = snowflake_example_test_dataset_config_with_namespace_meta
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        yield traversal.traversal_node_dict[
            CollectionAddress("snowflake_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.mark.parametrize(
        "namespace_meta, expected_query",
        [
            (
                SnowflakeNamespaceMeta(database_name="FIDESOPS_TEST", schema="TEST"),
                'SELECT "address_id", "created", "email", "id", "name", "variant_eg" FROM "FIDESOPS_TEST"."TEST"."customer" WHERE ("email" = (:email))',
            ),
            # Namespace meta will be a dict / JSON when retrieved from the DB
            (
                {"database_name": "FIDESOPS_TEST", "schema": "TEST"},
                'SELECT "address_id", "created", "email", "id", "name", "variant_eg" FROM "FIDESOPS_TEST"."TEST"."customer" WHERE ("email" = (:email))',
            ),
            (
                {
                    "database_name": "FIDESOPS_TEST",
                    "schema": "TEST",
                    "connection_type": "snowflake",
                },
                'SELECT "address_id", "created", "email", "id", "name", "variant_eg" FROM "FIDESOPS_TEST"."TEST"."customer" WHERE ("email" = (:email))',
            ),
            (
                None,
                'SELECT "address_id", "created", "email", "id", "name", "variant_eg" FROM "customer" WHERE ("email" = (:email))',
            ),
        ],
    )
    def test_generate_query_with_namespace_meta(
        self, execution_node: ExecutionNode, namespace_meta, expected_query
    ):
        query_config = SnowflakeQueryConfig(execution_node, namespace_meta)
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
            SnowflakeQueryConfig(
                execution_node, SnowflakeNamespaceMeta(dataset_id="first_dataset")
            )
        assert "Field required" in str(exc)

    def test_generate_update_stmt(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
        dataset_graph,
    ):
        """
        Test node uses typical policy-level masking strategies in an update statement
        """

        assert (
            dataset_graph.nodes[
                CollectionAddress("snowflake_example_test_dataset", "address")
            ].collection.masking_strategy_override
            is None
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmt = SnowflakeQueryConfig(address_node).generate_update_stmt(
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
        )
        assert (
            str(update_stmt)
            == 'UPDATE "address" SET "city" = :city, "house" = :house, "state" = :state, "street" = :street, "zip" = :zip WHERE "id" = :id'
        )

    def test_generate_namespaced_update_stmt(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
        dataset_graph,
    ):
        """
        Test node uses typical policy-level masking strategies in an update statement
        """

        assert (
            dataset_graph.nodes[
                CollectionAddress("snowflake_example_test_dataset", "address")
            ].collection.masking_strategy_override
            is None
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmt = SnowflakeQueryConfig(
            address_node,
            SnowflakeNamespaceMeta(database_name="FIDESOPS_TEST", schema="TEST"),
        ).generate_update_stmt(
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
        )
        assert (
            str(update_stmt)
            == 'UPDATE "FIDESOPS_TEST"."TEST"."address" SET "city" = :city, "house" = :house, "state" = :state, "street" = :street, "zip" = :zip WHERE "id" = :id'
        )

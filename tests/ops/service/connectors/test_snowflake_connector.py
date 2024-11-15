from typing import Generator

import pytest
from fideslang.models import Dataset

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.schemas.namespace_meta.snowflake_namespace_meta import (
    SnowflakeNamespaceMeta,
)
from fides.api.service.connectors.sql_connector import SnowflakeConnector


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
class TestSnowflakeConnector:
    """
    Tests to verify that the query_config method of SnowflakeConnector
    correctly retrieves namespace metadata from the dataset (if available).
    """

    @pytest.fixture
    def execution_node(
        self, snowflake_example_test_dataset_config: DatasetConfig
    ) -> Generator:
        dataset_config = snowflake_example_test_dataset_config
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        yield traversal.traversal_node_dict[
            CollectionAddress("snowflake_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.fixture
    def execution_node_with_namespace_meta(
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

    def test_query_config(
        self,
        snowflake_example_test_dataset_config: DatasetConfig,
        execution_node,
    ):
        dataset_config = snowflake_example_test_dataset_config
        connector = SnowflakeConnector(dataset_config.connection_config)
        query_config = connector.query_config(execution_node)
        assert query_config.namespace_meta is None

    def test_query_config_with_namespace_meta(
        self,
        snowflake_example_test_dataset_config_with_namespace_meta: DatasetConfig,
        execution_node_with_namespace_meta,
    ):
        dataset_config = snowflake_example_test_dataset_config_with_namespace_meta
        connector = SnowflakeConnector(dataset_config.connection_config)
        query_config = connector.query_config(execution_node_with_namespace_meta)
        assert query_config.namespace_meta == SnowflakeNamespaceMeta(
            **dataset_config.ctl_dataset.fides_meta["namespace"]
        )

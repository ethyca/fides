import pytest

from fides.api.common_exceptions import UnreachableNodesError
from fides.api.graph.graph import DatasetGraph, GraphDataset
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig


class TestOptionalIdentityFilter:
    """
    Tests for the OptionalIdentityFilter, which allows nodes that are reachable
    by optional identities to not raise an exception.
    """

    def test_optionally_reachable_nodes_do_not_raise_exception(
        self, optional_identities_dataset_config, connection_config: ConnectionConfig
    ):
        """Test that a collection reachable by an optional identity (email) does not raise an exception"""
        graph_dataset = optional_identities_dataset_config.get_graph()
        dataset_graph = DatasetGraph(graph_dataset)

        # Test address collection with email identity
        identities = {"user_id": "123"}
        Traversal(dataset_graph, identities)

    def test_unreachable_nodes_raise_exception(
        self, unreachable_collection_dataset_config: DatasetConfig
    ):
        """Test that a collection with no identity field or incoming dataset references raises an exception"""
        graph_dataset: GraphDataset = unreachable_collection_dataset_config.get_graph()
        dataset_graph = DatasetGraph(graph_dataset)

        identities = {"user_id": "123"}

        with pytest.raises(UnreachableNodesError) as exc:
            Traversal(dataset_graph, identities)
        assert "Some nodes were not reachable: unreachable_collection:address" in str(
            exc
        )

    def test_reachable_by_reference_does_not_raise_exception(
        self, reachable_by_reference_dataset_config: DatasetConfig
    ):
        """Test that a collection reachable by reference does not raise an exception"""
        graph: GraphDataset = reachable_by_reference_dataset_config.get_graph()
        dataset_graph = DatasetGraph(graph)

        identities = {"user_id": "123"}
        Traversal(dataset_graph, identities)

    @pytest.mark.parametrize(
        "identities",
        [
            {"email": "test@example.com"},
            {"user_id": "123"},
            {"email": "test@example.com", "user_id": "123"},
        ],
    )
    def test_reachable_by_multiple_identities(
        self, multiple_identities_dataset_config: DatasetConfig, identities
    ):
        """Test that a collection reachable by multiple identities does not raise an exception"""
        graph: GraphDataset = multiple_identities_dataset_config.get_graph()
        dataset_graph = DatasetGraph(graph)

        Traversal(dataset_graph, identities)

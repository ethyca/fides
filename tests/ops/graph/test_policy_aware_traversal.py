from typing import Dict, Tuple

import pytest

from fides.api.common_exceptions import UnreachableNodesError
from fides.api.graph.config import GraphDataset
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig


class TestPolicyAwareTraversal:

    def _create_graph_and_seed(
        self, dataset_config: DatasetConfig
    ) -> Tuple[DatasetGraph, Dict[str, str]]:
        """Creates dataset graph and identity seed dictionary from config"""
        graph: GraphDataset = dataset_config.get_graph()
        dataset_graph = DatasetGraph(graph)
        identity_seed: Dict[str, str] = {
            k: "something" for k in dataset_graph.identity_keys.values()
        }
        return dataset_graph, identity_seed

    def test_directly_reachable(
        self, policy, directly_reachable_dataset_config: DatasetConfig
    ):
        dataset_graph, identity_seed = self._create_graph_and_seed(
            directly_reachable_dataset_config
        )
        Traversal(dataset_graph, identity_seed, policy=policy)

    def test_ignores_unreachable_without_data_category(
        self, policy, unreachable_without_data_categories_dataset_config: DatasetConfig
    ):
        dataset_graph, identity_seed = self._create_graph_and_seed(
            unreachable_without_data_categories_dataset_config
        )
        Traversal(dataset_graph, identity_seed, policy=policy)

    def test_unreachable_with_data_category_errors(
        self, policy, unreachable_with_data_categories_dataset_config: DatasetConfig
    ):
        dataset_graph, identity_seed = self._create_graph_and_seed(
            unreachable_with_data_categories_dataset_config
        )
        with pytest.raises(UnreachableNodesError) as exc:
            Traversal(dataset_graph, identity_seed, policy=policy)
        assert (
            "Some nodes were not reachable: unreachable_with_data_categories:address"
            in str(exc)
        )

from typing import Dict

from fides.api.graph.config import GraphDataset
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig


class TestPolicyAwareTraversal:

    def test_directly_reachable(
        self, policy, directly_reachable_dataset_config: DatasetConfig
    ):
        graph: GraphDataset = directly_reachable_dataset_config.get_graph()
        dataset_graph = DatasetGraph(graph)
        identity_seed: Dict[str, str] = {
            k: "something" for k in dataset_graph.identity_keys.values()
        }
        Traversal(dataset_graph, identity_seed, policy)

    def test_ignores_unreachable_without_data_category(
        self, policy, unreachable_without_data_categories_dataset_config: DatasetConfig
    ):
        graph: GraphDataset = (
            unreachable_without_data_categories_dataset_config.get_graph()
        )
        dataset_graph = DatasetGraph(graph)
        identity_seed: Dict[str, str] = {
            k: "something" for k in dataset_graph.identity_keys.values()
        }
        Traversal(dataset_graph, identity_seed, policy)

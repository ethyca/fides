from fides.api.common_exceptions import UnreachableNodesError
from fides.api.graph.config import CollectionAddress, Field
from fides.api.graph.traversal import Traversal
from pygtrie import StringTrie

from typing import Any, Dict, List, Optional, Set

from fides.api.models.policy import Policy

from fides.api.graph.graph import DatasetGraph


def has_data_categories(field: Field, categories: Set[str]) -> bool:
    """
    Check if any field data categories match with the target categories using a trie-based approach.

    Args:
        field: The field to check
        categories: Set of target categories to match against

    Returns:
        True if any field category matches with target categories (including hierarchical matches)
    """
    if not field.data_categories:
        return False

    # Build trie from target categories
    target_trie = StringTrie(separator=".")
    for category in categories:
        target_trie[category] = True

    # Check each field category for matches
    for category in field.data_categories:
        prefix, _ = target_trie.longest_prefix(category)
        if prefix:
            return True

    return False


class PolicyAwareTraversal(Traversal):
    def __init__(
        self,
        graph: DatasetGraph,
        data: Dict[str, Any],
        *,
        policy: Optional[Policy] = None,
    ):
        target_data_categories: Set[str] = {"user"}
        if policy:
            target_data_categories = set(policy.get_access_target_categories()) + set(
                policy.get_erasure_target_categories()
            )
        try:
            super().__init__(graph, data)
        except UnreachableNodesError as exc:
            unreachable_target_node_keys: List[str] = []

            for key in exc.unreachable_node_keys:
                dataset, collection = key.split(":")
                node = self.traversal_node_dict[CollectionAddress(dataset, collection)]
                if node.node.collection.recursively_collect_matches(
                    lambda field: has_data_categories(field, target_data_categories)
                ):
                    unreachable_target_node_keys.append(key)

            if unreachable_target_node_keys:
                if policy:
                    raise UnreachableNodesError(
                        f"The following nodes are unreachable but contain data categories targeted by the {policy.key} policy",
                        unreachable_target_node_keys,
                    )
                else:
                    raise UnreachableNodesError(
                        "The following nodes are unreachable but contain user data categories",
                        unreachable_target_node_keys,
                    )

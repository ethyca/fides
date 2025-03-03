from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, Set

from fides.api.common_exceptions import TraversalError, UnreachableNodesError
from fides.api.graph.graph import DatasetGraph
from fides.api.models.policy import Policy

if TYPE_CHECKING:
    from fides.api.graph.traversal import TraversalNode


class NodeFilter(Protocol):
    """Protocol for node filters that determine if nodes should be excluded from traversal"""

    def exclude_node(self, node: "TraversalNode") -> bool:
        """Returns True if the node should be excluded from traversal requirements"""


class CustomRequestFieldFilter:
    """
    Remove nodes that have custom request fields, since we don't care if these are reachable or not.
    They will be used independently by the Dynamic Email Erasure Connector.

    TODO: ideally we'll update the Traversal code to include these "custom request field datasets"
    as part of the main graph. This is a targeted workaround for now.
    """

    def exclude_node(self, node: "TraversalNode") -> bool:
        return bool(node.node.collection.custom_request_fields())


class PolicyDataCategoryFilter:
    """
    If a policy is provided, we will allow collections without relevant
    data categories to remain unreachable without raising any exceptions.
    """

    def __init__(self, policy: Optional[Policy]):
        self.policy = policy

    def exclude_node(self, node: "TraversalNode") -> bool:
        if not self.policy:
            return False
        return not self.policy.applies_to(node)


class OptionalIdentityFilter:
    """
    Filter that excludes nodes that are reachable by an optional identity.
    This prevents traversal errors for nodes that would be reachable if all possible identities were provided.
    """

    def __init__(self, graph: DatasetGraph, identities: Dict[str, Any]):
        self.graph = graph
        self.identities = identities

        # Pre-compute which nodes are reachable with each identity
        self.reachable_by_identity: Dict[str, Set[str]] = {}

        # Get all collection addresses as strings
        all_collection_addresses = {str(addr) for addr in graph.nodes.keys()}

        # Test reachability with each possible identity seed
        for identity_key in graph.identity_keys.values():
            self._compute_reachable_nodes(identity_key, all_collection_addresses)

    def _compute_reachable_nodes(
        self, identity_key: str, all_addresses: Set[str]
    ) -> None:
        """Helper method to compute which nodes are reachable with a given identity key"""

        from fides.api.graph.traversal import BaseTraversal

        try:
            # Create a traversal object with just this identity
            BaseTraversal(self.graph, {identity_key: "dummy_value"})
            # If successful, all nodes are reachable
            self.reachable_by_identity[identity_key] = all_addresses
        except UnreachableNodesError as exc:
            # Get reachable nodes by removing unreachable ones from all nodes
            unreachable = set(exc.errors)
            self.reachable_by_identity[identity_key] = all_addresses - unreachable
        except TraversalError:
            # If traversal fails for other reasons, no nodes are reachable
            self.reachable_by_identity[identity_key] = set()

    def exclude_node(self, node: "TraversalNode") -> bool:
        """
        Exclude nodes that are reachable by any identity, provided or optional.
        Nodes (collections) not reachable by any identities should not be excluded and still be considered an error.
        """
        node_address = str(node.address)

        # Check if node is reachable by any provided identity
        for identity_key in self.identities:
            if node_address in self.reachable_by_identity.get(identity_key, set()):
                return True

        # Check if node is reachable by any optional identity
        for identity_key, reachable_nodes in self.reachable_by_identity.items():
            if identity_key not in self.identities and node_address in reachable_nodes:
                return True

        # Node isn't reachable by any identity, don't exclude it (will be an error)
        return False

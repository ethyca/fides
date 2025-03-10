from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from fides.api.common_exceptions import TraversalError, UnreachableNodesError
from fides.api.graph.graph import DatasetGraph
from fides.api.models.policy import Policy
from fides.api.util.logger import suppress_logging

if TYPE_CHECKING:
    from fides.api.graph.traversal import TraversalNode


class NodeFilter(ABC):
    """Abstract base class for node filters that determine if nodes should be excluded from traversal"""

    def __init__(self) -> None:
        self.skipped_nodes: Dict[str, str] = {}

    @abstractmethod
    def exclude_node(self, node: "TraversalNode") -> bool:
        """Returns True if the node should be excluded from traversal requirements"""


class CustomRequestFieldFilter(NodeFilter):
    """
    Remove nodes that have custom request fields, since we don't care if these are reachable or not.
    They will be used independently by the Dynamic Email Erasure Connector.

    TODO: ideally we'll update the Traversal code to include these "custom request field datasets"
    as part of the main graph. This is a targeted workaround for now.
    """

    def exclude_node(self, node: "TraversalNode") -> bool:
        return bool(node.node.collection.custom_request_fields())


class PolicyDataCategoryFilter(NodeFilter):
    """
    If a policy is provided, we will allow collections without relevant
    data categories to remain unreachable without raising any exceptions.
    """

    def __init__(self, policy: Optional[Policy]):
        super().__init__()
        self.policy = policy

    def exclude_node(self, node: "TraversalNode") -> bool:
        if not self.policy:
            return False
        return not self.policy.applies_to(node)


class OptionalIdentityFilter(NodeFilter):

    def __init__(self, graph: DatasetGraph, identities: Dict[str, Any]):
        """
        Filter that excludes nodes that are reachable by an optional identity.
        This prevents traversal errors for nodes that would be reachable if the required identities were provided.
        """

        super().__init__()
        self.graph = graph
        self.identities = identities
        self.skipped_nodes: Dict[str, str] = {}

        # Pre-compute which nodes are reachable with each identity
        self.reachable_by_identity: Dict[str, Set[str]] = {}

        # Get all collection addresses as strings
        all_collection_addresses = {str(addr) for addr in graph.nodes.keys()}

        # Test reachability with each possible identity seed
        for identity_key in graph.identity_keys.values():
            self._compute_reachable_nodes(identity_key, all_collection_addresses)

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

        # Find all optional identities that can reach this node
        reaching_identities = []
        for identity_key, reachable_nodes in self.reachable_by_identity.items():
            if identity_key not in self.identities and node_address in reachable_nodes:
                reaching_identities.append(identity_key)

        # If any optional identities can reach this node, record them and exclude
        if reaching_identities:
            self.skipped_nodes[node_address] = self._format_skip_message(
                node.address.value, reaching_identities
            )
            return True

        # Node isn't reachable by any identity, don't exclude it (will be an error)
        return False

    def _compute_reachable_nodes(
        self, identity_key: str, all_addresses: Set[str]
    ) -> None:
        """Helper method to compute which nodes are reachable with a given identity key"""

        from fides.api.graph.traversal import BaseTraversal

        try:
            # Create a traversal object with just this identity
            with suppress_logging():
                # Suppress the logs since we don't want to flood the logs
                # with traversal info for each identity we want to evaluate
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

    def _format_skip_message(
        self, node_address: str, reaching_identities: List[str]
    ) -> str:
        """
        Format the skip message with proper grammar based on identity counts.
        """

        # Format lists of quoted identities
        reachable_ids_str = ", ".join(f'"{id}"' for id in reaching_identities)
        provided_ids = list(self.identities.keys())
        provided_ids_str = ", ".join(f'"{id}"' for id in provided_ids)

        # Determine singular/plural forms based on counts
        reachable_term = "identity" if len(reaching_identities) == 1 else "identities"
        provided_term = "identity" if len(provided_ids) == 1 else "identities"
        was_were = "was" if len(provided_ids) == 1 else "were"

        return (
            f'Skipping the "{node_address}" collection, it is reachable by the {reachable_ids_str} '
            f"{reachable_term} but only the {provided_ids_str} {provided_term} {was_were} provided"
        )

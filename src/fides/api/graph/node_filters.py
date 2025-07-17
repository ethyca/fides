from abc import ABC, abstractmethod
from collections import defaultdict, deque
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph, Edge
from fides.api.models.policy import Policy

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

        # OPTIMIZATION: Use a single traversal-like algorithm to compute reachability
        # for all identities at once, rather than running full traversals
        self.reachable_by_identity: Dict[str, Set[str]] = (
            self._compute_all_reachability()
        )

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

    def _compute_all_reachability(self) -> Dict[str, Set[str]]:
        """
        Compute reachability for all identities in a single pass using graph traversal logic.
        This avoids creating multiple BaseTraversal objects.
        """

        # Result: identity_key -> set of reachable collection addresses
        reachable_by_identity: Dict[str, Set[str]] = defaultdict(set)

        # Build edge index by collection for efficient lookups
        edges_by_collection: Dict[Any, List[Edge]] = defaultdict(list)
        for edge in self.graph.edges:
            edges_by_collection[edge.f1.collection_address()].append(edge)
            edges_by_collection[edge.f2.collection_address()].append(edge)

        # Group field addresses by identity key (since multiple collections can have the same identity)
        identity_to_fields: Dict[str, List[Any]] = defaultdict(list)
        for field_address, identity_key in self.graph.identity_keys.items():
            identity_to_fields[identity_key].append(field_address)

        # For each identity key, find all reachable nodes from ALL collections that have this identity
        for identity_key, field_addresses in identity_to_fields.items():
            visited = set()
            queue: deque[CollectionAddress] = deque()

            # Start from ALL collections that have this identity field
            for field_address in field_addresses:
                start_collection = field_address.collection_address()
                if start_collection not in visited:
                    queue.append(start_collection)
                    visited.add(start_collection)
                    reachable_by_identity[identity_key].add(str(start_collection))

            # BFS to find all reachable collections from any starting point
            while queue:
                current = queue.popleft()

                # Find all edges from current collection
                for edge in edges_by_collection.get(current, []):
                    # Get the other end of the edge
                    other_addr = None
                    if edge.f1.collection_address() == current:
                        other_addr = edge.f2.collection_address()
                    elif edge.f2.collection_address() == current:
                        other_addr = edge.f1.collection_address()

                    if other_addr and other_addr not in visited:
                        visited.add(other_addr)
                        reachable_by_identity[identity_key].add(str(other_addr))
                        queue.append(other_addr)

        return dict(reachable_by_identity)  # Convert defaultdict to regular dict

    def _format_skip_message(self, node_address: str, identities: List[str]) -> str:
        """
        Format the skip message with proper grammar based on identity counts.
        """
        # Get the provided identities for the message
        provided_identities = list(self.identities.keys())

        if len(identities) == 1:
            identity_str = f'the "{identities[0]}" identity'
        else:
            # Format as: the "email", "phone" or "user_id" identity
            identity_list = ", ".join(f'"{id}"' for id in identities[:-1])
            identity_str = f'the {identity_list} or "{identities[-1]}" identity'

        if len(provided_identities) == 1:
            provided_str = f'the "{provided_identities[0]}" identity was provided'
        else:
            # Format as: the "user_id" and "name" identities were provided
            provided_list = ", ".join(f'"{id}"' for id in provided_identities[:-1])
            provided_str = f'the {provided_list} and "{provided_identities[-1]}" identities were provided'

        return f'Skipping the "{node_address}" collection, it is reachable by {identity_str} but only {provided_str}'

from typing import TYPE_CHECKING, Optional, Protocol

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

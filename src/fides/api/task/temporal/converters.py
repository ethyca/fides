"""Serializable dataclasses for Temporal workflow/activity communication.

Temporal requires all workflow and activity parameters to be serializable.
ORM objects cannot cross workflow/activity boundaries — only IDs and
plain data structures are passed. Activities create their own DB sessions
and load ORM objects as needed.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TraversalPhase:
    ACCESS = "access"
    ERASURE = "erasure"
    CONSENT = "consent"


@dataclass
class DSRLifecycleParams:
    """Input to the top-level DSR lifecycle workflow."""

    privacy_request_id: str
    from_webhook_id: Optional[str] = None
    from_step: Optional[str] = None


@dataclass
class DSRLifecycleResult:
    """Output from the DSR lifecycle workflow."""

    status: str
    error_message: Optional[str] = None


@dataclass
class PrivacyRequestContext:
    """Loaded context about a privacy request, returned by the load_context activity."""

    privacy_request_id: str
    policy_id: str
    has_access_rules: bool
    has_erasure_rules: bool
    has_consent_rules: bool
    identity_data: Dict[str, Any] = field(default_factory=dict)
    property_id: Optional[str] = None
    fides_connector_datasets: List[str] = field(default_factory=list)


@dataclass
class NodeInfo:
    """Metadata about a single node in the traversal graph."""

    address: str
    upstream: List[str] = field(default_factory=list)
    downstream: List[str] = field(default_factory=list)
    is_root: bool = False
    is_terminator: bool = False
    is_manual_task: bool = False
    async_type: Optional[str] = None
    request_task_id: Optional[str] = None
    already_completed: bool = False
    already_skipped: bool = False


@dataclass
class GraphPlan:
    """Serializable representation of a traversal graph for a phase.

    Contains the node addresses and their dependency relationships,
    plus metadata about each node needed for dispatch.
    """

    privacy_request_id: str
    phase: str
    nodes: Dict[str, NodeInfo] = field(default_factory=dict)


@dataclass
class GraphTraversalParams:
    """Input to the graph traversal child workflow."""

    privacy_request_id: str
    phase: str
    graph_plan: GraphPlan


@dataclass
class GraphTraversalResult:
    """Output from the graph traversal child workflow."""

    status: str
    completed_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[str] = field(default_factory=list)


@dataclass
class NodeExecutionParams:
    """Input to the per-node child workflow."""

    privacy_request_id: str
    phase: str
    node_address: str
    request_task_id: str
    is_manual_task: bool = False
    async_type: Optional[str] = None


@dataclass
class NodeExecutionResult:
    """Output from per-node execution."""

    node_address: str
    status: str
    rows_processed: int = 0
    error_message: Optional[str] = None

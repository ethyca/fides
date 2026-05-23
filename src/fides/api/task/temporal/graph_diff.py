"""Graph diff and cascading invalidation for Temporal DSR reprocessing.

Compares old graph (from existing RequestTasks) against a freshly-built
graph to determine which nodes need re-execution vs preservation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger


class NodeStatus(str, Enum):
    CLEAN = "clean"
    DIRTY = "dirty"
    ADDED = "added"
    ORPHAN = "orphan"


class DirtyReason(str, Enum):
    EDGES_CHANGED = "edges_changed"
    FIELDS_CHANGED = "fields_changed"
    CONNECTION_CHANGED = "connection_changed"
    SAAS_CONFIG_CHANGED = "saas_config_changed"
    PREVIOUSLY_ERRORED = "previously_errored"
    UPSTREAM_DIRTY = "upstream_dirty"
    NODE_ADDED = "node_added"


@dataclass
class OldNodeSnapshot:
    """Snapshot of a node from existing RequestTasks."""

    address: str
    incoming_edges: list[tuple[str, str]] = field(default_factory=list)
    outgoing_edges: list[tuple[str, str]] = field(default_factory=list)
    input_keys: list[str] = field(default_factory=list)
    connection_key: str = ""
    collection_json: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    rows_masked: int = 0
    consent_sent: bool = False
    access_data_exists: bool = False
    request_task_id: str = ""


@dataclass
class NewNodeSnapshot:
    """Snapshot of a node from the freshly-built graph."""

    address: str
    incoming_edges: list[tuple[str, str]] = field(default_factory=list)
    outgoing_edges: list[tuple[str, str]] = field(default_factory=list)
    input_keys: list[str] = field(default_factory=list)
    connection_key: str = ""
    collection_json: dict[str, Any] = field(default_factory=dict)
    saas_config_hash: str | None = None


@dataclass
class NodeDiffResult:
    """Result of diffing a single node."""

    address: str
    status: NodeStatus
    reasons: list[DirtyReason] = field(default_factory=list)
    old_request_task_id: str | None = None


@dataclass
class GraphDiffResult:
    """Full result of diffing old vs new graph."""

    nodes: dict[str, NodeDiffResult] = field(default_factory=dict)

    @property
    def dirty_nodes(self) -> list[str]:
        return [
            addr for addr, node in self.nodes.items() if node.status == NodeStatus.DIRTY
        ]

    @property
    def added_nodes(self) -> list[str]:
        return [
            addr for addr, node in self.nodes.items() if node.status == NodeStatus.ADDED
        ]

    @property
    def clean_nodes(self) -> list[str]:
        return [
            addr for addr, node in self.nodes.items() if node.status == NodeStatus.CLEAN
        ]

    @property
    def orphan_nodes(self) -> list[str]:
        return [
            addr
            for addr, node in self.nodes.items()
            if node.status == NodeStatus.ORPHAN
        ]

    @property
    def nodes_needing_execution(self) -> list[str]:
        return [
            addr
            for addr, node in self.nodes.items()
            if node.status in (NodeStatus.DIRTY, NodeStatus.ADDED)
        ]

    def to_summary(self) -> dict[str, Any]:
        return {
            "clean": len(self.clean_nodes),
            "dirty": len(self.dirty_nodes),
            "added": len(self.added_nodes),
            "orphan": len(self.orphan_nodes),
            "dirty_details": {
                addr: [r.value for r in self.nodes[addr].reasons]
                for addr in self.dirty_nodes
            },
        }


def _normalize_edges(edges: list[tuple[str, str]]) -> set[tuple[str, str]]:
    return {(e[0], e[1]) for e in edges}


def _hash_collection_fields(collection_json: dict[str, Any]) -> str:
    """Hash the field-relevant parts of a serialized Collection.

    Extracts field names, references, identities, data_categories,
    masking overrides, and other properties that affect execution.
    """
    relevant = _extract_field_signature(collection_json)
    return hashlib.sha256(
        json.dumps(relevant, sort_keys=True, default=str).encode()
    ).hexdigest()


def _extract_field_signature(collection_json: dict[str, Any]) -> dict[str, Any]:
    """Extract the parts of a collection that matter for invalidation."""
    fields = collection_json.get("fields", [])

    def _field_sig(f: dict[str, Any]) -> dict[str, Any]:
        sig: dict[str, Any] = {"name": f.get("name")}
        if f.get("references"):
            sig["references"] = f["references"]
        if f.get("identity"):
            sig["identity"] = f["identity"]
        if f.get("data_categories"):
            sig["data_categories"] = sorted(f["data_categories"])
        if f.get("return_all_elements") is not None:
            sig["return_all_elements"] = f["return_all_elements"]
        if f.get("read_only") is not None:
            sig["read_only"] = f["read_only"]
        if f.get("masking_strategy_override"):
            sig["masking_strategy_override"] = f["masking_strategy_override"]
        if f.get("fields"):
            sig["fields"] = [_field_sig(sub) for sub in f["fields"]]
        return sig

    return {
        "fields": [_field_sig(f) for f in fields],
        "after": sorted(collection_json.get("after", [])),
        "erase_after": sorted(collection_json.get("erase_after", [])),
        "masking_strategy_override": collection_json.get("masking_strategy_override"),
        "property_scope": collection_json.get("property_scope"),
        "grouped_inputs": sorted(collection_json.get("grouped_inputs", [])),
    }


def _diff_single_node(
    address: str,
    old: OldNodeSnapshot,
    new: NewNodeSnapshot,
) -> NodeDiffResult:
    """Compare a single retained node between old and new graph."""
    reasons: list[DirtyReason] = []

    if old.status in ("error", "pending", "retrying"):
        reasons.append(DirtyReason.PREVIOUSLY_ERRORED)

    old_incoming = _normalize_edges(old.incoming_edges)
    new_incoming = _normalize_edges(new.incoming_edges)

    if old_incoming != new_incoming:
        reasons.append(DirtyReason.EDGES_CHANGED)

    old_field_hash = _hash_collection_fields(old.collection_json)
    new_field_hash = _hash_collection_fields(new.collection_json)
    if old_field_hash != new_field_hash:
        reasons.append(DirtyReason.FIELDS_CHANGED)

    if old.connection_key != new.connection_key:
        reasons.append(DirtyReason.CONNECTION_CHANGED)

    if new.saas_config_hash is not None:
        old_saas_hash = _compute_saas_hash_from_old(old)
        if old_saas_hash != new.saas_config_hash:
            reasons.append(DirtyReason.SAAS_CONFIG_CHANGED)

    status = NodeStatus.DIRTY if reasons else NodeStatus.CLEAN
    return NodeDiffResult(
        address=address,
        status=status,
        reasons=reasons,
        old_request_task_id=old.request_task_id,
    )


def _compute_saas_hash_from_old(old: OldNodeSnapshot) -> str | None:
    """We don't store SaaS config hash on old tasks, so return None
    to indicate unknown. The caller handles this asymmetry."""
    return None


def _cascade_dirty(
    diff_result: GraphDiffResult,
    new_nodes: dict[str, NewNodeSnapshot],
) -> None:
    """Cascade DIRTY status downstream through the graph.

    BFS from each dirty/added node through outgoing edges.
    """
    new_downstream: dict[str, list[str]] = {}
    for addr, node in new_nodes.items():
        new_downstream[addr] = []

    for addr, node in new_nodes.items():
        for edge in node.outgoing_edges:
            target_addr = edge[1].rsplit(".", 1)[0] if "." in edge[1] else edge[1]
            target_collection = (
                ":".join(target_addr.split(":")[:2])
                if ":" in target_addr
                else target_addr
            )
            if target_collection in new_downstream and target_collection != addr:
                if target_collection not in new_downstream[addr]:
                    new_downstream[addr].append(target_collection)

    seeds = [
        addr
        for addr, node_diff in diff_result.nodes.items()
        if node_diff.status in (NodeStatus.DIRTY, NodeStatus.ADDED)
    ]

    visited: set[str] = set(seeds)
    queue = list(seeds)

    while queue:
        current = queue.pop(0)
        for downstream in new_downstream.get(current, []):
            if downstream in visited:
                continue
            if downstream not in diff_result.nodes:
                continue
            node_diff = diff_result.nodes[downstream]
            if node_diff.status == NodeStatus.CLEAN:
                node_diff.status = NodeStatus.DIRTY
                node_diff.reasons.append(DirtyReason.UPSTREAM_DIRTY)
                visited.add(downstream)
                queue.append(downstream)
            elif node_diff.status == NodeStatus.ORPHAN:
                continue
            else:
                visited.add(downstream)
                queue.append(downstream)


def compute_graph_diff(
    old_nodes: dict[str, OldNodeSnapshot],
    new_nodes: dict[str, NewNodeSnapshot],
) -> GraphDiffResult:
    """Compute the full graph diff between old and new traversal graphs.

    1. Classify nodes as ADDED, ORPHAN, or RETAINED
    2. For RETAINED nodes, diff edges, fields, connection
    3. Cascade DIRTY downstream
    """
    result = GraphDiffResult()

    old_addrs = set(old_nodes.keys())
    new_addrs = set(new_nodes.keys())

    for addr in new_addrs - old_addrs:
        result.nodes[addr] = NodeDiffResult(
            address=addr,
            status=NodeStatus.ADDED,
            reasons=[DirtyReason.NODE_ADDED],
        )

    for addr in old_addrs - new_addrs:
        result.nodes[addr] = NodeDiffResult(
            address=addr,
            status=NodeStatus.ORPHAN,
            old_request_task_id=old_nodes[addr].request_task_id,
        )

    for addr in old_addrs & new_addrs:
        result.nodes[addr] = _diff_single_node(addr, old_nodes[addr], new_nodes[addr])

    _cascade_dirty(result, new_nodes)

    summary = result.to_summary()
    logger.info(
        "Graph diff complete: {} clean, {} dirty, {} added, {} orphan",
        summary["clean"],
        summary["dirty"],
        summary["added"],
        summary["orphan"],
    )
    if summary["dirty_details"]:
        logger.info("Dirty node reasons: {}", summary["dirty_details"])

    return result


def build_old_node_snapshots_from_request_tasks(
    request_tasks: list[Any],
) -> dict[str, OldNodeSnapshot]:
    """Build OldNodeSnapshot dict from RequestTask ORM objects."""
    snapshots: dict[str, OldNodeSnapshot] = {}

    for task in request_tasks:
        traversal_details = task.traversal_details or {}
        snapshots[task.collection_address] = OldNodeSnapshot(
            address=task.collection_address,
            incoming_edges=traversal_details.get("incoming_edges", []),
            outgoing_edges=traversal_details.get("outgoing_edges", []),
            input_keys=traversal_details.get("input_keys", []),
            connection_key=traversal_details.get("dataset_connection_key", ""),
            collection_json=task.collection or {},
            status=task.status.value
            if hasattr(task.status, "value")
            else str(task.status),
            rows_masked=task.rows_masked or 0,
            consent_sent=bool(task.consent_sent),
            access_data_exists=bool(task.get_access_data())
            if hasattr(task, "get_access_data")
            else False,
            request_task_id=str(task.id),
        )

    return snapshots


def build_new_node_snapshots_from_traversal(
    traversal_nodes: dict[Any, Any],
    networkx_graph: Any,
    connection_configs: dict[str, Any] | None = None,
) -> dict[str, NewNodeSnapshot]:
    """Build NewNodeSnapshot dict from TraversalNode objects and networkx graph.

    connection_configs: optional dict of connection_key -> ConnectionConfig
    for SaaS config hashing.
    """
    snapshots: dict[str, NewNodeSnapshot] = {}

    for addr, traversal_node in traversal_nodes.items():
        addr_str = addr.value if hasattr(addr, "value") else str(addr)

        incoming = [(e.f1.value, e.f2.value) for e in traversal_node.incoming_edges()]
        outgoing = [(e.f1.value, e.f2.value) for e in traversal_node.outgoing_edges()]
        input_keys = [tn.value for tn in traversal_node.input_keys()]
        connection_key = traversal_node.node.dataset.connection_key
        collection_json = traversal_node.node.collection.model_dump(mode="json")

        saas_hash = None
        if connection_configs and connection_key in connection_configs:
            cc = connection_configs[connection_key]
            saas_config = getattr(cc, "saas_config", None)
            if saas_config:
                saas_hash = hashlib.sha256(
                    json.dumps(saas_config, sort_keys=True, default=str).encode()
                ).hexdigest()

        snapshots[addr_str] = NewNodeSnapshot(
            address=addr_str,
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            input_keys=input_keys,
            connection_key=connection_key,
            collection_json=collection_json,
            saas_config_hash=saas_hash,
        )

    return snapshots

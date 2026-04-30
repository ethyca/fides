from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Literal, Optional

from loguru import logger

from fides.api.graph.config import ROOT_COLLECTION_ADDRESS, CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.preview.schemas import (
    ActionStatus,
    CollectionCount,
    CollectionDetail,
    DatasetDetail,
    FieldDetail,
    IdentityRoot,
    IntegrationNode,
    ManualTaskNode,
    PreviewEdge,
    Reachability,
    SystemRef,
    TraversalPreview,
)
from fides.api.graph.traversal import Traversal, TraversalNode

ActionType = Literal["access", "erasure"]


class TraversalPreviewBuilder:
    """Build a structured preview of a DSR traversal without persisting RequestTask rows."""

    def __init__(
        self,
        graph: DatasetGraph,
        identity_seed: Dict[str, Any],
        action_type: ActionType,
        connection_lookup: Dict[str, Dict[str, Any]],
        manual_tasks: List[ManualTaskNode],
        identity_types: Optional[List[str]] = None,
    ):
        self.graph = graph
        self.identity_seed = identity_seed
        self.action_type = action_type
        self.connection_lookup = connection_lookup
        self.manual_tasks = manual_tasks
        self.identity_types = identity_types or sorted(identity_seed.keys())

    def build(self) -> TraversalPreview:
        captured = self._capture_traversal()
        integrations = self._build_integration_nodes(captured)
        edges = self._build_edges(captured, integrations)
        edges += self._manual_task_edges()

        return TraversalPreview(
            action_type=self.action_type,
            identity_root=IdentityRoot(identity_types=self.identity_types),
            integrations=integrations,
            manual_tasks=self.manual_tasks,
            edges=edges,
            warnings=[],
        )

    # --- internals ---

    def _capture_traversal(self) -> Dict[CollectionAddress, List[CollectionAddress]]:
        """Run Traversal in capture mode. Returns {node_address: [parent_addresses]}.

        Construction runs verification (which builds edge indices required by
        ``traverse``); we don't pass ``skip_verification`` here. Unreachable graphs
        are handled by the caller in Task 4 via a different code path.
        """
        traversal = Traversal(self.graph, self.identity_seed)
        deps: Dict[CollectionAddress, List[CollectionAddress]] = defaultdict(list)

        def capture(node: TraversalNode, _env: Dict[CollectionAddress, Any]) -> None:
            for edge in node.incoming_edges():
                parent = edge.f1.collection_address()
                if parent != node.address:
                    deps[node.address].append(parent)

        environment: Dict[CollectionAddress, Any] = {ROOT_COLLECTION_ADDRESS: [self.identity_seed]}
        try:
            traversal.traverse(environment, capture)
        except Exception as exc:  # capture-mode should not raise on partial graphs
            logger.warning("Traversal capture failed: {}", exc)
        return deps

    def _build_integration_nodes(
        self, captured: Dict[CollectionAddress, List[CollectionAddress]]
    ) -> List[IntegrationNode]:
        """Group captured collection addresses by ConnectionConfig."""
        per_integration: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "datasets": defaultdict(lambda: {"collections": []}),
            "data_categories": set(),
            "traversed": 0,
        })

        for addr in captured.keys():
            if addr == ROOT_COLLECTION_ADDRESS:
                continue
            dataset_key = addr.dataset
            conn = self.connection_lookup.get(dataset_key)
            if conn is None:
                continue
            integration_key = conn["connection_key"]
            bucket = per_integration[integration_key]
            bucket["traversed"] += 1
            graph_node = self.graph.nodes.get(addr)
            if graph_node is None:
                continue
            collection_detail = self._collection_detail(graph_node)
            bucket["datasets"][dataset_key]["collections"].append(collection_detail)
            for f in collection_detail.fields:
                bucket["data_categories"].update(f.data_categories)

        nodes: List[IntegrationNode] = []
        for integration_key, bucket in per_integration.items():
            conn = next(c for c in self.connection_lookup.values() if c["connection_key"] == integration_key)
            datasets = [
                DatasetDetail(fides_key=ds_key, collections=ds_bucket["collections"])
                for ds_key, ds_bucket in bucket["datasets"].items()
            ]
            total = sum(len(ds.collections) for ds in datasets)
            nodes.append(IntegrationNode(
                id=f"integration:{integration_key}",
                connection_key=integration_key,
                connector_type=conn["connector_type"],
                system=SystemRef(**conn["system"]) if conn.get("system") else None,
                reachability=Reachability.REACHABLE,
                action_status=ActionStatus.ACTIVE,
                collection_count=CollectionCount(traversed=bucket["traversed"], total=total),
                data_categories=sorted(bucket["data_categories"]),
                datasets=datasets,
            ))
        return nodes

    def _collection_detail(self, node) -> CollectionDetail:
        collection = node.collection
        identity_field_names = {f.name for f in collection.fields if getattr(f, "identity", None)}
        return CollectionDetail(
            name=collection.name,
            skipped=getattr(collection, "skip_processing", False),
            fields=[
                FieldDetail(
                    name=f.name,
                    data_categories=list(getattr(f, "data_categories", []) or []),
                    is_identity=f.name in identity_field_names,
                )
                for f in collection.fields
            ],
        )

    def _build_edges(
        self,
        captured: Dict[CollectionAddress, List[CollectionAddress]],
        integrations: List[IntegrationNode],
    ) -> List[PreviewEdge]:
        integration_ids = {i.connection_key for i in integrations}
        dataset_to_integration: Dict[str, str] = {
            ds_key: conn["connection_key"]
            for ds_key, conn in self.connection_lookup.items()
        }
        # Collapse collection-level deps to integration-level
        edge_counts: Dict[tuple, int] = defaultdict(int)
        roots_added: set = set()
        for addr, parents in captured.items():
            target_dataset = addr.dataset
            target_integration = dataset_to_integration.get(target_dataset)
            if target_integration not in integration_ids:
                continue
            target_id = f"integration:{target_integration}"
            if not parents:
                key = ("identity-root", target_id)
                if key not in roots_added:
                    edge_counts[key] += 1
                    roots_added.add(key)
                continue
            for parent in parents:
                if parent == ROOT_COLLECTION_ADDRESS:
                    edge_counts[("identity-root", target_id)] += 1
                    continue
                src_dataset = parent.dataset
                src_integration = dataset_to_integration.get(src_dataset)
                if src_integration is None or src_integration == target_integration:
                    continue
                edge_counts[(f"integration:{src_integration}", target_id)] += 1

        return [
            PreviewEdge(source=src, target=tgt, kind="depends_on", dep_count=cnt)
            for (src, tgt), cnt in edge_counts.items()
        ]

    def _manual_task_edges(self) -> List[PreviewEdge]:
        return [
            PreviewEdge(source=mt.id, target=gated, kind="gates")
            for mt in self.manual_tasks
            for gated in mt.gates
        ]

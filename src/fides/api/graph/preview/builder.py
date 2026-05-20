from __future__ import annotations

from collections import defaultdict
from typing import Any, Literal

from loguru import logger

from fides.api.common_exceptions import (
    TraversalError,
    UnreachableEdgesError,
    UnreachableNodesError,
)
from fides.api.graph.config import ROOT_COLLECTION_ADDRESS, CollectionAddress
from fides.api.graph.graph import DatasetGraph, Node
from fides.api.graph.preview.policy_filter import filter_categories_by_targets
from fides.api.graph.preview.reachability import classify_per_integration
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
        identity_seed: dict[str, Any],
        action_type: ActionType,
        connection_lookup: dict[str, dict[str, Any]],
        manual_tasks: list[ManualTaskNode],
        identity_types: list[str] | None = None,
        target_categories: set[str] | None = None,
    ):
        self.graph = graph
        self.identity_seed = identity_seed
        self.action_type = action_type
        self.connection_lookup = connection_lookup
        self.manual_tasks = manual_tasks
        self.identity_types = identity_types or sorted(identity_seed.keys())
        # When ``None``, all categories pass through (no policy bound). When a
        # set is supplied, fields and integration rollups are filtered to
        # categories that are descendants of (or equal to) any target.
        self.target_categories = target_categories
        # Pre-build connection_key → connection-metadata index for O(1) lookup.
        self._conn_by_key: dict[str, dict[str, Any]] = {
            conn["connection_key"]: conn for conn in connection_lookup.values()
        }
        # dataset fides_key → connection_key, used by edge builders.
        self._dataset_to_integration: dict[str, str] = {
            ds_key: conn["connection_key"] for ds_key, conn in connection_lookup.items()
        }
        # connection_key → [dataset fides_keys] (reverse of _dataset_to_integration).
        self._integration_datasets: dict[str, list[str]] = defaultdict(list)
        for ds_key, conn in connection_lookup.items():
            self._integration_datasets[conn["connection_key"]].append(ds_key)
        # dataset → [CollectionAddress] index for O(1) lookup in _static_dataset_detail.
        self._dataset_nodes: dict[str, list[CollectionAddress]] = defaultdict(list)
        for addr in graph.nodes:
            self._dataset_nodes[addr.dataset].append(addr)
        self._warnings: list[str] = []

    def build(self) -> TraversalPreview:
        captured = self._capture_traversal()
        integrations = self._build_integration_nodes(captured)

        classification = classify_per_integration(
            self.graph, set(captured.keys()), self.connection_lookup
        )
        existing = {i.connection_key: i for i in integrations}
        for integration_key, reach in classification.items():
            if integration_key in existing:
                existing[integration_key].reachability = reach
                continue
            conn = self._conn_by_key[integration_key]
            datasets, total, data_categories = self._static_dataset_detail(
                integration_key
            )
            integrations.append(
                IntegrationNode(
                    id=f"integration:{integration_key}",
                    connection_key=integration_key,
                    connector_type=conn["connector_type"],
                    saas_type=conn.get("saas_type"),
                    system=SystemRef(**conn["system"]) if conn.get("system") else None,
                    reachability=reach,
                    action_status=ActionStatus.ACTIVE,
                    collection_count=CollectionCount(traversed=0, total=total),
                    data_categories=data_categories,
                    datasets=datasets,
                )
            )

        edges = self._build_edges(captured, integrations)
        if not edges:
            # Traversal didn't capture deps (e.g. graph has unreachable nodes);
            # fall back to FK-derived static edges so the canvas still shows flow.
            edges = self._static_edges(integrations)
        edges += self._manual_task_edges()

        return TraversalPreview(
            action_type=self.action_type,
            identity_root=IdentityRoot(identity_types=self.identity_types),
            integrations=integrations,
            manual_tasks=self.manual_tasks,
            edges=edges,
            warnings=self._warnings,
        )

    # --- internals ---

    def _capture_traversal(self) -> dict[CollectionAddress, list[CollectionAddress]]:
        """Run Traversal in capture mode. Returns {node_address: [parent_addresses]}.

        If the graph contains unreachable nodes, ``Traversal`` raises during
        construction (it runs a verification traverse). We catch that and return
        an empty deps map; the caller falls back to static reachability
        classification for unreachable integrations.
        """
        self._warnings.clear()
        deps: dict[CollectionAddress, list[CollectionAddress]] = defaultdict(list)

        def capture(node: TraversalNode, _env: dict[CollectionAddress, Any]) -> None:
            for edge in node.incoming_edges():
                parent = edge.f1.collection_address()
                if parent != node.address:
                    deps[node.address].append(parent)

        try:
            traversal = Traversal(self.graph, self.identity_seed)
            environment: dict[CollectionAddress, Any] = {
                ROOT_COLLECTION_ADDRESS: [self.identity_seed]
            }
            traversal.traverse(environment, capture)
        except (UnreachableNodesError, UnreachableEdgesError, TraversalError) as exc:
            logger.warning("Traversal capture failed: {}", exc)
            self._warnings.append(str(exc))
        return deps

    def _build_integration_nodes(
        self, captured: dict[CollectionAddress, list[CollectionAddress]]
    ) -> list[IntegrationNode]:
        """Group captured collection addresses by ConnectionConfig."""
        per_integration: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "datasets": defaultdict(lambda: {"collections": []}),
                "data_categories": set(),
                "traversed": 0,
            }
        )

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

        nodes: list[IntegrationNode] = []
        for integration_key, bucket in per_integration.items():
            conn = self._conn_by_key[integration_key]
            datasets = [
                DatasetDetail(fides_key=ds_key, collections=ds_bucket["collections"])
                for ds_key, ds_bucket in bucket["datasets"].items()
            ]
            total = sum(len(ds.collections) for ds in datasets)
            nodes.append(
                IntegrationNode(
                    id=f"integration:{integration_key}",
                    connection_key=integration_key,
                    connector_type=conn["connector_type"],
                    saas_type=conn.get("saas_type"),
                    system=SystemRef(**conn["system"]) if conn.get("system") else None,
                    reachability=Reachability.REACHABLE,
                    action_status=ActionStatus.ACTIVE,
                    collection_count=CollectionCount(
                        traversed=bucket["traversed"], total=total
                    ),
                    data_categories=sorted(bucket["data_categories"]),
                    datasets=datasets,
                )
            )
        return nodes

    def _collection_detail(self, node: Node) -> CollectionDetail:
        collection = node.collection
        identity_field_names = {
            f.name for f in collection.fields if getattr(f, "identity", None)
        }
        return CollectionDetail(
            name=collection.name,
            fields=[
                FieldDetail(
                    name=f.name,
                    data_categories=filter_categories_by_targets(
                        getattr(f, "data_categories", []) or [],
                        self.target_categories,
                    ),
                    is_identity=f.name in identity_field_names,
                )
                for f in collection.fields
            ],
        )

    def _static_dataset_detail(
        self, integration_key: str
    ) -> tuple[list[DatasetDetail], int, list[str]]:
        """Build dataset/collection/field detail directly from ``self.graph`` for an
        integration that didn't participate in the traversal.

        Returns ``(datasets, total_collection_count, sorted_data_categories)``.
        """
        per_dataset: dict[str, list[CollectionDetail]] = defaultdict(list)
        data_categories: set[str] = set()
        for ds_key in self._integration_datasets.get(integration_key, ()):
            for addr in self._dataset_nodes.get(ds_key, ()):
                node = self.graph.nodes.get(addr)
                if node is None:
                    continue
                detail = self._collection_detail(node)
                per_dataset[ds_key].append(detail)
                for f in detail.fields:
                    data_categories.update(f.data_categories)
        datasets = [
            DatasetDetail(fides_key=ds_key, collections=collections)
            for ds_key, collections in per_dataset.items()
        ]
        total = sum(len(d.collections) for d in datasets)
        return datasets, total, sorted(data_categories)

    def _build_edges(
        self,
        captured: dict[CollectionAddress, list[CollectionAddress]],
        integrations: list[IntegrationNode],
    ) -> list[PreviewEdge]:
        integration_ids = {i.connection_key for i in integrations}
        # Collapse collection-level deps to integration-level
        edge_counts: dict[tuple, int] = defaultdict(int)
        roots_added: set = set()
        for addr, parents in captured.items():
            target_dataset = addr.dataset
            target_integration = self._dataset_to_integration.get(target_dataset)
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
                src_integration = self._dataset_to_integration.get(src_dataset)
                if src_integration is None or src_integration == target_integration:
                    continue
                edge_counts[(f"integration:{src_integration}", target_id)] += 1

        return self._edges_from_counts(edge_counts)

    @staticmethod
    def _edges_from_counts(edge_counts: dict[tuple, int]) -> list[PreviewEdge]:
        return [
            PreviewEdge(source=src, target=tgt, kind="depends_on", dep_count=cnt)
            for (src, tgt), cnt in edge_counts.items()
        ]

    def _manual_task_edges(self) -> list[PreviewEdge]:
        return [
            PreviewEdge(source=mt.id, target=gated, kind="gates")
            for mt in self.manual_tasks
            for gated in mt.gates
        ]

    def _static_edges(self, integrations: list[IntegrationNode]) -> list[PreviewEdge]:
        """Build integration-level edges from ``self.graph.edges`` directly.

        When ``Traversal`` fails (e.g. unreachable nodes), ``captured`` is empty
        and ``_build_edges`` produces nothing. Walking the static graph edges
        still yields the FK-reference shape between integrations, so users can
        see how data flows even without a successful traversal.
        """
        integration_ids = {i.connection_key for i in integrations}
        edge_counts: dict[tuple, int] = defaultdict(int)
        # Identify integrations with identity fields using graph.identity_keys.
        # Only iterates identity datasets (typically small) instead of all graph nodes.
        identity_datasets = {addr.dataset for addr in self.graph.identity_keys}
        identity_targets: set[str] = {
            self._dataset_to_integration[ds]
            for ds in identity_datasets
            if ds in self._dataset_to_integration
            and self._dataset_to_integration[ds] in integration_ids
        }

        for edge in self.graph.edges:
            src_addr = edge.f1.collection_address()
            tgt_addr = edge.f2.collection_address()
            if (
                src_addr == ROOT_COLLECTION_ADDRESS
                or tgt_addr == ROOT_COLLECTION_ADDRESS
            ):
                continue
            src_integration = self._dataset_to_integration.get(src_addr.dataset)
            tgt_integration = self._dataset_to_integration.get(tgt_addr.dataset)
            if src_integration is None or tgt_integration is None:
                continue
            if src_integration == tgt_integration:
                continue
            if (
                src_integration not in integration_ids
                or tgt_integration not in integration_ids
            ):
                continue
            edge_counts[
                (f"integration:{src_integration}", f"integration:{tgt_integration}")
            ] += 1

        edges = self._edges_from_counts(edge_counts)
        for integration_key in identity_targets:
            edges.append(
                PreviewEdge(
                    source="identity-root",
                    target=f"integration:{integration_key}",
                    kind="depends_on",
                    dep_count=1,
                )
            )
        return edges

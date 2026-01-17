"""
Test to compare the original MatchingQueue traverse with the optimized In-Degree Tracking traverse.

This ensures the optimized algorithm produces equivalent results.
"""

import time
from typing import Any, Dict, List, Set, Tuple

import pytest

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    FieldAddress,
    GraphDataset,
    ScalarField,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import BaseTraversal, TraversalNode


def create_linear_chain(n: int) -> Tuple[DatasetGraph, Dict[str, Any]]:
    """Create a linear chain: A -> B -> C -> ... -> N"""
    datasets = []

    for i in range(n):
        fields = [
            ScalarField(name="id"),
            ScalarField(name="parent_id"),
            ScalarField(name="data"),
        ]
        if i == 0:
            fields[0].identity = "email"

        dataset = GraphDataset(
            name=f"ds_{i}",
            collections=[Collection(name=f"coll_{i}", fields=fields)],
            connection_key=f"conn_{i}",
        )
        datasets.append(dataset)

    # Each node references the previous node with "from" direction
    for i in range(1, n):
        for field in datasets[i].collections[0].fields:
            if field.name == "parent_id":
                field.references.append(
                    (FieldAddress(f"ds_{i-1}", f"coll_{i-1}", "id"), "from")
                )
                break

    graph = DatasetGraph(*datasets)
    return graph, {"email": "test@example.com"}


def create_star_graph(n: int) -> Tuple[DatasetGraph, Dict[str, Any]]:
    """Create a star topology: Center -> [A, B, C, ...]"""
    datasets = []

    # Center node with identity
    center_fields = [ScalarField(name="id", identity="email"), ScalarField(name="data")]
    center = GraphDataset(
        name="center",
        collections=[Collection(name="center_coll", fields=center_fields)],
        connection_key="conn_center",
    )
    datasets.append(center)

    # Outer nodes reference the center
    for i in range(1, n):
        fields = [
            ScalarField(name="id"),
            ScalarField(name="center_id"),
            ScalarField(name="data"),
        ]
        dataset = GraphDataset(
            name=f"outer_{i}",
            collections=[Collection(name=f"outer_coll_{i}", fields=fields)],
            connection_key=f"conn_{i}",
        )
        datasets.append(dataset)

        for field in dataset.collections[0].fields:
            if field.name == "center_id":
                field.references.append(
                    (FieldAddress("center", "center_coll", "id"), "from")
                )
                break

    graph = DatasetGraph(*datasets)
    return graph, {"email": "test@example.com"}


def create_diamond_graph() -> Tuple[DatasetGraph, Dict[str, Any]]:
    """Create a diamond: A -> B, C -> D with B and C both pointing to D"""
    a_fields = [ScalarField(name="id", identity="email"), ScalarField(name="data")]
    b_fields = [ScalarField(name="id"), ScalarField(name="a_id"), ScalarField(name="data")]
    c_fields = [ScalarField(name="id"), ScalarField(name="a_id"), ScalarField(name="data")]
    d_fields = [ScalarField(name="id"), ScalarField(name="b_id"), ScalarField(name="c_id"), ScalarField(name="data")]

    ds_a = GraphDataset(name="ds_a", collections=[Collection(name="coll_a", fields=a_fields)], connection_key="conn_a")
    ds_b = GraphDataset(name="ds_b", collections=[Collection(name="coll_b", fields=b_fields)], connection_key="conn_b")
    ds_c = GraphDataset(name="ds_c", collections=[Collection(name="coll_c", fields=c_fields)], connection_key="conn_c")
    ds_d = GraphDataset(name="ds_d", collections=[Collection(name="coll_d", fields=d_fields)], connection_key="conn_d")

    # B and C reference A
    for field in ds_b.collections[0].fields:
        if field.name == "a_id":
            field.references.append((FieldAddress("ds_a", "coll_a", "id"), "from"))
    for field in ds_c.collections[0].fields:
        if field.name == "a_id":
            field.references.append((FieldAddress("ds_a", "coll_a", "id"), "from"))

    # D references B and C
    for field in ds_d.collections[0].fields:
        if field.name == "b_id":
            field.references.append((FieldAddress("ds_b", "coll_b", "id"), "from"))
        elif field.name == "c_id":
            field.references.append((FieldAddress("ds_c", "coll_c", "id"), "from"))

    graph = DatasetGraph(ds_a, ds_b, ds_c, ds_d)
    return graph, {"email": "test@example.com"}


def create_graph_with_after() -> Tuple[DatasetGraph, Dict[str, Any]]:
    """Create a graph with 'after' dependencies"""
    a_fields = [ScalarField(name="id", identity="email"), ScalarField(name="data")]
    b_fields = [ScalarField(name="id"), ScalarField(name="a_id"), ScalarField(name="data")]
    c_fields = [ScalarField(name="id", identity="phone"), ScalarField(name="data")]

    ds_a = GraphDataset(name="ds_a", collections=[Collection(name="coll_a", fields=a_fields)], connection_key="conn_a")
    ds_b = GraphDataset(name="ds_b", collections=[Collection(name="coll_b", fields=b_fields)], connection_key="conn_b")
    # C has 'after' dependency on B
    ds_c = GraphDataset(
        name="ds_c",
        collections=[Collection(name="coll_c", fields=c_fields, after={CollectionAddress("ds_b", "coll_b")})],
        connection_key="conn_c",
    )

    # B references A
    for field in ds_b.collections[0].fields:
        if field.name == "a_id":
            field.references.append((FieldAddress("ds_a", "coll_a", "id"), "from"))

    graph = DatasetGraph(ds_a, ds_b, ds_c)
    return graph, {"email": "test@example.com", "phone": "555-1234"}


def capture_traversal(traversal: BaseTraversal, use_optimized: bool) -> Dict[str, Any]:
    """Capture traversal results for comparison."""
    visited_order: List[str] = []
    traversal_nodes: Dict[CollectionAddress, TraversalNode] = {}

    def capture_fn(tn: TraversalNode, data: Dict) -> None:
        if not tn.is_root_node():
            visited_order.append(tn.address.value)
            data[tn.address] = tn

    if use_optimized:
        end_nodes = traversal.traverse(traversal_nodes, capture_fn)  # New O(N+E) algorithm
    else:
        end_nodes = traversal._traverse_legacy(traversal_nodes, capture_fn)  # Old O(N²) algorithm

    # Build parent/child map
    parent_child_map: Dict[str, List[str]] = {}
    for addr, tn in traversal_nodes.items():
        parent_child_map[addr.value] = sorted([c.value for c in tn.children.keys()])

    return {
        "visited_set": set(visited_order),
        "end_nodes": sorted([e.value for e in end_nodes]),
        "parent_child_map": parent_child_map,
        "node_count": len(traversal_nodes),
    }


def results_equivalent(original: Dict[str, Any], optimized: Dict[str, Any]) -> Tuple[bool, str]:
    """Compare two traversal results."""
    diffs = []

    if original["visited_set"] != optimized["visited_set"]:
        diffs.append(f"Visited nodes differ: {original['visited_set'].symmetric_difference(optimized['visited_set'])}")

    if original["end_nodes"] != optimized["end_nodes"]:
        diffs.append(f"End nodes differ: original={original['end_nodes']}, optimized={optimized['end_nodes']}")

    if original["parent_child_map"] != optimized["parent_child_map"]:
        for node in set(original["parent_child_map"].keys()) | set(optimized["parent_child_map"].keys()):
            o = original["parent_child_map"].get(node, [])
            p = optimized["parent_child_map"].get(node, [])
            if o != p:
                diffs.append(f"Children of {node} differ: original={o}, optimized={p}")

    if original["node_count"] != optimized["node_count"]:
        diffs.append(f"Node count differs: original={original['node_count']}, optimized={optimized['node_count']}")

    if diffs:
        return False, "\n".join(diffs)
    return True, "Results are equivalent"


class TestTraversalComparison:
    """Compare original and optimized traversal algorithms."""

    def test_linear_chain_small(self):
        """Test linear chain with 5 nodes."""
        graph, seed = create_linear_chain(5)

        # Create separate traversal instances to avoid state sharing
        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ:\n{diff}"

    def test_linear_chain_medium(self):
        """Test linear chain with 50 nodes."""
        graph, seed = create_linear_chain(50)

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ:\n{diff}"

    def test_star_graph_small(self):
        """Test star topology with 10 nodes."""
        graph, seed = create_star_graph(10)

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ:\n{diff}"

    def test_diamond_graph(self):
        """Test diamond pattern."""
        graph, seed = create_diamond_graph()

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ:\n{diff}"

    def test_graph_with_after_deps(self):
        """Test graph with 'after' dependencies."""
        graph, seed = create_graph_with_after()

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ:\n{diff}"


class TestTraversalPerformance:
    """Performance comparison between original and optimized algorithms."""

    def test_performance_linear_chain(self):
        """Compare performance on a 200-node linear chain."""
        graph, seed = create_linear_chain(200)

        # Time original
        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        start = time.perf_counter()
        capture_traversal(traversal_orig, use_optimized=False)
        original_time = time.perf_counter() - start

        # Time optimized
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)
        start = time.perf_counter()
        capture_traversal(traversal_opt, use_optimized=True)
        optimized_time = time.perf_counter() - start

        print(f"\n200-node linear chain:")
        print(f"  Original:  {original_time:.4f}s")
        print(f"  Optimized: {optimized_time:.4f}s")
        print(f"  Speedup:   {original_time / optimized_time:.2f}x")

    def test_performance_star_graph(self):
        """Compare performance on a 200-node star graph."""
        graph, seed = create_star_graph(200)

        # Time original
        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        start = time.perf_counter()
        capture_traversal(traversal_orig, use_optimized=False)
        original_time = time.perf_counter() - start

        # Time optimized
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)
        start = time.perf_counter()
        capture_traversal(traversal_opt, use_optimized=True)
        optimized_time = time.perf_counter() - start

        print(f"\n200-node star graph:")
        print(f"  Original:  {original_time:.4f}s")
        print(f"  Optimized: {optimized_time:.4f}s")
        print(f"  Speedup:   {original_time / optimized_time:.2f}x")

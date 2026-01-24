"""
Test to compare the original MatchingQueue traverse with the optimized In-Degree Tracking traverse.

This ensures the optimized algorithm produces equivalent results.
"""

import random
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest

from fides.api.common_exceptions import TraversalError, UnreachableNodesError
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


def create_random_graph(
    num_nodes: int,
    edge_probability: float = 0.3,
    after_probability: float = 0.1,
    rng_seed: Optional[int] = None,
    include_after_deps: bool = False,
) -> Tuple[DatasetGraph, Dict[str, Any]]:
    """Generate a random connected graph with configurable parameters.

    Uses a spanning tree approach to guarantee connectivity, then adds extra
    random edges based on edge_probability.

    Args:
        num_nodes: Number of collections/nodes to create (minimum 1)
        edge_probability: Probability of creating additional edges beyond the spanning tree
        after_probability: Probability of adding an 'after' dependency (only if include_after_deps=True)
        rng_seed: Random seed for reproducibility
        include_after_deps: Whether to include 'after' dependencies

    Returns:
        Tuple of (DatasetGraph, seed_data dict)
    """
    if num_nodes < 1:
        raise ValueError("num_nodes must be at least 1")

    rng = random.Random(rng_seed)

    # Track edges we'll create (from_node_idx -> to_node_idx)
    # These represent "from" direction edges: to_node references from_node
    spanning_tree_edges: List[Tuple[int, int]] = []
    extra_edges: List[Tuple[int, int]] = []

    # Build a random spanning tree to guarantee connectivity
    # Node 0 is always the root (has identity field)
    # Track parent in spanning tree for 'after' dependency validation
    spanning_tree_parent: Dict[int, int] = {}
    if num_nodes > 1:
        # For each node after 0, connect it to a random earlier node
        for i in range(1, num_nodes):
            parent = rng.randint(0, i - 1)
            spanning_tree_edges.append((parent, i))
            spanning_tree_parent[i] = parent

    # Build ancestors set for each node (for valid 'after' deps)
    def get_ancestors(node: int) -> Set[int]:
        """Get all ancestors of a node in the spanning tree."""
        ancestors: Set[int] = set()
        current = node
        while current in spanning_tree_parent:
            parent = spanning_tree_parent[current]
            ancestors.add(parent)
            current = parent
        return ancestors

    node_ancestors: Dict[int, Set[int]] = {i: get_ancestors(i) for i in range(num_nodes)}

    # Add extra random edges based on edge_probability
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            # Skip if this edge is already in the spanning tree
            if (i, j) in spanning_tree_edges or (j, i) in spanning_tree_edges:
                continue
            if rng.random() < edge_probability:
                # Randomly choose direction
                if rng.random() < 0.5:
                    extra_edges.append((i, j))
                else:
                    extra_edges.append((j, i))

    all_edges = spanning_tree_edges + extra_edges

    # Collect after dependencies for each node
    after_deps: Dict[int, Set[CollectionAddress]] = {i: set() for i in range(num_nodes)}

    if include_after_deps and num_nodes > 1:
        # Add random 'after' dependencies
        # IMPORTANT: Only add 'after' deps to DIRECT parents in the spanning tree
        # This ensures the 'after' target will always be visited before the
        # dependent node is discovered via edges, even with extra edges present.
        # Adding 'after' to non-parent ancestors can cause deadlocks when extra
        # edges create alternative discovery paths.
        for i in range(1, num_nodes):
            if i in spanning_tree_parent:
                parent = spanning_tree_parent[i]
                # Don't add after if there's already a direct edge (which there always is for parent)
                # So we skip this and only add to grandparents occasionally
                grandparent = spanning_tree_parent.get(parent)
                if grandparent is not None and rng.random() < after_probability:
                    # Only add 'after' to grandparent if there's no extra edge that could
                    # cause the node to be discovered before grandparent is visited
                    # Check if there's any edge from a non-ancestor to this node
                    has_shortcut_edge = any(
                        from_node not in node_ancestors[i] and from_node != spanning_tree_parent.get(i)
                        for from_node, to_node in extra_edges
                        if to_node == i
                    )
                    if not has_shortcut_edge:
                        after_deps[i].add(CollectionAddress(f"ds_{grandparent}", f"coll_{grandparent}"))

    # Create datasets
    datasets: List[GraphDataset] = []

    for i in range(num_nodes):
        fields = [
            ScalarField(name="id"),
            ScalarField(name="ref_id"),  # For incoming edges
            ScalarField(name="data"),
        ]

        # Node 0 always has the identity field
        if i == 0:
            fields[0].identity = "email"

        collection = Collection(
            name=f"coll_{i}",
            fields=fields,
            after=after_deps[i] if after_deps[i] else set(),
        )

        dataset = GraphDataset(
            name=f"ds_{i}",
            collections=[collection],
            connection_key=f"conn_{i}",
        )
        datasets.append(dataset)

    # Add edge references
    # Edge (from_idx, to_idx) means: to_node.ref_id references from_node.id with "from" direction
    for from_idx, to_idx in all_edges:
        for field in datasets[to_idx].collections[0].fields:
            if field.name == "ref_id":
                field.references.append(
                    (FieldAddress(f"ds_{from_idx}", f"coll_{from_idx}", "id"), "from")
                )
                break

    graph = DatasetGraph(*datasets)
    return graph, {"email": "test@example.com"}


def create_disconnected_graph(num_nodes: int) -> Tuple[DatasetGraph, Dict[str, Any]]:
    """Create a graph where some nodes are not reachable from the root.

    Node 0 has the identity field and is connected to nodes 1..num_nodes//2.
    Nodes num_nodes//2+1..num_nodes-1 are disconnected.

    Args:
        num_nodes: Total number of nodes (must be >= 3)

    Returns:
        Tuple of (DatasetGraph, seed_data dict)
    """
    if num_nodes < 3:
        raise ValueError("num_nodes must be at least 3 for disconnected graph")

    mid = num_nodes // 2

    datasets: List[GraphDataset] = []

    for i in range(num_nodes):
        fields = [
            ScalarField(name="id"),
            ScalarField(name="ref_id"),
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

    # Connect nodes 1..mid to node 0
    for i in range(1, mid + 1):
        for field in datasets[i].collections[0].fields:
            if field.name == "ref_id":
                field.references.append(
                    (FieldAddress("ds_0", "coll_0", "id"), "from")
                )
                break

    # Nodes mid+1..num_nodes-1 are connected to each other but not to the main graph
    if num_nodes > mid + 1:
        for i in range(mid + 2, num_nodes):
            for field in datasets[i].collections[0].fields:
                if field.name == "ref_id":
                    field.references.append(
                        (FieldAddress(f"ds_{mid+1}", f"coll_{mid+1}", "id"), "from")
                    )
                    break

    graph = DatasetGraph(*datasets)
    return graph, {"email": "test@example.com"}


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

    # Capture traversal details for each node
    traversal_details = capture_traversal_details(traversal_nodes)

    return {
        "visited_set": set(visited_order),
        "end_nodes": sorted([e.value for e in end_nodes]),
        "parent_child_map": parent_child_map,
        "node_count": len(traversal_nodes),
        "traversal_details": traversal_details,
    }


def capture_traversal_details(
    traversal_nodes: Dict[CollectionAddress, TraversalNode]
) -> Dict[str, Dict[str, Any]]:
    """Serialize full traversal details for each node.

    This captures the same information that would be persisted to RequestTask,
    enabling verification that both algorithms produce equivalent serialized results.

    Returns:
        Dict mapping node address strings to their serialized traversal details
    """
    result: Dict[str, Dict[str, Any]] = {}

    for addr, tn in traversal_nodes.items():
        details = tn.format_traversal_details_for_save()

        # Normalize for comparison (sort edges for order-independence)
        result[addr.value] = {
            "dataset_connection_key": details.get("dataset_connection_key"),
            "incoming_edges": sorted(details.get("incoming_edges", [])),
            "outgoing_edges": sorted(details.get("outgoing_edges", [])),
            "input_keys": sorted(details.get("input_keys", [])),
        }

    return result


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

    # Compare traversal details (serialized form)
    orig_details = original.get("traversal_details", {})
    opt_details = optimized.get("traversal_details", {})

    if set(orig_details.keys()) != set(opt_details.keys()):
        diffs.append(
            f"Traversal details nodes differ: "
            f"{set(orig_details.keys()).symmetric_difference(set(opt_details.keys()))}"
        )
    else:
        for node in orig_details.keys():
            orig_node = orig_details[node]
            opt_node = opt_details[node]

            if orig_node["incoming_edges"] != opt_node["incoming_edges"]:
                diffs.append(
                    f"Incoming edges for {node} differ: "
                    f"original={orig_node['incoming_edges']}, optimized={opt_node['incoming_edges']}"
                )

            if orig_node["outgoing_edges"] != opt_node["outgoing_edges"]:
                diffs.append(
                    f"Outgoing edges for {node} differ: "
                    f"original={orig_node['outgoing_edges']}, optimized={opt_node['outgoing_edges']}"
                )

            if orig_node["input_keys"] != opt_node["input_keys"]:
                diffs.append(
                    f"Input keys for {node} differ: "
                    f"original={orig_node['input_keys']}, optimized={opt_node['input_keys']}"
                )

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


def create_large_graph(
    num_datasets: int,
    collections_per_dataset: int,
) -> Tuple[DatasetGraph, Dict[str, Any]]:
    """Create a large graph with multiple datasets and collections.

    Creates a tree structure where:
    - First collection of first dataset has identity
    - Each subsequent collection references the previous one
    - Collections are chained within and across datasets

    Args:
        num_datasets: Number of datasets to create
        collections_per_dataset: Number of collections per dataset

    Returns:
        Tuple of (DatasetGraph, seed_data dict)
    """
    datasets: List[GraphDataset] = []
    total_collections = num_datasets * collections_per_dataset

    # Track the global collection index for edge creation
    global_idx = 0

    # Calculate log interval (log ~10 times during build)
    log_interval = max(1, num_datasets // 10)

    for ds_idx in range(num_datasets):
        # Log progress periodically
        if ds_idx > 0 and ds_idx % log_interval == 0:
            print(f"  Built {ds_idx:,}/{num_datasets:,} datasets "
                  f"({ds_idx * collections_per_dataset:,} collections)...", flush=True)

        collections: List[Collection] = []

        for coll_idx in range(collections_per_dataset):
            fields = [
                ScalarField(name="id"),
                ScalarField(name="ref_id"),
                ScalarField(name="data"),
            ]

            # First collection of first dataset has identity
            if ds_idx == 0 and coll_idx == 0:
                fields[0].identity = "email"
            else:
                # Reference the previous collection
                if coll_idx == 0:
                    # First collection in dataset references last collection of previous dataset
                    prev_ds = ds_idx - 1
                    prev_coll = collections_per_dataset - 1
                else:
                    # Reference previous collection in same dataset
                    prev_ds = ds_idx
                    prev_coll = coll_idx - 1

                fields[1].references.append(
                    (FieldAddress(f"ds_{prev_ds}", f"coll_{prev_coll}", "id"), "from")
                )

            collections.append(Collection(name=f"coll_{coll_idx}", fields=fields))
            global_idx += 1

        dataset = GraphDataset(
            name=f"ds_{ds_idx}",
            collections=collections,
            connection_key=f"conn_{ds_idx}",
        )
        datasets.append(dataset)

    graph = DatasetGraph(*datasets)
    return graph, {"email": "test@example.com"}


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

    def test_performance_large_graph(self):
        """
        Benchmark with 1,000,000 collections (1000 datasets x 1000 collections).

        This test runs ONLY the optimized O(N+E) algorithm to verify it can
        handle 1 million nodes efficiently. The legacy O(N²) algorithm would
        take hours at this scale.

        Run manually with: pytest -k test_performance_large_graph -s --no-cov
        """
        num_datasets = 1000
        collections_per_dataset = 1000
        total_collections = num_datasets * collections_per_dataset

        print(f"\n{'='*60}")
        print(f"LARGE SCALE BENCHMARK: {total_collections:,} collections")
        print(f"({num_datasets} datasets x {collections_per_dataset} collections each)")
        print(f"{'='*60}")

        # Build the graph
        print("\nBuilding graph...")
        start = time.perf_counter()
        graph, seed = create_large_graph(num_datasets, collections_per_dataset)
        build_time = time.perf_counter() - start
        print(f"Graph build time: {build_time:.2f}s")

        # Time optimized algorithm (should be fast even at 1M nodes)
        print("\nRunning OPTIMIZED algorithm (O(N+E))...")
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)
        traversal_nodes_opt: Dict[CollectionAddress, TraversalNode] = {}

        # Progress tracking
        nodes_processed = [0]  # Use list to allow mutation in closure
        traversal_start = time.perf_counter()
        log_interval = 10_000  # Log every 10k nodes

        def progress_callback(tn: TraversalNode, data: Dict) -> None:
            if tn.is_root_node():
                return
            # Add node to the result dict
            data[tn.address] = tn
            nodes_processed[0] += 1
            count = nodes_processed[0]
            # Log first node and then every log_interval nodes
            if count == 1 or count % log_interval == 0:
                elapsed = time.perf_counter() - traversal_start
                rate = count / elapsed if elapsed > 0 else 0
                remaining = (total_collections - count) / rate if rate > 0 else 0
                print(f"  Progress: {count:,}/{total_collections:,} nodes "
                      f"({count/total_collections*100:.1f}%) - "
                      f"{rate:,.0f} nodes/sec - ETA: {remaining:.1f}s", flush=True)

        start = time.perf_counter()
        end_nodes_opt = traversal_opt.traverse(
            traversal_nodes_opt,
            progress_callback
        )
        optimized_time = time.perf_counter() - start
        print(f"\nOptimized time: {optimized_time:.2f}s")
        print(f"Nodes visited: {len(traversal_nodes_opt):,}")

        # Results
        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Total collections:    {total_collections:,}")
        print(f"Optimized time:       {optimized_time:.2f}s")
        print(f"Time per node:        {optimized_time / total_collections * 1000:.6f}ms")
        print(f"Throughput:           {total_collections / optimized_time:,.0f} nodes/sec")

        # Verify all nodes were visited
        assert len(traversal_nodes_opt) == total_collections, \
            f"Expected {total_collections:,} nodes, got {len(traversal_nodes_opt):,}"

        print(f"\nSuccess: All {total_collections:,} nodes traversed correctly.")

    def test_performance_legacy_graph(self):
        """
        Benchmark the LEGACY O(N²) algorithm with a smaller graph.

        Uses 10,000 collections to demonstrate the polynomial scaling.
        At this size, the legacy algorithm should take noticeably longer
        than the optimized version.

        Run manually with: pytest -k test_performance_legacy_graph -s --no-cov
        """
        num_datasets = 100
        collections_per_dataset = 100
        total_collections = num_datasets * collections_per_dataset

        print(f"\n{'='*60}")
        print(f"LEGACY BENCHMARK: {total_collections:,} collections")
        print(f"({num_datasets} datasets x {collections_per_dataset} collections each)")
        print(f"{'='*60}")

        # Build the graph
        print("\nBuilding graph...")
        start = time.perf_counter()
        graph, seed = create_large_graph(num_datasets, collections_per_dataset)
        build_time = time.perf_counter() - start
        print(f"Graph build time: {build_time:.2f}s")

        # Time legacy algorithm
        print("\nRunning LEGACY algorithm (O(N²))...")
        traversal_legacy = BaseTraversal(graph, seed, skip_verification=True)
        traversal_nodes_legacy: Dict[CollectionAddress, TraversalNode] = {}

        # Progress tracking
        nodes_processed = [0]
        traversal_start = time.perf_counter()
        log_interval = 1_000  # Log every 1k nodes for legacy

        def progress_callback_legacy(tn: TraversalNode, data: Dict) -> None:
            if tn.is_root_node():
                return
            data[tn.address] = tn
            nodes_processed[0] += 1
            count = nodes_processed[0]
            if count == 1 or count % log_interval == 0:
                elapsed = time.perf_counter() - traversal_start
                rate = count / elapsed if elapsed > 0 else 0
                remaining = (total_collections - count) / rate if rate > 0 else 0
                print(f"  Progress: {count:,}/{total_collections:,} nodes "
                      f"({count/total_collections*100:.1f}%) - "
                      f"{rate:,.0f} nodes/sec - ETA: {remaining:.1f}s", flush=True)

        start = time.perf_counter()
        end_nodes_legacy = traversal_legacy._traverse_legacy(
            traversal_nodes_legacy,
            progress_callback_legacy
        )
        legacy_time = time.perf_counter() - start
        print(f"\nLegacy time: {legacy_time:.2f}s")
        print(f"Nodes visited: {len(traversal_nodes_legacy):,}")

        # Now run optimized for comparison
        print("\nRunning OPTIMIZED algorithm (O(N+E)) for comparison...")
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)
        traversal_nodes_opt: Dict[CollectionAddress, TraversalNode] = {}

        nodes_processed[0] = 0
        traversal_start = time.perf_counter()

        def progress_callback_opt(tn: TraversalNode, data: Dict) -> None:
            if tn.is_root_node():
                return
            data[tn.address] = tn
            nodes_processed[0] += 1
            count = nodes_processed[0]
            if count == 1 or count % log_interval == 0:
                elapsed = time.perf_counter() - traversal_start
                rate = count / elapsed if elapsed > 0 else 0
                remaining = (total_collections - count) / rate if rate > 0 else 0
                print(f"  Progress: {count:,}/{total_collections:,} nodes "
                      f"({count/total_collections*100:.1f}%) - "
                      f"{rate:,.0f} nodes/sec - ETA: {remaining:.1f}s", flush=True)

        start = time.perf_counter()
        end_nodes_opt = traversal_opt.traverse(
            traversal_nodes_opt,
            progress_callback_opt
        )
        optimized_time = time.perf_counter() - start
        print(f"\nOptimized time: {optimized_time:.2f}s")
        print(f"Nodes visited: {len(traversal_nodes_opt):,}")

        # Results
        print(f"\n{'='*60}")
        print("RESULTS COMPARISON")
        print(f"{'='*60}")
        print(f"Total collections:    {total_collections:,}")
        print(f"Legacy time:          {legacy_time:.2f}s")
        print(f"Optimized time:       {optimized_time:.2f}s")
        print(f"Speedup:              {legacy_time / optimized_time:.1f}x")
        print(f"Legacy per node:      {legacy_time / total_collections * 1000:.4f}ms")
        print(f"Optimized per node:   {optimized_time / total_collections * 1000:.4f}ms")

        # Verify both visited all nodes
        assert len(traversal_nodes_legacy) == total_collections, \
            f"Legacy: Expected {total_collections:,} nodes, got {len(traversal_nodes_legacy):,}"
        assert len(traversal_nodes_opt) == total_collections, \
            f"Optimized: Expected {total_collections:,} nodes, got {len(traversal_nodes_opt):,}"

        print(f"\nSuccess: Both algorithms traversed all {total_collections:,} nodes correctly.")

    def test_extrapolate_legacy_to_million(self):
        """
        Run legacy algorithm at multiple sizes and extrapolate to 1 million nodes.

        Uses polynomial curve fitting to predict how long the O(N²) legacy
        algorithm would take at 1 million nodes without actually running it.

        Run manually with: pytest -k test_extrapolate_legacy_to_million -s --no-cov
        """
        # Test sizes - small enough to complete quickly
        test_sizes = [500, 1000, 2000, 3000, 5000]
        legacy_times: List[float] = []
        optimized_times: List[float] = []

        print(f"\n{'='*70}")
        print("TIMING ANALYSIS: Extrapolating Legacy Performance to 1M Nodes")
        print(f"{'='*70}")

        for size in test_sizes:
            # Use a single dataset with 'size' collections for simplicity
            print(f"\n--- Testing with {size:,} nodes ---")

            # Build graph
            graph, seed = create_linear_chain(size)

            # Time legacy
            traversal_legacy = BaseTraversal(graph, seed, skip_verification=True)
            traversal_nodes_legacy: Dict[CollectionAddress, TraversalNode] = {}

            def capture_fn(tn: TraversalNode, data: Dict) -> None:
                if not tn.is_root_node():
                    data[tn.address] = tn

            start = time.perf_counter()
            traversal_legacy._traverse_legacy(traversal_nodes_legacy, capture_fn)
            legacy_time = time.perf_counter() - start
            legacy_times.append(legacy_time)

            # Time optimized
            traversal_opt = BaseTraversal(graph, seed, skip_verification=True)
            traversal_nodes_opt: Dict[CollectionAddress, TraversalNode] = {}

            start = time.perf_counter()
            traversal_opt.traverse(traversal_nodes_opt, capture_fn)
            optimized_time = time.perf_counter() - start
            optimized_times.append(optimized_time)

            print(f"  Legacy:    {legacy_time:.4f}s ({legacy_time/size*1000:.4f}ms/node)")
            print(f"  Optimized: {optimized_time:.4f}s ({optimized_time/size*1000:.4f}ms/node)")
            print(f"  Speedup:   {legacy_time/optimized_time:.1f}x")

        # Fit quadratic curve for legacy: time = a * n^2 + b * n + c
        # Using numpy-free approach: least squares for t = k * n^2
        # Since O(N²) dominates, we fit t = k * n^2
        print(f"\n{'='*70}")
        print("CURVE FITTING")
        print(f"{'='*70}")

        # Calculate k for legacy (t = k * n^2)
        # Using least squares: k = sum(t_i * n_i^2) / sum(n_i^4)
        sum_tn2 = sum(t * (n ** 2) for t, n in zip(legacy_times, test_sizes))
        sum_n4 = sum(n ** 4 for n in test_sizes)
        k_legacy = sum_tn2 / sum_n4

        # Calculate k for optimized (t = k * n, linear)
        sum_tn = sum(t * n for t, n in zip(optimized_times, test_sizes))
        sum_n2 = sum(n ** 2 for n in test_sizes)
        k_optimized = sum_tn / sum_n2

        print(f"\nLegacy fit:    t = {k_legacy:.2e} * n²")
        print(f"Optimized fit: t = {k_optimized:.2e} * n")

        # Verify fit quality
        print(f"\nFit Quality (predicted vs actual):")
        print(f"{'Size':>8} | {'Legacy Actual':>12} | {'Legacy Pred':>12} | {'Opt Actual':>10} | {'Opt Pred':>10}")
        print("-" * 70)
        for i, size in enumerate(test_sizes):
            legacy_pred = k_legacy * (size ** 2)
            opt_pred = k_optimized * size
            print(f"{size:>8,} | {legacy_times[i]:>12.4f}s | {legacy_pred:>12.4f}s | {optimized_times[i]:>10.4f}s | {opt_pred:>10.4f}s")

        # Extrapolate to 1 million
        target_size = 1_000_000
        legacy_predicted = k_legacy * (target_size ** 2)
        optimized_predicted = k_optimized * target_size

        print(f"\n{'='*70}")
        print(f"EXTRAPOLATION TO {target_size:,} NODES")
        print(f"{'='*70}")

        # Convert to human-readable time
        def format_time(seconds: float) -> str:
            if seconds < 60:
                return f"{seconds:.1f} seconds"
            elif seconds < 3600:
                return f"{seconds/60:.1f} minutes"
            elif seconds < 86400:
                return f"{seconds/3600:.1f} hours"
            else:
                return f"{seconds/86400:.1f} days"

        print(f"\nLegacy algorithm (O(N²)):")
        print(f"  Predicted time: {format_time(legacy_predicted)} ({legacy_predicted:,.0f} seconds)")

        print(f"\nOptimized algorithm (O(N+E)):")
        print(f"  Predicted time: {format_time(optimized_predicted)} ({optimized_predicted:.1f} seconds)")

        print(f"\nPredicted speedup at 1M nodes: {legacy_predicted/optimized_predicted:,.0f}x")

        # Show scaling comparison
        print(f"\n{'='*70}")
        print("SCALING COMPARISON")
        print(f"{'='*70}")
        comparison_sizes = [1000, 10000, 100000, 1000000]
        print(f"{'Nodes':>12} | {'Legacy':>15} | {'Optimized':>12} | {'Speedup':>10}")
        print("-" * 60)
        for n in comparison_sizes:
            leg_time = k_legacy * (n ** 2)
            opt_time = k_optimized * n
            speedup = leg_time / opt_time
            print(f"{n:>12,} | {format_time(leg_time):>15} | {format_time(opt_time):>12} | {speedup:>10,.0f}x")

        print(f"\nConclusion: The legacy O(N²) algorithm would take approximately")
        print(f"{format_time(legacy_predicted)} for 1 million nodes,")
        print(f"while the optimized O(N+E) algorithm takes {format_time(optimized_predicted)}.")


class TestScalabilityComparison:
    """Test how algorithms scale with increasing graph size."""

    @pytest.mark.parametrize("size", [100, 500, 1000, 2000, 5000])
    def test_scaling_comparison(self, size: int):
        """Compare algorithm scaling at different sizes."""
        graph, seed = create_linear_chain(size)

        # Time legacy
        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        start = time.perf_counter()
        traversal_orig._traverse_legacy({}, lambda tn, data: None)
        legacy_time = time.perf_counter() - start

        # Time optimized
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)
        start = time.perf_counter()
        traversal_opt.traverse({}, lambda tn, data: None)
        optimized_time = time.perf_counter() - start

        speedup = legacy_time / optimized_time if optimized_time > 0 else float('inf')

        print(f"\nSize {size:5d}: Legacy={legacy_time:.4f}s, Optimized={optimized_time:.4f}s, Speedup={speedup:.1f}x")


class TestRandomGraphEquivalence:
    """Test equivalence on randomly generated graphs."""

    @pytest.mark.parametrize("rng_seed", range(10))
    def test_random_small_graphs(self, rng_seed: int):
        """Test 10 random graphs with 5-15 nodes."""
        rng = random.Random(rng_seed)
        num_nodes = rng.randint(5, 15)

        graph, seed = create_random_graph(
            num_nodes=num_nodes,
            edge_probability=0.3,
            rng_seed=rng_seed,
        )

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ for seed={rng_seed}, nodes={num_nodes}:\n{diff}"

    @pytest.mark.parametrize("rng_seed", range(5))
    def test_random_medium_graphs(self, rng_seed: int):
        """Test 5 random graphs with 50-100 nodes."""
        rng = random.Random(rng_seed + 100)  # Offset to get different graphs
        num_nodes = rng.randint(50, 100)

        graph, seed = create_random_graph(
            num_nodes=num_nodes,
            edge_probability=0.2,
            rng_seed=rng_seed + 100,
        )

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ for seed={rng_seed + 100}, nodes={num_nodes}:\n{diff}"

    @pytest.mark.parametrize("rng_seed", range(5))
    def test_random_with_after_deps(self, rng_seed: int):
        """Test random graphs with 'after' dependencies."""
        rng = random.Random(rng_seed + 200)
        num_nodes = rng.randint(10, 30)

        graph, seed = create_random_graph(
            num_nodes=num_nodes,
            edge_probability=0.25,
            after_probability=0.15,
            rng_seed=rng_seed + 200,
            include_after_deps=True,
        )

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ for seed={rng_seed + 200}, nodes={num_nodes}:\n{diff}"

    @pytest.mark.parametrize("rng_seed", range(5))
    def test_random_dense_graphs(self, rng_seed: int):
        """Test random graphs with high edge probability (0.7)."""
        rng = random.Random(rng_seed + 300)
        num_nodes = rng.randint(10, 25)

        graph, seed = create_random_graph(
            num_nodes=num_nodes,
            edge_probability=0.7,
            rng_seed=rng_seed + 300,
        )

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ for seed={rng_seed + 300}, nodes={num_nodes}:\n{diff}"

    @pytest.mark.parametrize("rng_seed", range(5))
    def test_random_sparse_graphs(self, rng_seed: int):
        """Test random graphs with low edge probability (0.05)."""
        rng = random.Random(rng_seed + 400)
        num_nodes = rng.randint(15, 40)

        graph, seed = create_random_graph(
            num_nodes=num_nodes,
            edge_probability=0.05,
            rng_seed=rng_seed + 400,
        )

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ for seed={rng_seed + 400}, nodes={num_nodes}:\n{diff}"

    def test_single_node_graph(self):
        """Test graph with only one node (edge case)."""
        graph, seed = create_random_graph(num_nodes=1, rng_seed=999)

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ for single node graph:\n{diff}"

    def test_two_node_graph(self):
        """Test graph with only two nodes (edge case)."""
        graph, seed = create_random_graph(num_nodes=2, rng_seed=998)

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        original = capture_traversal(traversal_orig, use_optimized=False)
        optimized = capture_traversal(traversal_opt, use_optimized=True)

        match, diff = results_equivalent(original, optimized)
        assert match, f"Results differ for two node graph:\n{diff}"


class TestTraversalErrorEquivalence:
    """Test that both algorithms raise the same errors for invalid graphs."""

    def test_disconnected_graph_raises_unreachable_nodes_error(self):
        """Both algorithms should raise UnreachableNodesError for disconnected graphs."""
        graph, seed = create_disconnected_graph(num_nodes=6)

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        # Test legacy algorithm raises error
        orig_error: Optional[UnreachableNodesError] = None
        try:
            traversal_orig._traverse_legacy({}, lambda tn, data: None)
        except UnreachableNodesError as e:
            orig_error = e

        # Test optimized algorithm raises error
        opt_error: Optional[UnreachableNodesError] = None
        try:
            traversal_opt.traverse({}, lambda tn, data: None)
        except UnreachableNodesError as e:
            opt_error = e

        # Both should raise the same type of error
        assert orig_error is not None, "Legacy algorithm should raise UnreachableNodesError"
        assert opt_error is not None, "Optimized algorithm should raise UnreachableNodesError"

        # The unreachable nodes should be the same (as sets, order may differ)
        assert set(orig_error.errors) == set(opt_error.errors), (
            f"Unreachable nodes differ: original={orig_error.errors}, optimized={opt_error.errors}"
        )

    @pytest.mark.parametrize("num_nodes", [4, 6, 10])
    def test_disconnected_graph_error_consistency(self, num_nodes: int):
        """Test error consistency across different disconnected graph sizes."""
        graph, seed = create_disconnected_graph(num_nodes=num_nodes)

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        orig_error: Optional[Exception] = None
        opt_error: Optional[Exception] = None

        try:
            traversal_orig._traverse_legacy({}, lambda tn, data: None)
        except (UnreachableNodesError, TraversalError) as e:
            orig_error = e

        try:
            traversal_opt.traverse({}, lambda tn, data: None)
        except (UnreachableNodesError, TraversalError) as e:
            opt_error = e

        # Both should raise errors
        assert orig_error is not None, f"Legacy should raise error for {num_nodes} nodes"
        assert opt_error is not None, f"Optimized should raise error for {num_nodes} nodes"

        # Error types should match
        assert type(orig_error) == type(opt_error), (
            f"Error types differ: original={type(orig_error)}, optimized={type(opt_error)}"
        )

        # If both are UnreachableNodesError, compare the unreachable nodes
        if isinstance(orig_error, UnreachableNodesError) and isinstance(
            opt_error, UnreachableNodesError
        ):
            assert set(orig_error.errors) == set(opt_error.errors), (
                f"Unreachable nodes differ for {num_nodes} nodes: "
                f"original={orig_error.errors}, optimized={opt_error.errors}"
            )

    def test_connected_graph_no_error(self):
        """Verify that connected random graphs don't raise errors in either algorithm."""
        graph, seed = create_random_graph(num_nodes=20, edge_probability=0.3, rng_seed=12345)

        traversal_orig = BaseTraversal(graph, seed, skip_verification=True)
        traversal_opt = BaseTraversal(graph, seed, skip_verification=True)

        # Neither should raise an error
        try:
            traversal_orig._traverse_legacy({}, lambda tn, data: None)
        except (UnreachableNodesError, TraversalError) as e:
            pytest.fail(f"Legacy algorithm unexpectedly raised: {e}")

        try:
            traversal_opt.traverse({}, lambda tn, data: None)
        except (UnreachableNodesError, TraversalError) as e:
            pytest.fail(f"Optimized algorithm unexpectedly raised: {e}")

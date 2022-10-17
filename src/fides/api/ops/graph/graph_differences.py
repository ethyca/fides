from typing import TYPE_CHECKING, Dict, List, Optional, Set

from fides.api.ops.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.ops.schemas.base_class import BaseSchema
from fides.api.ops.util.collection_util import Row

if TYPE_CHECKING:
    from fides.api.ops.task.graph_task import GraphTask

GraphRepr = Dict[str, Dict[str, List[str]]]


def format_graph_for_caching(
    env: Dict[CollectionAddress, "GraphTask"], end_nodes: List[CollectionAddress]
) -> GraphRepr:
    """
    Builds a representation of the current graph built for a privacy request (that includes its edges)
    for caching in Redis.

    Requires the results of traversal.traverse():
        - the modified `env`
        - and the outputted end_nodes, which are the final nodes without children

    Maps collections to their upstream dependencies and associated edges. The root is stored as having
    no upstream collections and the terminator collection has no incoming edges.

    Example:
    {
       <collection>: {
          <upstream collection>: [edge between upstream and current],
          <another upstream collection>: [edge between another upstream and current]
       },
       <root collection>: {},
       <terminator collection>: {
            <end collection>: [],
            <end collection>: []
       }
    }
    """
    graph_repr: GraphRepr = {
        collection.value: {
            upstream_collection_address.value: [str(edge) for edge in edge_list]
            for upstream_collection_address, edge_list in g_task.incoming_edges_by_collection.items()
        }
        for collection, g_task in env.items()
    }
    graph_repr[ROOT_COLLECTION_ADDRESS.value] = {}
    graph_repr[TERMINATOR_ADDRESS.value] = {
        end_node.value: [] for end_node in end_nodes
    }

    return graph_repr


class GraphDiff(BaseSchema):
    """A more detailed description about how two graphs differ. Do not send these details to FidesLog."""

    previous_collections: List[str] = []
    current_collections: List[str] = []
    added_collections: List[str] = []
    removed_collections: List[str] = []
    added_edges: List[str] = []
    removed_edges: List[str] = []
    already_processed_access_collections: List[str] = []
    already_processed_erasure_collections: List[str] = []
    skipped_added_edges: List[str] = []


class GraphDiffSummary(BaseSchema):
    """A summary about how two graphs have changed. This can be sent to FidesLog."""

    prev_collection_count: int = 0
    curr_collection_count: int = 0
    added_collection_count: int = 0
    removed_collection_count: int = 0
    added_edge_count: int = 0
    removed_edge_count: int = 0
    already_processed_access_collection_count: int = 0
    already_processed_erasure_collection_count: int = 0
    skipped_added_edge_count: int = 0


artificial_collections: Set[str] = {
    ROOT_COLLECTION_ADDRESS.value,
    TERMINATOR_ADDRESS.value,
}


def get_skipped_added_edges(
    already_processed_access_collections: List[str],
    current_graph: GraphRepr,
    added_edges: List[str],
) -> List[str]:
    """
    Gets newly added edges *directly* upstream of an already-processed collection.

    Already-processed collections have their immediate upstream edges removed from the graph
    when we reprocess an access portion of the request.  We don't re-query collections that were already run:
    we use saved incoming results from last time.
    """
    added_upstream_edges: List[str] = []

    for collection in already_processed_access_collections:
        for _, upstream_edges in current_graph[collection].items():
            for edge in upstream_edges:
                if edge in added_edges:
                    added_upstream_edges.append(edge)
    return added_upstream_edges


def _find_graph_differences(
    previous_graph: Optional[GraphRepr],
    current_graph: GraphRepr,
    previous_results: Dict[str, Optional[List[Row]]],
    previous_erasure_results: Dict[str, int],
) -> Optional[GraphDiff]:
    """
    Determine how/if a graph has changed from the previous run when a privacy request is reprocessed.

    Takes in the previous graph, the current graph, and any collections that already ran the first time (previous_results).
    Where applicable, we also take in the erasure collections that have already run.  The current design doesn't run
    the access request on a collection or the erasure portion of the collection more than once.
    """
    if not previous_graph:
        return None

    def all_edges(graph: GraphRepr) -> Set[str]:
        edge_list: List[str] = []
        for _, dependent_collections in graph.items():
            for _, edges in dependent_collections.items():
                if edges:
                    edge_list.extend(edges)
        return set(edge_list)

    current_collections: Set[str] = (
        set(list(current_graph.keys())) - artificial_collections
    )
    current_edges: Set[str] = all_edges(current_graph)
    previous_collections: Set[str] = (
        set(list(previous_graph.keys())) - artificial_collections
    )
    previous_edges: Set[str] = all_edges(previous_graph)

    added_collections: List[str] = list(current_collections - previous_collections)
    added_edges: List[str] = list(current_edges - previous_edges)
    removed_collections: List[str] = list(previous_collections - current_collections)
    removed_edges: List[str] = list(previous_edges - current_edges)

    already_processed_access_collections = list(previous_results.keys())
    skipped_added_edges: List[str] = get_skipped_added_edges(
        already_processed_access_collections, current_graph, added_edges
    )

    already_processed_erasure_collections = list(previous_erasure_results.keys())

    return GraphDiff(
        previous_collections=list(sorted(previous_collections)),
        current_collections=list(sorted(current_collections)),
        added_collections=sorted(added_collections),
        removed_collections=sorted(removed_collections),
        added_edges=sorted(added_edges),
        removed_edges=sorted(removed_edges),
        already_processed_access_collections=sorted(
            already_processed_access_collections
        ),
        already_processed_erasure_collections=sorted(
            already_processed_erasure_collections
        ),
        skipped_added_edges=sorted(skipped_added_edges),
    )


def find_graph_differences_summary(
    previous_graph: Optional[GraphRepr],
    current_graph: GraphRepr,
    previous_results: Dict[str, Optional[List[Row]]],
    previous_erasure_results: Dict[str, int],
) -> Optional[GraphDiffSummary]:
    """
    Summarizes the differences between the current graph and previous graph
    with a series of counts.
    """
    graph_diff: Optional[GraphDiff] = _find_graph_differences(
        previous_graph, current_graph, previous_results, previous_erasure_results
    )

    if not graph_diff:
        return None

    return GraphDiffSummary(
        prev_collection_count=len(graph_diff.previous_collections),
        curr_collection_count=len(graph_diff.current_collections),
        added_collection_count=len(graph_diff.added_collections),
        removed_collection_count=len(graph_diff.removed_collections),
        added_edge_count=len(graph_diff.added_edges),
        removed_edge_count=len(graph_diff.removed_edges),
        already_processed_access_collection_count=len(
            graph_diff.already_processed_access_collections
        ),
        already_processed_erasure_collection_count=len(
            graph_diff.already_processed_erasure_collections
        ),
        skipped_added_edge_count=len(graph_diff.skipped_added_edges),
    )

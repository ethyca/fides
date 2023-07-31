"""Utilities used when building Graphs."""
from typing import Any, Callable, Dict, List, Optional, Tuple

from fides.api.privacy_requests.graph.config import CollectionAddress
from fides.api.privacy_requests.graph.traversal import Traversal, TraversalNode
from fides.api.privacy_requests.graph_tasks.graph_task import GraphTask
from fides.api.privacy_requests.graph_tasks.task_resources import TaskResources
from fides.api.util.cache import get_cache
from fides.api.util.collection_util import Row, extract_key_for_address


def collect_queries(
    traversal: Traversal, resources: TaskResources
) -> Dict[CollectionAddress, str]:
    """Collect all queries for dry-run"""

    def collect_queries_fn(
        tn: TraversalNode, data: Dict[CollectionAddress, str]
    ) -> None:
        if not tn.is_root_node():
            data[tn.address] = GraphTask(tn, resources).generate_dry_run_query()  # type: ignore

    env: Dict[CollectionAddress, str] = {}
    traversal.traverse(env, collect_queries_fn)
    return env


def update_mapping_from_cache(
    dsk: Dict[CollectionAddress, Tuple[Any, ...]],
    resources: TaskResources,
    start_fn: Callable,
) -> None:
    """When resuming a privacy request from a paused or failed state, update the `dsk` dictionary with results we've
    already obtained from a previous run. Remove upstream dependencies for these nodes, and just return the data we've
    already retrieved, rather than visiting them again.

    If there's no cached data, the dsk dictionary won't change.
    """

    cached_results: Dict[str, Optional[List[Row]]] = resources.get_all_cached_objects()

    for collection_name in cached_results:
        dsk[CollectionAddress.from_string(collection_name)] = (
            start_fn(cached_results[collection_name]),
        )


def get_cached_data_for_erasures(
    privacy_request_id: str,
) -> Dict[str, Any]:
    """
    Fetches processed access request results to be used for erasures.

    Processing may have added indicators to not mask certain elements in array data.
    """
    cache = get_cache()
    value_dict = cache.get_encoded_objects_by_prefix(
        f"PLACEHOLDER_RESULTS__{privacy_request_id}"
    )
    number_of_leading_strings_to_exclude = 3
    return {
        extract_key_for_address(k, number_of_leading_strings_to_exclude): v
        for k, v in value_dict.items()
    }

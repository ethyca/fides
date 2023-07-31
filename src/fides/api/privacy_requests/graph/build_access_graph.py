"""
Build Privacy Request graphs.
"""
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.privacy_requests.graph.analytics_events import (
    fideslog_graph_rerun,
    prepare_rerun_graph_analytics_event,
)
from fides.api.privacy_requests.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.privacy_requests.graph.graph import DatasetGraph
from fides.api.privacy_requests.graph.graph_differences import format_graph_for_caching
from fides.api.privacy_requests.graph.traversal import Traversal, TraversalNode
from fides.api.privacy_requests.graph.utils import update_mapping_from_cache
from fides.api.privacy_requests.graph_tasks.graph_task import GraphTask
from fides.api.privacy_requests.graph_tasks.task_resources import TaskResources
from fides.api.schemas.policy import ActionType
from fides.api.util.collection_util import Row


def _format_data_use_map_for_caching(
    env: Dict[CollectionAddress, "GraphTask"]
) -> Dict[str, Set[str]]:
    """
    Create a map of `Collection`s mapped to their associated `DataUse`s
    to be stored in the cache. This is done before request execution, so that we
    maintain the _original_ state of the graph as it's used for request execution.
    The graph is subject to change "from underneath" the request execution runtime,
    but we want to avoid picking up those changes in our data use map.

    `DataUse`s are associated with a `Collection` by means of the `System`
    that's linked to a `Collection`'s `Connection` definition.

    Example:
    {
       <collection1>: {"data_use_1", "data_use_2"},
       <collection2>: {"data_use_1"},
    }
    """
    return {collection.value: g_task.data_uses for collection, g_task in env.items()}


def start_function(seed: List[Dict[str, Any]]) -> Callable[[], List[Dict[str, Any]]]:
    """Return a function for collections with no upstream dependencies, that just start
    with seed data.

    This is used for root nodes or previously-visited nodes on restart."""

    def g() -> List[Dict[str, Any]]:
        return seed

    return g


async def build_access_graph(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
) -> Dict[CollectionAddress, Tuple[Any, ...]]:
    """Build an access request Graph."""
    traversal: Traversal = Traversal(graph, identity)
    with TaskResources(
        privacy_request, policy, connection_configs, session
    ) as resources:

        def collect_tasks_fn(
            tn: TraversalNode, data: Dict[CollectionAddress, GraphTask]
        ) -> None:
            """Run the traversal, as an action creating a GraphTask for each traversal_node."""
            if not tn.is_root_node():
                data[tn.address] = GraphTask(tn, resources)

        def termination_fn(
            *dependent_values: List[Row],
        ) -> Dict[str, Optional[List[Row]]]:
            """A termination function that just returns its inputs mapped to their source addresses.
            This needs to wait for all dependent keys because this is how dask is informed to wait for
            all terminating addresses before calling this."""

            return resources.get_all_cached_objects()

        env: Dict[CollectionAddress, Any] = {}
        end_nodes = traversal.traverse(env, collect_tasks_fn)

        dsk: Dict[CollectionAddress, Tuple[Any, ...]] = {
            k: (t.access_request, *t.input_keys) for k, t in env.items()
        }
        dsk[ROOT_COLLECTION_ADDRESS] = (start_function([traversal.seed_data]),)
        dsk[TERMINATOR_ADDRESS] = (termination_fn, *end_nodes)
        update_mapping_from_cache(dsk, resources, start_function)

        await fideslog_graph_rerun(
            prepare_rerun_graph_analytics_event(
                privacy_request, env, end_nodes, resources, ActionType.access
            )
        )

        # cache access graph for use in logging/analytics event
        privacy_request.cache_access_graph(format_graph_for_caching(env, end_nodes))

        # cache a map of collections -> data uses for the output package of access requests
        # this is cached here before request execution, since this is the state of the
        # graph used for request execution. the graph could change _during_ request execution,
        # but we don't want those changes in our data use map.
        privacy_request.cache_data_use_map(_format_data_use_map_for_caching(env))

        return dsk

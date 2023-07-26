"""
Build Privacy Request graphs.
"""
from typing import Any, Dict, List, Set, Tuple, Union

from dask.core import getcycle
from sqlalchemy.orm import Session

from fides.api.common_exceptions import TraversalError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.util.collection_util import Row
from fides.privacy_requests.graph.analytics_events import (
    fideslog_graph_rerun,
    prepare_rerun_graph_analytics_event,
)
from fides.privacy_requests.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.privacy_requests.graph.graph import DatasetGraph
from fides.privacy_requests.graph.traversal import Traversal, TraversalNode
from fides.privacy_requests.graph_tasks.graph_task import GraphTask
from fides.privacy_requests.graph_tasks.task_resources import TaskResources


def _evaluate_erasure_dependencies(
    t: GraphTask, end_nodes: List[CollectionAddress]
) -> Set[CollectionAddress]:
    """
    Return a set of collection addresses corresponding to collections that need
    to be erased before the given task. Remove the dependent collection addresses
    from `end_nodes` so they can be executed in the correct order. If a task does
    not have any dependencies it is linked directly to the root node
    """
    erase_after = t.traversal_node.node.collection.erase_after
    for collection in erase_after:
        if collection in end_nodes:
            # end_node list is modified in place
            end_nodes.remove(collection)
    # this task will execute after the collections in `erase_after` or
    # execute at the beginning by linking it to the root node
    return erase_after if len(erase_after) else {ROOT_COLLECTION_ADDRESS}


def update_erasure_mapping_from_cache(
    dsk: Dict[CollectionAddress, Union[Tuple[Any, ...], int]], resources: TaskResources
) -> None:
    """On pause or restart from failure, update the dsk graph to skip running erasures on collections
    we've already visited. Instead, just return the previous count of rows affected.

    If there's no cached data, the dsk dictionary won't change.
    """
    cached_erasures: Dict[str, int] = resources.get_all_cached_erasures()

    for collection_name in cached_erasures:
        dsk[CollectionAddress.from_string(collection_name)] = cached_erasures[
            collection_name
        ]


async def build_erasure_graph(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    access_request_data: Dict[str, List[Row]],
    session: Session,
) -> Dict[CollectionAddress, Any]:
    """Build an erasure request"""
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

        # We store the end nodes from the traversal for analytics purposes
        # but we generate a separate erasure_end_nodes list for the actual erasure traversal
        env: Dict[CollectionAddress, Any] = {}
        access_end_nodes = traversal.traverse(env, collect_tasks_fn)
        erasure_end_nodes = list(graph.nodes.keys())

        def termination_fn(*dependent_values: int) -> Dict[str, int]:
            """
            The erasure order can be affected in a way that not every node is directly linked
            to the termination node. This means that we can't just aggregate the inputs directly,
            we must read the erasure results from the cache.
            """
            return resources.get_all_cached_erasures()

        access_request_data[ROOT_COLLECTION_ADDRESS.value] = [identity]

        dsk: Dict[CollectionAddress, Any] = {
            k: (
                t.erasure_request,
                access_request_data.get(
                    str(k), []
                ),  # Pass in the results of the access request for this collection
                [
                    access_request_data.get(
                        str(upstream_key), []
                    )  # Additionally pass in the original input data we used for the access request. It's helpful in
                    # cases like the EmailConnector where the access request doesn't actually retrieve data.
                    for upstream_key in t.input_keys
                ],
                *_evaluate_erasure_dependencies(t, erasure_end_nodes),
            )
            for k, t in env.items()
        }

        # root node returns 0 to be consistent with the output of the other erasure tasks
        dsk[ROOT_COLLECTION_ADDRESS] = 0
        # terminator function reads and returns the cached erasure results for the entire erasure traversal
        dsk[TERMINATOR_ADDRESS] = (termination_fn, *erasure_end_nodes)
        update_erasure_mapping_from_cache(dsk, resources)
        await fideslog_graph_rerun(
            prepare_rerun_graph_analytics_event(
                privacy_request, env, access_end_nodes, resources, ActionType.erasure
            )
        )

        # using an existing function from dask.core to detect cycles in the generated graph
        collection_cycle = getcycle(dsk, None)
        if collection_cycle:
            raise TraversalError(
                f"The values for the `erase_after` fields caused a cycle in the following collections {collection_cycle}"
            )

        return dsk

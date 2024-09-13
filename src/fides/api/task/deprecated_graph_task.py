# pylint: disable=too-many-lines
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import dask
from dask import delayed  # type: ignore[attr-defined]
from dask.core import getcycle
from dask.threaded import get
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import TraversalError
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import (
    Traversal,
    TraversalNode,
    log_traversal_error_and_update_privacy_request,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.schemas.policy import ActionType
from fides.api.task.graph_task import EMPTY_REQUEST_TASK, GraphTask
from fides.api.task.task_resources import TaskResources
from fides.api.util.collection_util import Row

# These are deprecated DSR 2.0 functions that support running DSR's in sequence with Dask in-memory
# Supported for a limited time.

dask.config.set(scheduler="threads")


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


def format_data_use_map_for_caching(
    connection_key_mapping: Dict[CollectionAddress, str],
    connection_configs: List[ConnectionConfig],
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
    resp: Dict[str, Set[str]] = {}
    connection_config_mapping: Dict[str, ConnectionConfig] = {
        connection_config.key: connection_config
        for connection_config in connection_configs
    }
    for collection_addr, connection_key in connection_key_mapping.items():
        connection_config = connection_config_mapping.get(connection_key, None)
        if not connection_config or not connection_config.system:
            resp[collection_addr.value] = set()
            continue
        data_uses: Set[str] = System.get_data_uses(
            [connection_config.system], include_parents=False
        )
        resp[collection_addr.value] = data_uses

    return resp


def start_function(seed: List[Dict[str, Any]]) -> Callable[[], List[Dict[str, Any]]]:
    """Return a function for collections with no upstream dependencies, that just start
    with seed data.

    This is used for root nodes or previously-visited nodes on restart."""

    def g() -> List[Dict[str, Any]]:
        return seed

    return g


def run_access_request_deprecated(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
) -> Dict[str, List[Row]]:
    """Deprecated: Run the access request sequentially in-memory using Dask"""
    try:
        traversal: Traversal = Traversal(graph, identity)
    except TraversalError as err:
        log_traversal_error_and_update_privacy_request(privacy_request, session, err)
        raise err

    with TaskResources(
        privacy_request, policy, connection_configs, EMPTY_REQUEST_TASK, session
    ) as resources:

        def collect_tasks_fn(
            tn: TraversalNode, data: Dict[CollectionAddress, GraphTask]
        ) -> None:
            """Run the traversal, as an action creating a GraphTask for each traversal_node."""
            if not tn.is_root_node():
                # Mock a RequestTask object in memory to share code with DSR 3.0
                resources.privacy_request_task = tn.to_mock_request_task()
                data[tn.address] = GraphTask(resources)

        def termination_fn(
            *dependent_values: List[Row],
        ) -> Dict[str, Optional[List[Row]]]:
            """A termination function that just returns its inputs mapped to their source addresses.
            This needs to wait for all dependent keys because this is how dask is informed to wait for
            all terminating addresses before calling this."""

            return resources.get_all_cached_objects()

        env: Dict[CollectionAddress, GraphTask] = {}
        end_nodes: List[CollectionAddress] = traversal.traverse(env, collect_tasks_fn)

        dsk: Dict[CollectionAddress, Tuple[Any, ...]] = {
            k: (t.access_request, *t.execution_node.input_keys) for k, t in env.items()
        }
        dsk[ROOT_COLLECTION_ADDRESS] = (start_function([traversal.seed_data]),)
        dsk[TERMINATOR_ADDRESS] = (termination_fn, *end_nodes)
        update_mapping_from_cache(dsk, resources, start_function)

        # cache a map of collections -> data uses for the output package of access requests
        # this is cached here before request execution, since this is the state of the
        # graph used for request execution. the graph could change _during_ request execution,
        # but we don't want those changes in our data use map.
        privacy_request.cache_data_use_map(
            format_data_use_map_for_caching(
                {
                    coll_address: gt.execution_node.connection_key
                    for (coll_address, gt) in env.items()
                },
                connection_configs,
            )
        )

        v = delayed(get(dsk, TERMINATOR_ADDRESS, num_workers=1))
        return v.compute()


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


def run_erasure_request_deprecated(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    access_request_data: Dict[str, List[Row]],
    session: Session,
) -> Dict[str, int]:
    """Deprecated: Run an erasure request sequentially in-memory using Dask"""
    traversal: Traversal = Traversal(graph, identity)
    with TaskResources(
        privacy_request, policy, connection_configs, EMPTY_REQUEST_TASK, session
    ) as resources:

        def collect_tasks_fn(
            tn: TraversalNode, data: Dict[CollectionAddress, GraphTask]
        ) -> None:
            """Run the traversal, as an action creating a GraphTask for each traversal_node."""
            if not tn.is_root_node():
                # Mock a RequestTask object in memory to share code with DSR 3.0
                resources.privacy_request_task = tn.to_mock_request_task()
                data[tn.address] = GraphTask(resources)

        env: Dict[CollectionAddress, GraphTask] = {}
        # Modifies env in place
        traversal.traverse(env, collect_tasks_fn)
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
                *_evaluate_erasure_dependencies(t, erasure_end_nodes),
            )
            for k, t in env.items()
        }

        # root node returns 0 to be consistent with the output of the other erasure tasks
        dsk[ROOT_COLLECTION_ADDRESS] = 0
        # terminator function reads and returns the cached erasure results for the entire erasure traversal
        dsk[TERMINATOR_ADDRESS] = (termination_fn, *erasure_end_nodes)
        update_erasure_mapping_from_cache(dsk, resources)

        # using an existing function from dask.core to detect cycles in the generated graph
        collection_cycle = getcycle(dsk, None)
        if collection_cycle:
            logger.error(
                "TraversalError encountered for privacy request {}. Error: The values for the `erase_after` fields caused a cycle in the following collections {}",
                privacy_request.id,
                collection_cycle,
            )
            privacy_request.add_error_execution_log(
                db=session,
                connection_key=None,
                collection_name=None,
                dataset_name=None,
                message=f"The values for the `erase_after` fields caused a cycle in the following collections {collection_cycle}",
                action_type=ActionType.erasure,
            )
            privacy_request.error_processing(session)
            raise TraversalError(
                f"The values for the `erase_after` fields caused a cycle in the following collections {collection_cycle}"
            )

        v = delayed(get(dsk, TERMINATOR_ADDRESS, num_workers=1))
        return v.compute()


def _evaluate_erasure_dependencies(
    t: GraphTask, end_nodes: List[CollectionAddress]
) -> Set[CollectionAddress]:
    """
    Return a set of collection addresses corresponding to collections that need
    to be erased before the given task. Remove the dependent collection addresses
    from `end_nodes` so they can be executed in the correct order. If a task does
    not have any dependencies it is linked directly to the root node
    """
    erase_after = t.execution_node.collection.erase_after
    for collection in erase_after:
        if collection in end_nodes:
            # end_node list is modified in place
            end_nodes.remove(collection)
    # this task will execute after the collections in `erase_after` or
    # execute at the beginning by linking it to the root node
    return erase_after if len(erase_after) else {ROOT_COLLECTION_ADDRESS}


def run_consent_request_deprecated(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
) -> Dict[str, bool]:
    """Run a consent request

    The graph built is very simple: there are no relationships between the nodes, every node has
    identity data input and every node outputs whether the consent request succeeded.

    The DatasetGraph passed in is expected to have one Node per Dataset.  That Node is expected to carry out requests
    for the Dataset as a whole.
    """
    with TaskResources(
        privacy_request, policy, connection_configs, EMPTY_REQUEST_TASK, session
    ) as resources:
        graph_keys: List[CollectionAddress] = list(graph.nodes.keys())
        dsk: Dict[CollectionAddress, Any] = {}

        for col_address, node in graph.nodes.items():
            traversal_node = TraversalNode(node)
            # Mock a RequestTask object in memory to share code with DSR 3.0
            resources.privacy_request_task = traversal_node.to_mock_request_task()
            task = GraphTask(resources)
            dsk[col_address] = (task.consent_request, identity)

        def termination_fn(*dependent_values: bool) -> Tuple[bool, ...]:
            """The dependent_values here is an bool output from each task feeding in, where
            each task reports the output of 'task.consent_request(identity_data)', which is whether the
            consent request succeeded

            The termination function just returns this tuple of booleans."""
            return dependent_values

        # terminator function waits for all keys
        dsk[TERMINATOR_ADDRESS] = (termination_fn, *graph_keys)

        v = delayed(get(dsk, TERMINATOR_ADDRESS, num_workers=1))

        update_successes: Tuple[bool, ...] = v.compute()
        # we combine the output of the termination function with the input keys to provide
        # a map of {collection_name: whether consent request succeeded}:
        consent_update_map: Dict[str, bool] = dict(
            zip([coll.value for coll in graph_keys], update_successes)
        )

        return consent_update_map

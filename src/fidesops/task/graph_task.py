import itertools
import logging
import traceback
from abc import ABC
from collections import defaultdict
from time import sleep
from typing import List, Dict, Any, Tuple, Callable, Optional, Set
from functools import wraps

import dask
from dask.threaded import get

from fidesops.core.config import config
from fidesops.graph.config import (
    CollectionAddress,
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
)
from fidesops.graph.graph import Edge, DatasetGraph
from fidesops.graph.traversal import TraversalNode, Row, Traversal
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.models.policy import ActionType, Policy
from fidesops.models.privacy_request import PrivacyRequest, ExecutionLogStatus
from fidesops.service.connectors import BaseConnector
from fidesops.task.task_resources import TaskResources
from fidesops.util.collection_util import partition, append

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dask.config.set(scheduler="processes")

EMPTY_REQUEST = PrivacyRequest()


def retry(
    action_type: ActionType,
    default_return: Any,
) -> Callable:
    """
    Retry decorator for access and right to forget requests requests -

    If an exception is raised, we retry the function `count` times with exponential backoff. After the number of
    retries have expired, we call GraphTask.end() with the appropriate `action_type` and `default_return`.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def result(*args: Any, **kwargs: Any) -> List[Optional[Row]]:
            func_delay = config.execution.TASK_RETRY_DELAY
            method_name = func.__name__
            self = args[0]

            raised_ex = None
            for attempt in range(config.execution.TASK_RETRY_COUNT + 1):
                try:
                    # Create ExecutionLog with status in_processing or retrying
                    if attempt:
                        self.log_retry(action_type)
                    else:
                        self.log_start(action_type)
                    # Run access or erasure request
                    return func(*args, **kwargs)
                except BaseException as ex:  # pylint: disable=W0703
                    func_delay *= config.execution.TASK_RETRY_BACKOFF
                    logger.warning(
                        f"Retrying {method_name} {self.traversal_node.address} in {func_delay} seconds..."
                    )
                    sleep(func_delay)
                    raised_ex = ex
            self.log_end(action_type, raised_ex)
            return default_return

        return result

    return decorator


class GraphTask(ABC):  # pylint: disable=too-many-instance-attributes
    """A task that operates on one traversal_node of a traversal"""

    def __init__(
        self, traversal_node: TraversalNode, resources: TaskResources
    ):  # cache config, log config, db store config
        super().__init__()
        self.traversal_node = traversal_node
        self.resources = resources
        self.connector: BaseConnector = resources.get_connector(
            self.traversal_node.node.dataset.connection_key  # ConnectionConfig.key
        )

        # # [(foreign address, local address)]
        # self._incoming_edge_tuples: List[Tuple[FieldAddress, FieldAddress]] = [
        #     (e.f1, e.f2) for e in self.traversal_node.incoming_edges()
        # ]

        # build incoming edges to the form : [dataset address: [(foreign field, local field)]
        b: Dict[CollectionAddress, List[Edge]] = partition(
            self.traversal_node.incoming_edges(), lambda e: e.f1.collection_address()
        )
        self.incoming_field_map: Dict[CollectionAddress, List[Tuple[str, str]]] = {
            k: [(e.f1.field, e.f2.field) for e in t] for k, t in b.items()
        }
        # fields that point to child nodes
        self.outgoing_field_map: List[str] = sorted(
            {e.f1.field for e in self.traversal_node.outgoing_edges()}
        )

        # the input keys this task will read from.These will build the dask graph
        self.input_keys: List[CollectionAddress] = sorted(b.keys())

        self.key = self.traversal_node.address

        self.execution_log_id = None
        # a local copy of the execution log record written to. If we write multiple status
        # updates, we will use this id to ensure that we're updating rather than creating
        # a new record

    def __repr__(self) -> str:
        return f"{type(self)}:{self.key}"

    def generate_dry_run_query(self) -> str:
        """Type-specific query generated for this traversal_node."""
        return self.connector.dry_run_query(self.traversal_node)

    def to_dask_input_data(self, *data: List[Row]) -> Dict[str, List[Any]]:
        """Each dict in the input list represents the output of a dependent task.
        These outputs should correspond to the input key order.
        {table1: [{x:1, y:A}, {x:2, y:B}], table2: [{x:3},{x:4}],
           where table1.x => self.id,
           table1.y=> self.name,
           table2.x=>self.id
         becomes
         {id:[1,2,3,4], name:["A","B"]}
        """

        if not len(data) == len(self.input_keys):
            logger.warning(
                "%s expected %s input keys, received %s",
                self,
                len(self.input_keys),
                len(data),
            )

        output: Dict[str, List[Any]] = {}
        for i, rowset in enumerate(data):
            collection_address = self.input_keys[i]
            field_mappings = self.incoming_field_map[collection_address]

            for row in rowset:
                for foreign_field, local_field in field_mappings:
                    append(output, local_field, row.get(foreign_field))

        return output

    def update_status(
        self,
        msg: str,
        fields_affected: Any,
        action_type: ActionType,
        status: ExecutionLogStatus,
    ) -> None:
        """Update status activities"""
        self.resources.write_execution_log(
            self.traversal_node.address,
            fields_affected,
            action_type,
            status,
            msg,
        )

    def log_start(self, action_type: ActionType) -> None:
        """Task start activities"""
        logger.info(f"Starting {self.resources.request.id}, traversal_node {self.key}")

        self.update_status(
            "starting", [], action_type, ExecutionLogStatus.in_processing
        )

    def log_retry(self, action_type: ActionType) -> None:
        """Task retry activities"""
        logger.info(f"Retrying {self.resources.request.id}, node {self.key}")

        self.update_status("retrying", [], action_type, ExecutionLogStatus.retrying)

    def log_end(
        self, action_type: ActionType, ex: Optional[BaseException] = None
    ) -> None:
        """On completion activities"""
        if ex:
            traceback.print_exc()
            logger.warning(
                f"Ending {self.resources.request.id}, {self.key} with failure {ex}"
            )
            self.update_status(str(ex), [], action_type, ExecutionLogStatus.error)
        else:
            logger.info(f"Ending {self.resources.request.id}, {self.key}")
            self.update_status(
                "success",
                [
                    {
                        "field_name": f.name,
                        "path": f"{self.traversal_node.node.address}:{f.name}",
                        "data_categories": f.data_categories,
                    }
                    for f in self.traversal_node.node.collection.fields
                ],
                action_type,
                ExecutionLogStatus.complete,
            )

    @retry(action_type=ActionType.access, default_return=[])
    def access_request(self, *inputs: List[Row]) -> List[Row]:
        """Run access request"""
        output = self.connector.retrieve_data(
            self.traversal_node, self.resources.policy, self.to_dask_input_data(*inputs)
        )
        self.resources.cache_object(f"access_request__{self.key}", output)
        self.log_end(ActionType.access)
        return output

    @retry(action_type=ActionType.erasure, default_return=0)
    def erasure_request(self, retrieved_data: List[Row]) -> int:
        """Run erasure request"""
        # if there is no primary key specified in the graph node configuration
        # note this in the execution log and perform no erasures on this node
        if not self.traversal_node.node.contains_field(lambda f: f.primary_key):
            self.update_status(
                "No values were erased since no primary key was defined for this collection",
                None,
                ActionType.erasure,
                ExecutionLogStatus.complete,
            )
            return 0

        output = self.connector.mask_data(
            self.traversal_node, self.resources.policy, retrieved_data, True
        )
        self.log_end(ActionType.erasure)
        return output


def collect_queries(
    traversal: Traversal, resources: TaskResources
) -> Dict[CollectionAddress, str]:
    """Collect all queries for dry-run"""

    def collect_queries_fn(
        tn: TraversalNode, data: Dict[CollectionAddress, str]
    ) -> None:
        if not tn.is_root_node():
            data[tn.address] = GraphTask(tn, resources).generate_dry_run_query()

    env: Dict[CollectionAddress, str] = {}
    traversal.traverse(env, collect_queries_fn)
    return env


def run_access_request(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
) -> Dict[str, List[Row]]:
    """Run the access request"""
    traversal: Traversal = Traversal(graph, identity)
    resources = TaskResources(privacy_request, policy, connection_configs)

    def start_function(seed: Dict[str, Any]) -> Callable[[], List[Dict[str, Any]]]:
        """Return a function that returns the seed value to kick off the dask function chain.

        The first traversal_node in the dask function chain is just a function that when called returns
        the graph seed value."""

        def g() -> List[Dict[str, Any]]:
            return [seed]

        return g

    def collect_tasks_fn(
        tn: TraversalNode, data: Dict[CollectionAddress, GraphTask]
    ) -> None:
        """Run the traversal, as an action creating a GraphTask for each traversal_node."""
        if not tn.is_root_node():
            data[tn.address] = GraphTask(tn, resources)

    def termination_fn(*dependent_values: List[Row]) -> Dict[str, List[Row]]:

        """A termination function that just returns its inputs mapped to their source addresses.

        This needs to wait for all dependent keys because this is how dask is informed to wait for
        all terminating addresses before calling this."""

        return resources.get_all_cached_objects()

    env: Dict[CollectionAddress, Any] = {}
    end_nodes = traversal.traverse(env, collect_tasks_fn)

    dsk = {k: (t.access_request, *t.input_keys) for k, t in env.items()}
    dsk[ROOT_COLLECTION_ADDRESS] = (start_function(traversal.seed_data),)
    dsk[TERMINATOR_ADDRESS] = (termination_fn, *end_nodes)
    v = dask.delayed(get(dsk, TERMINATOR_ADDRESS))

    return v.compute()


def run_erasure(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    access_request_data: Dict[str, List[Row]],
) -> Dict[str, int]:
    """Run an erasure request"""
    traversal: Traversal = Traversal(graph, identity)
    resources = TaskResources(privacy_request, policy, connection_configs)

    def collect_tasks_fn(
        tn: TraversalNode, data: Dict[CollectionAddress, GraphTask]
    ) -> None:
        """Run the traversal, as an action creating a GraphTask for each traversal_node."""
        if not tn.is_root_node():
            data[tn.address] = GraphTask(tn, resources)

    env: Dict[CollectionAddress, Any] = {}
    traversal.traverse(env, collect_tasks_fn)

    def termination_fn(*dependent_values: int) -> Tuple[int, ...]:

        """The dependent_values here is an int output from each task feeding in, where
        each task reports the output of 'task.rtf(access_request_data)', which is the number of
        records updated.

        The termination function just returns this tuple of ints."""
        return dependent_values

    dsk: Dict[CollectionAddress, Any] = {
        k: (t.erasure_request, access_request_data[str(k)]) for k, t in env.items()
    }
    # terminator function waits for all keys
    dsk[TERMINATOR_ADDRESS] = (termination_fn, *env.keys())
    v = dask.delayed(get(dsk, TERMINATOR_ADDRESS))

    update_cts: Tuple[int, ...] = v.compute()
    # we combine the output of the termination function with the input keys to provide
    # a map of {collection_name: records_updated}:
    erasure_update_map: Dict[str, int] = dict(zip([str(x) for x in env], update_cts))

    return erasure_update_map


def filter_data_categories(
    access_request_results: Dict[str, Optional[Any]],
    target_categories: Set[str],
    graph: DatasetGraph,
) -> Dict[str, List[Dict[str, Any]]]:
    """Filter access request results to only return fields associated with the target data categories
    and subcategories

    For example, if data category "user.provided.identifiable.contact" is specified on one of the rule targets,
    all fields on subcategories also apply, so ["user.provided.identifiable.contact.city",
    "user.provided.identifiable.contact.street", ...], etc.
    """
    logger.info(
        "Filtering Access Request results to return fields associated with data categories"
    )
    filtered_access_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    data_category_fields: Dict[str, Dict[str, List]] = graph.data_category_field_mapping

    for node_address, results in access_request_results.items():
        if not results:
            continue

        # Gets all fields on this traversal_node associated with the requested data categories and sub data categories
        target_fields = set(
            itertools.chain(
                *[
                    fields
                    for cat, fields in data_category_fields[node_address].items()
                    if any([cat.startswith(tar) for tar in target_categories])
                ]
            )
        )

        if not target_fields:
            continue

        for row in results:
            filtered_access_results[node_address].append(
                {
                    field: result
                    for field, result in row.items()
                    if field in target_fields
                }
            )

    return filtered_access_results

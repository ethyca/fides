import copy

import logging
import traceback
from abc import ABC
from functools import wraps

from time import sleep
from typing import List, Dict, Any, Tuple, Callable, Optional, Set

import dask
from dask.threaded import get

from fidesops.core.config import config
from fidesops.graph.config import (
    CollectionAddress,
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    FieldPath,
    Field,
    FieldAddress,
)
from fidesops.graph.graph import Edge, DatasetGraph, Node
from fidesops.graph.traversal import TraversalNode, Traversal
from fidesops.models.connectionconfig import ConnectionConfig, AccessLevel
from fidesops.models.policy import ActionType, Policy
from fidesops.models.privacy_request import PrivacyRequest, ExecutionLogStatus
from fidesops.service.connectors import BaseConnector
from fidesops.task.consolidate_query_matches import consolidate_query_matches
from fidesops.task.filter_element_match import filter_element_match
from fidesops.task.refine_target_path import FieldPathNodeInput
from fidesops.task.task_resources import TaskResources
from fidesops.util.cache import get_cache
from fidesops.util.collection_util import partition, append, NodeInput, Row
from fidesops.util.logger import NotPii
from fidesops.util.saas_util import FIDESOPS_GROUPED_INPUTS

logger = logging.getLogger(__name__)

dask.config.set(scheduler="processes")

EMPTY_REQUEST = PrivacyRequest()
COLLECTION_FIELD_PATH_MAP = Dict[CollectionAddress, List[Tuple[FieldPath, FieldPath]]]


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

        # build incoming edges to the form : [dataset address: [(foreign field, local field)]
        self.incoming_edges_by_collection: Dict[
            CollectionAddress, List[Edge]
        ] = partition(
            self.traversal_node.incoming_edges(), lambda e: e.f1.collection_address()
        )

        # the input keys this task will read from.These will build the dask graph
        self.input_keys: List[CollectionAddress] = sorted(
            self.incoming_edges_by_collection.keys()
        )

        self.key = self.traversal_node.address

        self.execution_log_id = None
        # a local copy of the execution log record written to. If we write multiple status
        # updates, we will use this id to ensure that we're updating rather than creating
        # a new record

    def __repr__(self) -> str:
        return f"{type(self)}:{self.key}"

    @property
    def grouped_fields(self) -> Set[Optional[str]]:
        """Convenience property - returns a set of fields that have been specified on the collection as dependent
        upon one another
        """
        return self.traversal_node.node.collection.grouped_inputs or set()

    @property
    def dependent_identity_fields(self) -> bool:
        """If the current collection needs inputs from other collections, in addition to its seed data."""
        collection = self.traversal_node.node.collection
        for field in self.grouped_fields:
            if collection.field(FieldPath(field)).identity:
                return True
        return False

    def build_incoming_field_path_maps(
        self, group_dependent_fields: bool = False
    ) -> Tuple[COLLECTION_FIELD_PATH_MAP, COLLECTION_FIELD_PATH_MAP]:
        """
        For each collection connected to the current collection, return a list of tuples
        mapping the foreign field to the local field.  This is used to process data from incoming collections
        into the current collection.

        :param group_dependent_fields: Whether we should split the incoming fields into two groups: one whose
        fields are completely independent of one another, and the other whose incoming data needs to stay linked together.
        If False, all fields are returned in the first tuple, and the second tuple just maps collections to an empty list.

        """

        def field_map(keep: Callable) -> COLLECTION_FIELD_PATH_MAP:
            return {
                col_addr: [
                    (edge.f1.field_path, edge.f2.field_path)
                    for edge in edge_list
                    if keep(edge.f2.field_path.string_path)
                ]
                for col_addr, edge_list in self.incoming_edges_by_collection.items()
            }

        if group_dependent_fields:
            return field_map(
                lambda string_path: string_path not in self.grouped_fields
            ), field_map(lambda string_path: string_path in self.grouped_fields)

        return field_map(lambda string_path: True), field_map(lambda string_path: False)

    def generate_dry_run_query(self) -> str:
        """Type-specific query generated for this traversal_node."""
        return self.connector.dry_run_query(self.traversal_node)

    def can_write_data(self) -> bool:
        """Checks if the relevant ConnectionConfig has been granted "write" access to its data"""
        connection_config: ConnectionConfig = self.connector.configuration
        return connection_config.access == AccessLevel.write

    def _combine_seed_data(
        self,
        *data: List[Row],
        grouped_data: Dict[str, Any],
        dependent_field_mappings: COLLECTION_FIELD_PATH_MAP,
    ) -> Dict[str, Any]:
        """Combine the seed data with the other dependent inputs. This is used when the seed data in a collection requires
        inputs from another collection to generate subsequent queries."""
        # Get the identity values from the seeds that were passed into this collection.
        seed_index = self.input_keys.index(ROOT_COLLECTION_ADDRESS)
        seed_data = data[seed_index]

        for (foreign_field_path, local_field_path) in dependent_field_mappings[
            ROOT_COLLECTION_ADDRESS
        ]:
            dependent_values: List = consolidate_query_matches(
                row=seed_data, target_path=foreign_field_path
            )
            grouped_data[local_field_path.string_path] = dependent_values
        return grouped_data

    def pre_process_input_data(
        self, *data: List[Row], group_dependent_fields: bool = False
    ) -> NodeInput:
        """
        Consolidates the outputs of queries from potentially multiple collections whose
        data is needed as input into the current collection.

        Each dict in the input list represents the output of a dependent task.
        These outputs should correspond to the input key order.  Any nested fields are
        converted into dot-separated paths in the return.

         table1: [{x:1, y:A}, {x:2, y:B}], table2: [{x:3},{x:4}], table3: [{z: {a: C}, "y": [4, 5]}]
           where table1.x => self.id,
           table1.y=> self.name,
           table2.x=>self.id
           table3.z.a => self.contact.address
           table3.y => self.contact.email
         becomes
         {id:[1,2,3,4], name:["A","B"], contact.address:["C"], "contact.email": [4, 5]}

         If there are dependent fields from one collection into another, they are separated out as follows:
         {fidesops_grouped_inputs: [{"organization_id": 1, "project_id": "math}, {"organization_id": 5, "project_id": "science"}]
        """
        if not len(data) == len(self.input_keys):
            logger.warning(
                "%s expected %s input keys, received %s",
                NotPii(self),
                NotPii(len(self.input_keys)),
                NotPii(len(data)),
            )

        output: Dict[str, List[Any]] = {FIDESOPS_GROUPED_INPUTS: []}

        (
            independent_field_mappings,
            dependent_field_mappings,
        ) = self.build_incoming_field_path_maps(group_dependent_fields)

        for i, rowset in enumerate(data):
            collection_address = self.input_keys[i]

            if (
                group_dependent_fields
                and self.dependent_identity_fields
                and collection_address == ROOT_COLLECTION_ADDRESS
            ):
                # Skip building data for the root collection if the seed data needs to be combined with other inputs
                continue

            logger.info(
                f"Consolidating incoming data into {self.traversal_node.node.address} from {collection_address}."
            )
            for row in rowset:
                # Consolidate lists of independent field inputs
                for foreign_field_path, local_field_path in independent_field_mappings[
                    collection_address
                ]:
                    new_values: List = consolidate_query_matches(
                        row=row, target_path=foreign_field_path
                    )
                    if new_values:
                        append(output, local_field_path.string_path, new_values)

                # Separately group together dependent inputs if applicable
                if dependent_field_mappings[collection_address]:
                    grouped_data: Dict[str, Any] = {}
                    for (
                        foreign_field_path,
                        local_field_path,
                    ) in dependent_field_mappings[collection_address]:
                        dependent_values: List = consolidate_query_matches(
                            row=row, target_path=foreign_field_path
                        )
                        grouped_data[local_field_path.string_path] = dependent_values

                    if self.dependent_identity_fields:
                        grouped_data = self._combine_seed_data(
                            *data,
                            grouped_data=grouped_data,
                            dependent_field_mappings=dependent_field_mappings,
                        )

                    output[FIDESOPS_GROUPED_INPUTS].append(grouped_data)
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
                build_affected_field_logs(
                    self.traversal_node.node, self.resources.policy, action_type
                ),
                action_type,
                ExecutionLogStatus.complete,
            )

    def post_process_input_data(
        self, pre_processed_inputs: NodeInput
    ) -> FieldPathNodeInput:
        """
        For each entrypoint field, specify if we should return all data, or just data that matches the coerced
        input values. Used for post-processing access request results for a given collection.

        :param pre_processed_inputs: string paths mapped to values that were used to query the current collection
        :return: FieldPaths mapped to type-coerced values that we need to match in
        access request results, or FieldPaths mapped to None if we want to return everything.

        :Example:
        owner.phone field will not be filtered but we will process the owner.identifier results to return
        values that match one of [1234, 5678, 9102]

        {FieldPath("owner", "phone"): None, FieldPath("owner", "identifier"): [1234, 5678, 9102]}
        """
        out: FieldPathNodeInput = {}
        for key, values in pre_processed_inputs.items():
            path: FieldPath = FieldPath.parse(key)
            field: Field = self.traversal_node.node.collection.field(path)
            if (
                field
                and path in self.traversal_node.query_field_paths
                and isinstance(values, list)
            ):
                if field.return_all_elements:
                    # All data will be returned
                    out[path] = None
                else:
                    # Default behavior - we will filter values to match those in filtered
                    cast_values = [
                        field.cast(v) for v in values
                    ]  # Cast values to expected type where possible
                    filtered = list(filter(lambda x: x is not None, cast_values))
                    if filtered:
                        out[path] = filtered
        return out

    def access_results_post_processing(
        self, formatted_input_data: NodeInput, output: List[Row]
    ) -> List[Row]:
        """
        Completes post-processing filtering of access request results.

        By default, if an array field was an entry point into the node, return only array elements that *match* the
        condition.  Specifying return_all_elements = true on the field's config will instead return *all* array elements.

        Caches the data in TWO separate formats: 1) erasure format, *replaces* unmatched array elements with placeholder
        text, and 2) access request format, which *removes* unmatched array elements altogether.  If no data was filtered
        out, both cached versions will be the same.
        """
        post_processed_node_input_data: FieldPathNodeInput = (
            self.post_process_input_data(formatted_input_data)
        )

        # For erasures: cache results with non-matching array elements *replaced* with placeholder text
        placeholder_output: List[Row] = copy.deepcopy(output)
        for row in placeholder_output:
            filter_element_match(
                row, query_paths=post_processed_node_input_data, delete_elements=False
            )
        self.resources.cache_results_with_placeholders(
            f"access_request__{self.key}", placeholder_output
        )

        # For access request results, cache results with non-matching array elements *removed*
        for row in output:
            logger.info(
                f"Filtering row in {self.traversal_node.node.address} for matching array elements."
            )
            filter_element_match(row, post_processed_node_input_data)
        self.resources.cache_object(f"access_request__{self.key}", output)

        # Return filtered rows with non-matched array data removed.
        return output

    @retry(action_type=ActionType.access, default_return=[])
    def access_request(self, *inputs: List[Row]) -> List[Row]:
        """Run an access request on a single node."""
        formatted_input_data: NodeInput = self.pre_process_input_data(
            *inputs, group_dependent_fields=True
        )
        output: List[Row] = self.connector.retrieve_data(
            self.traversal_node,
            self.resources.policy,
            self.resources.request,
            formatted_input_data,
        )
        filtered_output: List[Row] = self.access_results_post_processing(
            self.pre_process_input_data(*inputs, group_dependent_fields=False), output
        )
        self.log_end(ActionType.access)
        return filtered_output

    @retry(action_type=ActionType.erasure, default_return=0)
    def erasure_request(self, retrieved_data: List[Row]) -> int:
        """Run erasure request"""
        # if there is no primary key specified in the graph node configuration
        # note this in the execution log and perform no erasures on this node
        if not self.traversal_node.node.contains_field(lambda f: f.primary_key):
            logger.warning(
                f"No erasures on {self.traversal_node.node.address} as there is no primary_key defined."
            )
            self.update_status(
                "No values were erased since no primary key was defined for this collection",
                None,
                ActionType.erasure,
                ExecutionLogStatus.complete,
            )
            return 0

        if not self.can_write_data():
            logger.warning(
                f"No erasures on {self.traversal_node.node.address} as its ConnectionConfig does not have write access."
            )
            self.update_status(
                f"No values were erased since this connection {self.connector.configuration.key} has not been "
                f"given write access",
                None,
                ActionType.erasure,
                ExecutionLogStatus.error,
            )
            return 0

        output = self.connector.mask_data(
            self.traversal_node,
            self.resources.policy,
            self.resources.request,
            retrieved_data,
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
    with TaskResources(privacy_request, policy, connection_configs) as resources:

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
    return {k.split("__")[-1]: v for k, v in value_dict.items()}


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
    with TaskResources(privacy_request, policy, connection_configs) as resources:

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
        erasure_update_map: Dict[str, int] = dict(
            zip([str(x) for x in env], update_cts)
        )

        return erasure_update_map


def build_affected_field_logs(
    node: Node, policy: Policy, action_type: ActionType
) -> List[Dict[str, Any]]:
    """For a given node (collection), policy, and action_type (access or erasure) format all of the fields that
    were potentially touched to be stored in the ExecutionLogs for troubleshooting.

    :Example:
    [{
        "path": "dataset_name:collection_name:field_name",
        "field_name": "field_name",
        "data_categories": ["data_category_1", "data_category_2"]
    }]
    """

    targeted_field_paths: Dict[FieldAddress, str] = {}

    for rule in policy.rules:
        if rule.action_type != action_type:
            continue
        rule_categories: List[str] = rule.get_target_data_categories()
        if not rule_categories:
            continue

        collection_categories: Dict[
            str, List[FieldPath]
        ] = node.collection.field_paths_by_category
        for rule_cat in rule_categories:
            for collection_cat, field_paths in collection_categories.items():
                if collection_cat.startswith(rule_cat):
                    targeted_field_paths.update(
                        {
                            node.address.field_address(field_path): collection_cat
                            for field_path in field_paths
                        }
                    )

    ret: List[Dict[str, Any]] = []
    for field_address, data_categories in targeted_field_paths.items():
        ret.append(
            {
                "path": field_address.value,
                "field_name": field_address.field_path.string_path,
                "data_categories": [data_categories],
            }
        )

    return ret

# pylint: disable=too-many-lines
import copy
import traceback
from abc import ABC
from functools import wraps
from time import sleep
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import dask
from dask import delayed  # type: ignore[attr-defined]
from dask.core import getcycle
from dask.threaded import get
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    ActionDisabled,
    CollectionDisabled,
    NotSupportedForCollection,
    PrivacyRequestErasureEmailSendRequired,
    PrivacyRequestPaused,
    SkippingConsentPropagation,
    TraversalError,
)
from fides.api.graph.analytics_events import (
    fideslog_graph_rerun,
    prepare_rerun_graph_analytics_event,
)
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
    Field,
    FieldAddress,
    FieldPath,
)
from fides.api.graph.graph import DatasetGraph, Edge, Node
from fides.api.graph.graph_differences import format_graph_for_caching
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.connectionconfig import AccessLevel, ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import ExecutionLogStatus, PrivacyRequest
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.task.consolidate_query_matches import consolidate_query_matches
from fides.api.task.filter_element_match import filter_element_match
from fides.api.task.refine_target_path import FieldPathNodeInput
from fides.api.task.task_resources import TaskResources
from fides.api.util.cache import get_cache
from fides.api.util.collection_util import (
    NodeInput,
    Row,
    append,
    extract_key_for_address,
    partition,
)
from fides.api.util.consent_util import add_errored_system_status_for_consent_reporting
from fides.api.util.logger import Pii
from fides.api.util.saas_util import FIDESOPS_GROUPED_INPUTS
from fides.config import CONFIG

dask.config.set(scheduler="threads")

COLLECTION_FIELD_PATH_MAP = Dict[CollectionAddress, List[Tuple[FieldPath, FieldPath]]]

EMPTY_REQUEST = PrivacyRequest()


def retry(
    action_type: ActionType,
    default_return: Any,
) -> Callable:
    """
    Retry decorator for access and right to forget requests requests -

    If an exception is raised, we retry the function `count` times with exponential backoff. After the number of
    retries have expired, we call GraphTask.end() with the appropriate `action_type` and `default_return`.

    If we exceed the number of TASK_RETRY_COUNT retries, we re-raise the exception to stop execution of the privacy request.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def result(*args: Any, **kwargs: Any) -> Any:
            func_delay = CONFIG.execution.task_retry_delay
            method_name = func.__name__
            self = args[0]

            raised_ex: Optional[Union[BaseException, Exception]] = None
            for attempt in range(CONFIG.execution.task_retry_count + 1):
                try:
                    self.skip_if_disabled()
                    self.skip_if_action_disabled(action_type)
                    # Create ExecutionLog with status in_processing or retrying
                    if attempt:
                        self.log_retry(action_type)
                    else:
                        self.log_start(action_type)
                    # Run access or erasure request
                    return func(*args, **kwargs)
                except PrivacyRequestPaused as ex:
                    traceback.print_exc()
                    logger.warning(
                        "Privacy request {} paused {}",
                        method_name,
                        self.traversal_node.address,
                    )
                    self.log_paused(action_type, ex)
                    # Re-raise to stop privacy request execution on pause.
                    raise
                except PrivacyRequestErasureEmailSendRequired as exc:
                    traceback.print_exc()
                    self.log_end(action_type, ex=None, success_override_msg=exc)
                    self.resources.cache_erasure(
                        f"{self.traversal_node.address.value}", 0
                    )  # Cache that the erasure was performed in case we need to restart
                    return 0
                except (
                    CollectionDisabled,
                    ActionDisabled,
                    NotSupportedForCollection,
                ) as exc:
                    traceback.print_exc()
                    logger.warning(
                        "Skipping collection {} for privacy_request: {}",
                        self.traversal_node.address,
                        self.resources.request.id,
                    )
                    self.log_skipped(action_type, exc)
                    return default_return
                except SkippingConsentPropagation as exc:
                    traceback.print_exc()
                    logger.warning(
                        "Skipping consent propagation on collection {} for privacy_request: {}",
                        self.traversal_node.address,
                        self.resources.request.id,
                    )
                    self.log_skipped(action_type, exc)
                    for pref in self.resources.request.privacy_preferences:
                        # For consent reporting, also caching the given system as skipped for all historical privacy preferences.
                        pref.cache_system_status(
                            self.resources.session,
                            self.connector.configuration.system_key,
                            ExecutionLogStatus.skipped,
                        )
                    return default_return
                except BaseException as ex:  # pylint: disable=W0703
                    traceback.print_exc()
                    func_delay *= CONFIG.execution.task_retry_backoff
                    logger.warning(
                        "Retrying {} {} in {} seconds...",
                        method_name,
                        self.traversal_node.address,
                        func_delay,
                    )
                    sleep(func_delay)
                    raised_ex = ex
            self.log_end(action_type, raised_ex)
            self.resources.request.cache_failed_checkpoint_details(
                step=action_type, collection=self.traversal_node.address
            )
            add_errored_system_status_for_consent_reporting(
                self.resources.session,
                self.resources.request,
                self.connector.configuration,
            )
            # Re-raise to stop privacy request execution on failure.
            raise raised_ex  # type: ignore

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
        self.data_uses: Set[str] = (
            System.get_data_uses(
                [self.connector.configuration.system], include_parents=False
            )
            if self.connector.configuration.system
            else {}
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
    def grouped_fields(self) -> Set[str]:
        """Convenience property - returns a set of fields that have been specified on the collection as dependent
        upon one another
        """
        return self.traversal_node.node.collection.grouped_inputs or set()

    @property
    def dependent_identity_fields(self) -> bool:
        """If the current collection needs inputs from other collections, in addition to its seed data."""
        collection = self.traversal_node.node.collection
        for field in self.grouped_fields:
            if collection.field(FieldPath(field)).identity:  # type: ignore
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

    def generate_dry_run_query(self) -> Optional[str]:
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

        for foreign_field_path, local_field_path in dependent_field_mappings[
            ROOT_COLLECTION_ADDRESS
        ]:
            dependent_values = consolidate_query_matches(
                row=seed_data, target_path=foreign_field_path  # type: ignore
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
                "{} expected {} input keys, received {}",
                self,
                len(self.input_keys),
                len(data),
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
                "Consolidating incoming data into {} from {}.",
                self.traversal_node.node.address,
                collection_address,
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
            self.traversal_node.node.dataset.connection_key,
            self.traversal_node.address,
            fields_affected,
            action_type,
            status,
            msg,
        )

    def log_start(self, action_type: ActionType) -> None:
        """Task start activities"""
        logger.info(
            "Starting {}, traversal_node {}", self.resources.request.id, self.key
        )

        self.update_status(
            "starting", [], action_type, ExecutionLogStatus.in_processing
        )

    def log_retry(self, action_type: ActionType) -> None:
        """Task retry activities"""
        logger.info("Retrying {}, node {}", self.resources.request.id, self.key)

        self.update_status("retrying", [], action_type, ExecutionLogStatus.retrying)

    def log_paused(self, action_type: ActionType, ex: Optional[BaseException]) -> None:
        """On paused activities"""
        logger.info("Pausing {}, node {}", self.resources.request.id, self.key)

        self.update_status(str(ex), [], action_type, ExecutionLogStatus.paused)

    def log_skipped(self, action_type: ActionType, ex: str) -> None:
        """Log that a collection was skipped.  For now, this is because a collection has been disabled."""
        logger.info("Skipping {}, node {}", self.resources.request.id, self.key)

        self.update_status(str(ex), [], action_type, ExecutionLogStatus.skipped)

    def log_end(
        self,
        action_type: ActionType,
        ex: Optional[BaseException] = None,
        success_override_msg: Optional[BaseException] = None,
    ) -> None:
        """On completion activities"""
        if ex:
            logger.warning(
                "Ending {}, {} with failure {}",
                self.resources.request.id,
                self.key,
                Pii(ex),
            )
            self.update_status(str(ex), [], action_type, ExecutionLogStatus.error)
        else:
            logger.info("Ending {}, {}", self.resources.request.id, self.key)
            self.update_status(
                str(success_override_msg) if success_override_msg else "success",
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
            field: Optional[Field] = self.traversal_node.node.collection.field(path)
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
                "Filtering row in {} for matching array elements.",
                self.traversal_node.node.address,
            )
            filter_element_match(row, post_processed_node_input_data)
        self.resources.cache_object(f"access_request__{self.key}", output)

        # Return filtered rows with non-matched array data removed.
        return output

    def skip_if_disabled(self) -> None:
        """Skip execution for the given collection if it is attached to a disabled ConnectionConfig."""
        connection_config: ConnectionConfig = self.connector.configuration
        if connection_config.disabled:
            raise CollectionDisabled(
                f"Skipping collection {self.traversal_node.node.address}. "
                f"ConnectionConfig {connection_config.key} is disabled.",
            )

    def skip_if_action_disabled(self, action_type: ActionType) -> None:
        """Skip execution for the given collection if it is attached to a ConnectionConfig that does not have the given action_type enabled."""

        # the access action is never disabled since it provides data that is needed for erasure requests
        if action_type == ActionType.access:
            return

        connection_config: ConnectionConfig = self.connector.configuration
        if (
            connection_config.enabled_actions is not None
            and action_type not in connection_config.enabled_actions
        ):
            raise ActionDisabled(
                f"Skipping collection {self.traversal_node.node.address}. "
                f"The {action_type} action is disabled for connection config with key '{connection_config.key}'.",
            )

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
    def erasure_request(
        self,
        retrieved_data: List[Row],
        inputs: List[List[Row]],
        *erasure_prereqs: int,
    ) -> int:
        """Run erasure request"""
        # if there is no primary key specified in the graph node configuration
        # note this in the execution log and perform no erasures on this node
        if not self.traversal_node.node.contains_field(lambda f: f.primary_key):
            logger.warning(
                "No erasures on {} as there is no primary_key defined.",
                self.traversal_node.node.address,
            )
            self.update_status(
                "No values were erased since no primary key was defined for this collection",
                None,
                ActionType.erasure,
                ExecutionLogStatus.complete,
            )
            # Cache that the erasure was performed in case we need to restart
            self.resources.cache_erasure(self.key.value, 0)
            return 0

        if not self.can_write_data():
            logger.warning(
                "No erasures on {} as its ConnectionConfig does not have write access.",
                self.traversal_node.node.address,
            )
            self.update_status(
                f"No values were erased since this connection {self.connector.configuration.key} has not been "
                f"given write access",
                None,
                ActionType.erasure,
                ExecutionLogStatus.error,
            )
            self.resources.cache_erasure(self.key.value, 0)
            return 0

        formatted_input_data: NodeInput = self.pre_process_input_data(
            *inputs, group_dependent_fields=True
        )

        output = self.connector.mask_data(
            self.traversal_node,
            self.resources.policy,
            self.resources.request,
            retrieved_data,
            formatted_input_data,
        )
        self.log_end(ActionType.erasure)
        self.resources.cache_erasure(
            f"{self.key}", output
        )  # Cache that the erasure was performed in case we need to restart
        return output

    @retry(action_type=ActionType.consent, default_return=False)
    def consent_request(self, identity: Dict[str, Any]) -> bool:
        """Run consent request request"""
        if not self.can_write_data():
            logger.warning(
                "No consent on {} as its ConnectionConfig does not have write access.",
                self.traversal_node.node.address,
            )
            self.update_status(
                f"No values were erased since this connection {self.connector.configuration.key} has not been "
                f"given write access",
                None,
                ActionType.erasure,
                ExecutionLogStatus.error,
            )
            return False

        output: bool = self.connector.run_consent_request(
            self.traversal_node,
            self.resources.policy,
            self.resources.request,
            identity,
            self.resources.session,
        )
        self.log_end(ActionType.consent)
        return output


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


async def run_access_request(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
) -> Dict[str, List[Row]]:
    """Run the access request"""
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

        v = delayed(get(dsk, TERMINATOR_ADDRESS, num_workers=1))
        access_results = v.compute()
        filtered_access_results = filter_by_enabled_actions(
            access_results, connection_configs
        )
        return filtered_access_results


def filter_by_enabled_actions(
    access_results: Dict[str, Any], connection_configs: List[ConnectionConfig]
) -> Dict[str, Any]:
    """Removes any access results that are associated with a connection config that doesn't have the access action enabled."""

    # create a map between the dataset and its connection config's enabled actions
    dataset_enabled_actions = {}
    for config in connection_configs:
        for dataset in config.datasets:
            dataset_enabled_actions[dataset.fides_key] = config.enabled_actions

    # use the enabled actions map to filter out the access results
    filtered_access_results = {}
    for key, value in access_results.items():
        dataset_name = key.split(":")[0]
        enabled_action = dataset_enabled_actions.get(dataset_name)
        if enabled_action is None or ActionType.access in enabled_action:
            filtered_access_results[key] = value

    return filtered_access_results


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


async def run_erasure(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    access_request_data: Dict[str, List[Row]],
    session: Session,
) -> Dict[str, int]:
    """Run an erasure request"""
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
    erase_after = t.traversal_node.node.collection.erase_after
    for collection in erase_after:
        if collection in end_nodes:
            # end_node list is modified in place
            end_nodes.remove(collection)
    # this task will execute after the collections in `erase_after` or
    # execute at the beginning by linking it to the root node
    return erase_after if len(erase_after) else {ROOT_COLLECTION_ADDRESS}


async def run_consent_request(  # pylint: disable = too-many-arguments
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
        privacy_request, policy, connection_configs, session
    ) as resources:
        graph_keys: List[CollectionAddress] = list(graph.nodes.keys())
        dsk: Dict[CollectionAddress, Any] = {}

        for col_address, node in graph.nodes.items():
            traversal_node = TraversalNode(node)
            task = GraphTask(traversal_node, resources)
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

    for rule in policy.rules:  # type: ignore[attr-defined]
        if rule.action_type != action_type:
            continue
        rule_categories: List[str] = rule.get_target_data_categories()
        if not rule_categories:
            continue

        collection_categories: Dict[
            str, List[FieldPath]
        ] = node.collection.field_paths_by_category  # type: ignore
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

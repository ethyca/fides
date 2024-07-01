from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from fideslang.validation import FidesKey

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    Field,
    FieldAddress,
    FieldPath,
)
from fides.api.graph.graph import Edge
from fides.api.models.privacy_request import RequestTask, TraversalDetails
from fides.api.util.collection_util import partition
from fides.api.util.logger_context_utils import Contextualizable, LoggerContextKeys

COLLECTION_FIELD_PATH_MAP = Dict[CollectionAddress, List[Tuple[FieldPath, FieldPath]]]


class ExecutionNode(Contextualizable):  # pylint: disable=too-many-instance-attributes
    """Node for *executing* a task. This node only has knowledge of itself and its incoming and outgoing edges

    After we build the graph, we save details to RequestTasks in the database that are hydrated here to execute an individual
    node without rebuilding the graph with traversal.traverse
    """

    def __init__(self, request_task: RequestTask):
        assert request_task.collection  # For mypy
        self.collection: Collection = Collection.parse_from_request_task(
            request_task.collection
        )
        self.address: CollectionAddress = CollectionAddress.from_string(
            request_task.collection_address
        )
        traversal_details = TraversalDetails.model_validate(
            request_task.traversal_details or {}
        )

        self.incoming_edges: Set[Edge] = {
            Edge(FieldAddress.from_string(edge[0]), FieldAddress.from_string(edge[1]))
            for edge in traversal_details.incoming_edges
        }
        self.outgoing_edges: Set[Edge] = {
            Edge(FieldAddress.from_string(edge[0]), FieldAddress.from_string(edge[1]))
            for edge in traversal_details.outgoing_edges
        }
        self.connection_key: FidesKey = FidesKey(
            traversal_details.dataset_connection_key
        )

        self.incoming_edges_by_collection: Dict[CollectionAddress, List[Edge]] = (
            partition(self.incoming_edges, lambda e: e.f1.collection_address())
        )

        # Input should be passed into accessing data in this order
        self.input_keys: List[CollectionAddress] = [
            CollectionAddress.from_string(input_key)
            for input_key in traversal_details.input_keys
        ]
        self.grouped_fields = self.collection.grouped_inputs

    @property
    def query_field_paths(self) -> Set[FieldPath]:
        """
        All of the possible field paths that we can query for possible filter values.
        These are field paths that are the ends of incoming edges.
        """
        return {edge.f2.field_path for edge in self.incoming_edges}

    @property
    def dependent_identity_fields(self) -> bool:
        """If the current collection needs inputs from other collections, in addition to its seed data."""
        for field in self.grouped_fields:
            if self.collection.field(FieldPath(field)).identity:  # type: ignore
                return True
        return False

    def get_log_context(self) -> Dict[LoggerContextKeys, Any]:
        return {LoggerContextKeys.collection: self.collection.name}

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

    def typed_filtered_values(self, input_data: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Return a filtered list of key/value sets of data items that are both in
        the list of incoming edge fields, and contain data in the input data set.

        The values are cast based on field types, if those types are specified.
        """
        out = {}
        for key, values in input_data.items():
            path: FieldPath = FieldPath.parse(key)
            field: Optional[Field] = self.collection.field(path)

            if field and path in self.query_field_paths and isinstance(values, list):
                cast_values = [field.cast(v) for v in values]
                filtered = list(filter(lambda x: x is not None, cast_values))
                if filtered:
                    out[key] = filtered
        return out

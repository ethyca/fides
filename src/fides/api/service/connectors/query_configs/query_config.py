# pylint: disable=too-many-lines
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

import pydash
from loguru import logger
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.sql import Executable  # type: ignore
from sqlalchemy.sql.elements import TextClause

from fides.api.common_exceptions import MissingNamespaceSchemaException
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    CollectionAddress,
    Field,
    FieldPath,
    MaskingTruncation,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta
from fides.api.schemas.policy import ActionType
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.service.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)
from fides.api.task.refine_target_path import (
    build_refined_target_paths,
    join_detailed_path,
)
from fides.api.util.collection_util import Row, append, filter_nonempty_values
from fides.api.util.logger import Pii
from fides.api.util.querytoken import QueryToken

T = TypeVar("T")


class QueryConfig(Generic[T], ABC):
    """A wrapper around a resource-type dependent query object that can generate runnable queries
    and string representations."""

    def __init__(self, node: ExecutionNode):
        self.node = node

    @property
    def partitioning(self) -> Optional[Dict]:  # pylint: disable=R1711
        # decided to de-scope partitioning support to only bigquery as this grew more complex,
        # but keeping more generic support stubbed out feels like a reasonable step.
        if self.node.collection.partitioning:
            logger.warning(
                "Partitioning is only supported on BigQuery connectors at this time!"
            )
        return None

    def field_map(self) -> Dict[FieldPath, Field]:
        """Flattened FieldPaths of interest from this traversal_node."""
        return self.node.collection.field_dict

    def top_level_field_map(self) -> Dict[FieldPath, Field]:
        """Top level FieldPaths on this traversal_node."""
        return self.node.collection.top_level_field_dict

    def build_rule_target_field_paths(
        self, policy: Policy
    ) -> Dict[Rule, List[FieldPath]]:
        """
        Return dictionary of rules mapped to update-able field paths on a given collection
        Example:
        {<fides.api.models.policy.Rule object at 0xffff9160e190>: [FieldPath('name'), FieldPath('code'), FieldPath('ccn')]}
        """
        rule_updates: Dict[Rule, List[FieldPath]] = {}
        for rule in policy.rules:  # type: ignore[attr-defined]
            if rule.action_type != ActionType.erasure:
                continue
            rule_categories: List[str] = rule.get_target_data_categories()
            if not rule_categories:
                continue

            targeted_field_paths = []
            collection_categories: Dict[
                str, List[FieldPath]
            ] = self.node.collection.field_paths_by_category  # type: ignore
            for rule_cat in rule_categories:
                for collection_cat, field_paths in collection_categories.items():
                    if collection_cat.startswith(rule_cat):
                        targeted_field_paths.extend(field_paths)
            rule_updates[rule] = targeted_field_paths

        return rule_updates

    @property
    def primary_key_field_paths(self) -> Dict[FieldPath, Field]:
        """Mapping of FieldPaths to Fields that are marked as PK's"""
        return {
            field_path: field
            for field_path, field in self.field_map().items()
            if field.primary_key
        }

    def query_sources(self) -> Dict[str, List[CollectionAddress]]:
        """Display the input collection(s) for each query key for display purposes.

        {'user_info.user_id': [postgres_db:users]}

        Translate keys from field paths to string values
        """
        data: Dict[str, List[CollectionAddress]] = {}
        for edge in self.node.incoming_edges:
            append(data, edge.f2.field_path.string_path, edge.f1.collection_address())
        return data

    def display_query_data(self) -> Dict[str, Any]:
        """Data to represent a display (dry-run) query. Since we don't know
        what data is available, just generate a query where the input identity
        values are assumed to be present and singular and all other values that
        may be multiple are represented by a pair [?,?]"""

        data = {}
        t = QueryToken()

        for field_str, input_collection_address in self.query_sources().items():
            if (
                len(input_collection_address) == 1
                and input_collection_address[0] == ROOT_COLLECTION_ADDRESS
            ):
                data[field_str] = [t]
            else:
                data[field_str] = [
                    t,
                    QueryToken(),
                ]  # intentionally want a second instance so that set does not collapse into 1 value

        return data

    def update_value_map(  # pylint: disable=R0914
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> Dict[str, Any]:
        """Map the relevant field (as strings) to be updated on the row with their masked values from Policy Rules

        Example return:  {'name': None, 'ccn': None, 'code': None, 'workplace_info.employer': None, 'children.0': None}

        In this example, a Null Masking Strategy was used to determine that the name/ccn/code fields, nested
        workplace_info.employer field, and the first element in 'children' for a given customer_id will be replaced
        with null values.

        """
        rule_to_collection_field_paths: Dict[Rule, List[FieldPath]] = (
            self.build_rule_target_field_paths(policy)
        )

        value_map: Dict[str, Any] = {}
        for rule, field_paths in rule_to_collection_field_paths.items():
            strategy_config = rule.masking_strategy
            if not strategy_config:
                continue
            for rule_field_path in field_paths:
                strategy: MaskingStrategy = MaskingStrategy.get_strategy(
                    strategy_config["strategy"], strategy_config["configuration"]
                )
                truncation: MaskingTruncation = [
                    MaskingTruncation(field.data_type_converter, field.length)
                    for field_path, field in self.field_map().items()
                    if field_path == rule_field_path
                ][0]
                field = self.field_map().get(rule_field_path)
                if field and field.masking_strategy_override:
                    masking_strategy_override = field.masking_strategy_override
                    strategy = MaskingStrategy.get_strategy(
                        masking_strategy_override.strategy,
                        masking_strategy_override.configuration,  # type: ignore[arg-type]
                    )
                    logger.warning(
                        f"Using field-level masking override of type '{strategy.name}' for {rule_field_path.string_path}"
                    )
                null_masking: bool = strategy.name == NullMaskingStrategy.name
                if not self._supported_data_type(truncation, null_masking, strategy):
                    logger.warning(
                        "Unable to generate a query for field {}: data_type is either not present on the field or not supported for the {} masking strategy. Received data type: {}",
                        rule_field_path.string_path,
                        strategy.name,
                        truncation.data_type_converter.name,  # type: ignore
                    )
                    continue

                paths_to_mask: List[str] = [
                    join_detailed_path(path)
                    for path in build_refined_target_paths(
                        row, query_paths={rule_field_path: None}
                    )
                ]
                for detailed_path in paths_to_mask:
                    value_map[detailed_path] = self._generate_masked_value(
                        request_id=request.id,
                        strategy=strategy,
                        val=pydash.objects.get(row, detailed_path),
                        masking_truncation=truncation,
                        null_masking=null_masking,
                        str_field_path=detailed_path,
                    )
        return value_map

    @staticmethod
    def _supported_data_type(
        masking_truncation: MaskingTruncation,
        null_masking: bool,
        strategy: MaskingStrategy,
    ) -> bool:
        """Helper method to determine whether given data_type exists and is supported by the masking strategy"""
        if null_masking:
            return True
        if not masking_truncation.data_type_converter:
            return False
        if not strategy.data_type_supported(
            data_type=masking_truncation.data_type_converter.name
        ):
            return False
        return True

    @staticmethod
    def _generate_masked_value(  # pylint: disable=R0913
        request_id: str,
        strategy: MaskingStrategy,
        val: Any,
        masking_truncation: MaskingTruncation,
        null_masking: bool,
        str_field_path: str,
    ) -> T:
        # masking API takes and returns lists, but here we are only leveraging single elements
        masked_val = strategy.mask([val], request_id)[0]  # type: ignore

        logger.debug(
            "Generated the following masked val for field {}: {}",
            str_field_path,
            masked_val,
        )

        # special case for null masking
        if null_masking:
            return masked_val

        if masking_truncation.length:
            logger.warning(
                "Because a length has been specified for field {}, we will truncate length of masked value to match, regardless of masking strategy",
                str_field_path,
            )
            #  for strategies other than null masking we assume that masked data type is the same as specified data type
            masked_val = masking_truncation.data_type_converter.truncate(  # type: ignore
                masking_truncation.length, masked_val
            )
        return masked_val

    @abstractmethod
    def generate_query(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy]
    ) -> Optional[T]:
        """Generate a retrieval query. If there is no data to be queried
        (for example, if the policy identifies no fields to be queried)
        returns None"""

    @abstractmethod
    def query_to_str(self, t: T, input_data: Dict[str, List[Any]]) -> Optional[str]:
        """Convert query to string"""

    @abstractmethod
    def dry_run_query(self) -> Optional[str]:
        """dry run query for display"""

    @abstractmethod
    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> Optional[T]:
        """Generate an update statement. If there is no data to be updated
        (for example, if the policy identifies no fields to be updated)
        returns None"""


class SQLLikeQueryConfig(QueryConfig[T], ABC):
    """
    Abstract query config for SQL-like languages (that may not be strictly SQL).
    """

    namespace_meta_schema: Optional[Type[NamespaceMeta]] = None

    def __init__(self, node: ExecutionNode, namespace_meta: Optional[Dict] = None):
        super().__init__(node)
        self.namespace_meta: Optional[NamespaceMeta] = None

        if namespace_meta is not None:
            if self.namespace_meta_schema is None:
                raise MissingNamespaceSchemaException(
                    f"{self.__class__.__name__} must define a namespace_meta_schema when namespace_meta is provided."
                )
            try:
                self.namespace_meta = self.namespace_meta_schema.model_validate(
                    namespace_meta
                )
            except ValidationError as exc:
                raise ValueError(f"Invalid namespace_meta: {exc}")

    def format_fields_for_query(
        self,
        field_paths: List[FieldPath],
    ) -> List[str]:
        """Returns field paths in a format they can be added into SQL queries.

        This currently takes no nesting into account and only returns the
        last value from each key. It will need to be updated to support
        nested values.
        """
        return [fk.levels[-1] for fk in field_paths]

    @abstractmethod
    def format_query_data_name(self, query_data_name: str) -> str:
        """Returns query_data_name formatted according to specific SQL dialect"""

    @abstractmethod
    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns a SQL query string."""

    @abstractmethod
    def format_clause_for_query(
        self, string_path: str, operator: str, operand: str
    ) -> str:
        """Returns clause formatted in the specific SQL dialect for the query"""

    def generate_raw_query_without_tuples(
        self, field_list: List[str], filters: Dict[str, List[Any]]
    ) -> Optional[T]:
        """
        Generate a raw query using the provided field_list and filters,
        i.e a query of the form:
        SELECT <field_list> FROM <collection> WHERE <filters>

        Generates distinct key/val pairs for building the query string instead of a tuple.

        E.g. SQLQueryConfig uses 1 key as a tuple:
        SELECT order_id,product_id,quantity FROM order_item WHERE order_id IN (:some-params-in-tuple)
        which for some connectors gets interpreted as data types (mssql) or quotes (bigquery).

        This method produces distinct keys for the query_str:
        SELECT order_id,product_id,quantity FROM order_item WHERE order_id IN (:_in_stmt_generated_0, :_in_stmt_generated_1, :_in_stmt_generated_2)

        """
        clauses = []
        query_data: Dict[str, Tuple[Any, ...]] = {}
        for field_name, field_value in filters.items():
            data = set(field_value)
            if len(data) == 1:
                clauses.append(
                    self.format_clause_for_query(field_name, "=", field_name)
                )
                query_data[field_name] = data.pop()
            elif len(data) > 1:
                data_vals = list(data)
                query_data_keys: List[str] = []
                for val in data_vals:
                    # appending "_in_stmt_generated_" (can be any arbitrary str) so that this name has less change of conflicting with pre-existing column in table
                    query_data_name = (
                        field_name + "_in_stmt_generated_" + str(data_vals.index(val))
                    )
                    query_data[query_data_name] = val
                    query_data_keys.append(self.format_query_data_name(query_data_name))
                operand = ", ".join(query_data_keys)
                clauses.append(self.format_clause_for_query(field_name, "IN", operand))

        if len(clauses) > 0:
            formatted_fields = ", ".join(field_list)
            query_str = self.get_formatted_query_string(formatted_fields, clauses)
            return self.format_query_stmt(query_str, query_data)

        return None

    def generate_query_without_tuples(  # pylint: disable=R0914
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy] = None,
    ) -> Optional[T]:
        """
        Generate a retrieval query. Generates distinct key/val pairs for building the query string instead of a tuple.

        E.g. SQLQueryConfig uses 1 key as a tuple:
        SELECT order_id,product_id,quantity FROM order_item WHERE order_id IN (:some-params-in-tuple)
        which for some connectors gets interpreted as data types (mssql) or quotes (bigquery).

        This override produces distinct keys for the query_str:
        SELECT order_id,product_id,quantity FROM order_item WHERE order_id IN (:_in_stmt_generated_0, :_in_stmt_generated_1, :_in_stmt_generated_2)
        """
        filtered_data = self.node.typed_filtered_values(input_data)

        if filtered_data:
            formatted_fields = self.format_fields_for_query(
                list(self.field_map().keys())
            )

            return self.generate_raw_query_without_tuples(
                formatted_fields, filtered_data
            )

        logger.warning(
            "There is not enough data to generate a valid query for {}",
            self.node.address,
        )
        return None

    def get_update_stmt(
        self,
        update_clauses: List[str],
        pk_clauses: List[str],
    ) -> str:
        """Returns a SQL UPDATE statement to fit SQL syntax."""
        return f"UPDATE {self.node.address.collection} SET {', '.join(update_clauses)} WHERE {' AND '.join(pk_clauses)}"

    @abstractmethod
    def get_update_clauses(
        self, update_value_map: Dict[str, Any], non_empty_primary_keys: Dict[str, Field]
    ) -> List[str]:
        """Returns a list of update clauses for the update statement."""

    @abstractmethod
    def format_query_stmt(self, query_str: str, update_value_map: Dict[str, Any]) -> T:
        """Returns a formatted update statement in the appropriate dialect."""

    @abstractmethod
    def format_key_map_for_update_stmt(self, fields: List[str]) -> List[str]:
        """Adds the appropriate formatting for update statements in this datastore."""

    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> Optional[T]:
        """Returns an update statement in generic SQL-ish dialect."""
        update_value_map: Dict[str, Any] = self.update_value_map(row, policy, request)
        non_empty_primary_keys: Dict[str, Field] = filter_nonempty_values(
            {
                fpath.string_path: fld.cast(row[fpath.string_path])
                for fpath, fld in self.primary_key_field_paths.items()
                if fpath.string_path in row
            }
        )

        update_clauses = self.get_update_clauses(
            update_value_map, non_empty_primary_keys
        )
        pk_clauses = self.format_key_map_for_update_stmt(
            list(non_empty_primary_keys.keys())
        )

        for k, v in non_empty_primary_keys.items():
            update_value_map[k] = v

        valid = len(pk_clauses) > 0 and len(update_clauses) > 0
        if not valid:
            logger.warning(
                "There is not enough data to generate a valid update statement for {}",
                self.node.address,
            )
            return None

        query_str = self.get_update_stmt(
            update_clauses,
            pk_clauses,
        )
        logger.info("query = {}, params = {}", Pii(query_str), Pii(update_value_map))
        return self.format_query_stmt(query_str, update_value_map)


class SQLQueryConfig(SQLLikeQueryConfig[Executable]):
    """Query config that translates parameters into SQL statements."""

    def generate_raw_query(
        self, field_list: List[str], filters: Dict[str, List[Any]]
    ) -> Optional[TextClause]:
        """
        Generate a raw query using the provided field_list and filters,
        i.e a query of the form:
        SELECT <field_list> FROM <collection> WHERE <filters>
        """
        clauses = []
        query_data: Dict[str, Tuple[Any, ...]] = {}
        for field_name, field_value in filters.items():
            data = set(field_value)
            if len(data) == 1:
                clauses.append(
                    self.format_clause_for_query(field_name, "=", field_name)
                )
                query_data[field_name] = (data.pop(),)
            elif len(data) > 1:
                clauses.append(
                    self.format_clause_for_query(field_name, "IN", field_name)
                )
                query_data[field_name] = tuple(data)

        if len(clauses) > 0:
            formatted_fields = ", ".join(field_list)
            query_str = self.get_formatted_query_string(formatted_fields, clauses)
            return text(query_str).params(query_data)

        return None

    def format_clause_for_query(
        self, string_path: str, operator: str, operand: str
    ) -> str:
        """Returns clauses in a format they can be added into SQL queries."""
        return f"{string_path} {operator} :{operand}"

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns an SQL query string."""
        return f"SELECT {field_list} FROM {self.node.collection.name} WHERE {' OR '.join(clauses)}"

    def generate_query(
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy] = None,
    ) -> Optional[TextClause]:
        """Generate a retrieval query"""
        filtered_data: Dict[str, Any] = self.node.typed_filtered_values(input_data)

        if filtered_data:
            formatted_fields: List[str] = self.format_fields_for_query(
                list(self.field_map().keys())
            )

            return self.generate_raw_query(formatted_fields, filtered_data)

        logger.warning(
            "There is not enough data to generate a valid query for {}",
            self.node.address,
        )
        return None

    def format_key_map_for_update_stmt(self, fields: List[str]) -> List[str]:
        """Adds the appropriate formatting for update statements in this datastore."""
        fields.sort()
        return [f"{k} = :{k}" for k in fields]

    def get_update_clauses(
        self, update_value_map: Dict[str, Any], non_empty_primary_keys: Dict[str, Field]
    ) -> List[str]:
        """Returns a list of update clauses for the update statement."""
        return self.format_key_map_for_update_stmt(list(update_value_map.keys()))

    def format_query_stmt(
        self, query_str: str, update_value_map: Dict[str, Any]
    ) -> Executable:
        """Returns a formatted update statement in the appropriate dialect."""
        return text(query_str).params(update_value_map)

    def query_to_str(self, t: TextClause, input_data: Dict[str, List[Any]]) -> str:
        """string representation of a query for logging/dry-run"""

        def transform_param(p: Any) -> str:
            if isinstance(p, str):
                return f"'{p}'"
            return str(p)

        query_str = str(t)
        for k, v in input_data.items():
            if len(v) == 1:
                query_str = re.sub(f"= :{k}", f"= {transform_param(v[0])}", query_str)
            elif len(v) > 0:
                query_str = re.sub(f"IN :{k}", f"IN { tuple(set(v)) }", query_str)
        return query_str

    def dry_run_query(self) -> Optional[str]:
        """Returns a text representation of the query."""
        query_data = self.display_query_data()
        text_clause = self.generate_query(query_data, None)
        if text_clause is not None:
            return self.query_to_str(text_clause, query_data)
        return None

    def format_query_data_name(self, query_data_name: str) -> str:
        return f":{query_data_name}"


class QueryStringWithoutTuplesOverrideQueryConfig(SQLQueryConfig):
    """
    Generates SQL valid for connectors that require the query string to be built without tuples.
    """

    # Overrides SQLQueryConfig.generate_raw_query
    def generate_raw_query(
        self, field_list: List[str], filters: Dict[str, List[Any]]
    ) -> Optional[TextClause]:
        """
        Allows executing a somewhat raw query where the field_list and filters do not depend
        on the Node or Graph structure.
        """
        clauses = []
        query_data = {}
        for field_name, field_value in filters.items():
            data = set(field_value)
            if len(data) == 1:
                clauses.append(
                    self.format_clause_for_query(field_name, "=", field_name)
                )
                query_data[field_name] = data.pop()
            elif len(data) > 1:
                data_vals = list(data)
                query_data_keys: List[str] = []
                for val in data_vals:
                    # appending "_in_stmt_generated_" (can be any arbitrary str) so that this name has lower chance of conflicting with pre-existing column in table
                    query_data_name = (
                        field_name + "_in_stmt_generated_" + str(data_vals.index(val))
                    )
                    query_data[query_data_name] = val
                    query_data_keys.append(self.format_query_data_name(query_data_name))
                operand = ", ".join(query_data_keys)
                clauses.append(self.format_clause_for_query(field_name, "IN", operand))

        if len(clauses) > 0:
            formatted_fields = ", ".join(field_list)
            query_str = self.get_formatted_query_string(formatted_fields, clauses)
            return text(query_str).params(query_data)

        return None

    # Overrides SQLConnector.format_clause_for_query
    def format_clause_for_query(
        self, string_path: str, operator: str, operand: str
    ) -> str:
        """
        Returns clauses in a format they can be added into SQL queries.
        Expects the operand of IN statements to be formatted in the following manner so that
        these distinct keys can be appended to the clause:
        ":_in_stmt_generated_0, :_in_stmt_generated_1, :_in_stmt_generated_2"
        """
        if operator == "IN":
            return f"{string_path} IN ({operand})"
        return super().format_clause_for_query(string_path, operator, operand)

    # Overrides SQLConnector.generate_query
    def generate_query(  # pylint: disable=R0914
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy] = None,
    ) -> Optional[TextClause]:
        """
        Generate a retrieval query. Generates distinct key/val pairs for building the query string instead of a tuple.

        E.g. The base SQLQueryConfig uses 1 key as a tuple:
        SELECT order_id,product_id,quantity FROM order_item WHERE order_id IN (:some-params-in-tuple)
        which for some connectors gets interpreted as data types (mssql) or quotes (bigquery).

        This override produces distinct keys for the query_str:
        SELECT order_id,product_id,quantity FROM order_item WHERE order_id IN (:_in_stmt_generated_0, :_in_stmt_generated_1, :_in_stmt_generated_2)
        """
        return self.generate_query_without_tuples(input_data, policy)

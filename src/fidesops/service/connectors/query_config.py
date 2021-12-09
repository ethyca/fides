import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Set, Optional, Generic, TypeVar, Tuple

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

from fidesops.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    CollectionAddress,
    Field,
    MaskingOverride,
)
from fidesops.graph.data_type import DataTypeConverter
from fidesops.graph.traversal import TraversalNode, Row
from fidesops.models.policy import Policy, ActionType, Rule
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_nullify import NULL_REWRITE
from fidesops.util.querytoken import QueryToken
from fidesops.service.masking.strategy.masking_strategy_factory import (
    get_strategy,
)
from fidesops.util.collection_util import append, filter_nonempty_values

logger = logging.getLogger(__name__)
T = TypeVar("T")


class QueryConfig(Generic[T], ABC):
    """A wrapper around a resource-type dependant query object that can generate runnable queries and string representations."""

    def __init__(self, node: TraversalNode):
        self.node = node

    @property
    def fields(self) -> List[str]:
        """Fields of interest from this traversal traversal_node."""
        return [f.name for f in self.node.node.collection.fields]

    def build_rule_target_fields(self, policy: Policy) -> Dict[Rule, List[str]]:
        """
        Return dictionary of rules mapped to update-able field names on a given collection
        Example:
        {<fidesops.models.policy.Rule object at 0xffff9160e190>: ['name', 'code', 'ccn']}
        """
        rule_updates: Dict[Rule, List[str]] = {}
        for rule in policy.rules:
            if rule.action_type != ActionType.erasure:
                continue
            rule_categories = rule.get_target_data_categories()
            if not rule_categories:
                continue

            targeted_fields = []
            collection_categories = self.node.node.collection.fields_by_category
            for rule_cat in rule_categories:
                for collection_cat, fields in collection_categories.items():
                    if collection_cat.startswith(rule_cat):
                        targeted_fields.extend(fields)
            rule_updates[rule] = targeted_fields

        return rule_updates

    @property
    def primary_key_fields(self) -> List[Field]:
        """List of fields marked as primary keys"""
        return [f for f in self.node.node.collection.fields if f.primary_key]

    @property
    def query_keys(self) -> Set[str]:
        """
        All of the possible keys that we can query for possible filter values.
        These are keys that are the ends of incoming edges.
        """
        return set(map(lambda edge: edge.f2.field, self.node.incoming_edges()))

    def typed_filtered_values(self, input_data: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Return a filtered list of key/value sets of data items that are both in
        the list of incoming edge fields, and contain data in the input data set.

        The values are cast based on field types, if those types are specified.
        """

        out = {}
        for key, values in input_data.items():
            field = self.node.node.collection.field(key)
            if field and key in self.query_keys and isinstance(values, list):
                cast_values = [field.cast(v) for v in values]
                filtered = list(filter(lambda x: x is not None, cast_values))
                if filtered:
                    out[key] = filtered
        return out

    def query_sources(self) -> Dict[str, List[CollectionAddress]]:
        """Display the input sources for each query key"""
        data: Dict[str, List[CollectionAddress]] = {}
        for edge in self.node.incoming_edges():
            append(data, edge.f2.field, edge.f1.collection_address())

        return data

    def display_query_data(self) -> Dict[str, Any]:
        """Data to represent a display (dry-run) query. Since we don't know
        what data is available, just generate a query where the input identity
        values are assumed to be present and singular and all other values that
        may be multiple are represented by a pair [?,?]"""

        data = {}
        t = QueryToken()

        for k, v in self.query_sources().items():

            if len(v) == 1 and v[0] == ROOT_COLLECTION_ADDRESS:
                data[k] = [t]
            else:
                data[k] = [
                    t,
                    QueryToken(),
                ]  # intentionally want a second instance so that set does not collapse into 1 value

        return data

    def update_value_map(self, row: Row, policy: Policy) -> Dict[str, Any]:
        """Map the relevant fields to be updated on the row with their masked values from Policy Rules

        Example return:  {'name': None, 'ccn': None, 'code': None}

        In this example, a Null Masking Strategy was used to determine that the name/ccn/code fields
        for a given customer_id will be replaced with null values.

        """
        rule_to_collection_fields: Dict[
            Rule, List[str]
        ] = self.build_rule_target_fields(policy)

        value_map: Dict[str, Any] = {}
        for rule, field_names in rule_to_collection_fields.items():
            strategy_config = rule.masking_strategy
            if not strategy_config:
                continue
            strategy: MaskingStrategy = get_strategy(
                strategy_config["strategy"], strategy_config["configuration"]
            )

            for field_name in field_names:
                masking_override: MaskingOverride = [
                    MaskingOverride(field.data_type, field.length)
                    for field in self.node.node.collection.fields
                    if field.name == field_name
                ][0]
                null_masking: bool = strategy_config.get("strategy") == NULL_REWRITE
                if not self._supported_data_type(
                    masking_override, null_masking, strategy
                ):
                    logger.warning(
                        f"Unable to generate a query for field {field_name}: data_type is either not present on the field or not supported for the {strategy_config['strategy']} masking strategy. Received data type: {masking_override.data_type}"
                    )
                    continue
                val: Any = row[field_name]
                masked_val = self._generate_masked_value(
                    strategy, val, masking_override, null_masking, field_name
                )
                value_map[field_name] = masked_val
        return value_map

    @staticmethod
    def _supported_data_type(
        masking_override: MaskingOverride, null_masking: bool, strategy: MaskingStrategy
    ) -> bool:
        """Helper method to determine whether given data_type exists and is supported by the masking strategy"""
        if null_masking:
            return True
        if not masking_override.data_type:
            return False
        if not strategy.data_type_supported(data_type=masking_override.data_type.name):
            return False
        return True

    @staticmethod
    def _generate_masked_value(
        strategy: MaskingStrategy,
        val: Any,
        masking_override: MaskingOverride,
        null_masking: bool,
        field_name: str,
    ) -> T:
        masked_val = strategy.mask(val)
        logger.debug(
            f"Generated the following masked val for field {field_name}: {masked_val}"
        )
        if null_masking:
            return masked_val
        if masking_override.length:
            logger.warning(
                f"Because a length has been specified for field {field_name}, we will truncate length of masked value to match, regardless of masking strategy"
            )
            #  for strategies other than null masking we assume that masked data type is the same as specified data type
            data_type_convertor: DataTypeConverter = masking_override.data_type.value
            masked_val = data_type_convertor.truncate(
                masking_override.length, masked_val
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
    def query_to_str(self, t: T, input_data: Dict[str, List[Any]]) -> str:
        """Convert query to string"""

    @abstractmethod
    def dry_run_query(self) -> Optional[str]:
        """dry run query for display"""

    @abstractmethod
    def generate_update_stmt(self, row: Row, policy: Optional[Policy]) -> Optional[T]:
        """Generate an update statement. If there is no data to be updated
        (for example, if the policy identifies no fields to be updated)
        returns None"""


class SQLQueryConfig(QueryConfig[TextClause]):
    """Query config that translates parameters into SQL statements."""

    def format_fields_for_query(
        self,
        fields: List[str],
    ) -> List[str]:
        """Returns fields in a format they can be added into SQL queries."""
        return fields

    def format_clause_for_query(
        self,
        field_name: str,
        operator: str,
    ) -> str:
        """Returns clauses in a format they can be added into SQL queries."""
        return f"{field_name} {operator} :{field_name}"

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns an SQL query string."""
        return f"SELECT {field_list} FROM {self.node.node.collection.name} WHERE {' OR '.join(clauses)}"

    def get_formatted_update_stmt(
        self,
        update_clauses: List[str],
        pk_clauses: List[str],
    ) -> str:
        """Returns a formatted SQL UPDATE statement to fit the Snowflake syntax."""
        return f"UPDATE {self.node.address.collection} SET {','.join(update_clauses)} WHERE {' AND '.join(pk_clauses)}"

    def generate_query(
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy] = None,
    ) -> Optional[TextClause]:
        """Generate a retrieval query"""

        filtered_data = self.typed_filtered_values(input_data)

        if filtered_data:
            clauses = []
            query_data: Dict[str, Tuple[Any, ...]] = {}
            formatted_fields = self.format_fields_for_query(self.fields)
            field_list = ",".join(formatted_fields)
            for field_name, data in filtered_data.items():
                data = set(data)
                if len(data) == 1:
                    clauses.append(self.format_clause_for_query(field_name, "="))
                    query_data[field_name] = (data.pop(),)
                elif len(data) > 1:
                    clauses.append(self.format_clause_for_query(field_name, "IN"))
                    query_data[field_name] = tuple(data)
                else:
                    #  if there's no data, create no clause
                    pass
            if len(clauses) > 0:
                query_str = self.get_formatted_query_string(field_list, clauses)
                return text(query_str).params(query_data)

        logger.warning(
            f"There is not enough data to generate a valid query for {self.node.address}"
        )
        return None

    def format_key_map_for_update_stmt(self, key_map: Dict[str, Any]) -> List[str]:
        """Adds the appropriate formatting for update statements in this datastore."""
        return [f"{k} = :{k}" for k in key_map]

    def generate_update_stmt(self, row: Row, policy: Policy) -> Optional[TextClause]:
        """Returns an update statement in generic SQL dialect."""
        update_value_map = self.update_value_map(row, policy)
        update_clauses = self.format_key_map_for_update_stmt(update_value_map)
        non_empty_primary_keys = filter_nonempty_values(
            {
                f.name: f.cast(row[f.name])
                for f in self.primary_key_fields
                if f.name in row
            }
        )
        pk_clauses = self.format_key_map_for_update_stmt(non_empty_primary_keys)

        for k, v in non_empty_primary_keys.items():
            update_value_map[k] = v

        valid = len(pk_clauses) > 0 and len(update_clauses) > 0
        if not valid:
            logger.warning(
                f"There is not enough data to generate a valid update statement for {self.node.address}"
            )
            return None

        query_str = self.get_formatted_update_stmt(
            update_clauses,
            pk_clauses,
        )
        logger.info("query = %s, params = %s", query_str, update_value_map)
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


class SnowflakeQueryConfig(SQLQueryConfig):
    """Generates SQL in Snowflake's custom dialect."""

    def format_fields_for_query(
        self,
        fields: List[str],
    ) -> List[str]:
        """Returns fields surrounded by quotation marks as required by Snowflake syntax."""
        return [f'"{field}"' for field in fields]

    def format_clause_for_query(
        self,
        field_name: str,
        operator: str,
    ) -> str:
        """Returns field names in clauses surrounded by quotation marks as required by Snowflake syntax."""
        return f'"{field_name}" {operator} (:{field_name})'

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns a query string with double quotation mark formatting as required by Snowflake syntax."""
        return f'SELECT {field_list} FROM "{self.node.node.collection.name}" WHERE {" OR ".join(clauses)}'

    def format_key_map_for_update_stmt(self, key_map: Dict[str, Any]) -> List[str]:
        """Adds the appropriate formatting for update statements in this datastore."""
        return [f'"{k}" = :{k}' for k in key_map]

    def get_formatted_update_stmt(
        self,
        update_clauses: List[str],
        pk_clauses: List[str],
    ) -> str:
        """Returns a parameterised update statement in Snowflake dialect."""
        return f'UPDATE "{self.node.address.collection}" SET {",".join(update_clauses)} WHERE  {" AND ".join(pk_clauses)}'


MongoStatement = Tuple[Dict[str, Any], Dict[str, Any]]
"""A mongo query is expressed in the form of 2 dicts, the first of which represents
  the query object(s) and the second of which represents fields to return.
  e.g. 'collection.find({k1:v1, k2:v2},{f1:1, f2:1 ... })'. This is returned as
  a tuple ({k1:v1, k2:v2},{f1:1, f2:1 ... }).

  An update statement takes the form
  collection.update_one({k1:v1},{k2:v2}...}, {$set: {f1:fv1, f2:fv2 ... }}, upsert=False).
  This is returned as a tuple
  ({k1:v1},{k2:v2}...},  {f1:fv1, f2: fv2 ... }
  """


class MongoQueryConfig(QueryConfig[MongoStatement]):
    """Query config that translates parameters into mongo statements"""

    def generate_query(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy] = None
    ) -> Optional[MongoStatement]:
        def transform_query_pairs(pairs: Dict[str, Any]) -> Dict[str, Any]:
            """Since we want to do an 'OR' match in mongo, transform queries of the form
            {A:1, B:2} => "{$or:[{A:1},{B:2}]}".
            Don't bother to do this if the pairs size is 1
            """
            if len(pairs) < 2:
                return pairs
            return {"$or": [dict([(k, v)]) for k, v in pairs.items()]}

        if input_data:
            filtered_data = self.typed_filtered_values(input_data)
            if filtered_data:
                field_list = {field_name: 1 for field_name in self.fields}
                query_pairs = {}
                for field_name, data in filtered_data.items():

                    if len(data) == 1:
                        query_pairs[field_name] = data[0]

                    elif len(data) > 1:
                        query_pairs[field_name] = {"$in": data}

                    else:
                        #  if there's no data, create no clause
                        pass
                query_fields, return_fields = (
                    transform_query_pairs(query_pairs),
                    field_list,
                )
                return query_fields, return_fields

        logger.warning(
            f"There is not enough data to generate a valid query for {self.node.address}"
        )
        return None

    def generate_update_stmt(
        self, row: Row, policy: Optional[Policy] = None
    ) -> Optional[MongoStatement]:
        """Generate a SQL update statement in the form of Mongo update statement components"""
        update_clauses = self.update_value_map(row, policy)

        pk_clauses = filter_nonempty_values(
            {k.name: k.cast(row[k.name]) for k in self.primary_key_fields}
        )

        valid = len(pk_clauses) > 0 and len(update_clauses) > 0
        if not valid:
            logger.warning(
                f"There is not enough data to generate a valid update for {self.node.address}"
            )
            return None
        return pk_clauses, {"$set": update_clauses}

    def query_to_str(self, t: MongoStatement, input_data: Dict[str, List[Any]]) -> str:
        """string representation of a query for logging/dry-run"""
        query_data, field_list = t
        db_name = self.node.address.dataset
        collection_name = self.node.address.collection
        return f"db.{db_name}.{collection_name}.find({query_data}, {field_list})"

    def dry_run_query(self) -> Optional[str]:
        data = self.display_query_data()
        mongo_query = self.generate_query(self.display_query_data(), None)
        if mongo_query is not None:
            return self.query_to_str(mongo_query, data)
        return None

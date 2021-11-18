import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Set, Optional, Generic, TypeVar, Tuple

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

from fidesops.graph.config import ROOT_COLLECTION_ADDRESS, CollectionAddress
from fidesops.graph.traversal import TraversalNode, Row
from fidesops.models.policy import Policy, ActionType, Rule
from fidesops.service.masking.strategy.masking_strategy_factory import get_strategy
from fidesops.util.collection_util import append

logger = logging.getLogger(__name__)
T = TypeVar("T")


class QueryConfig(Generic[T], ABC):
    """A wrapper around a resource-type dependant query object that can generate runnable queries and string representations."""

    class QueryToken:
        """A placeholder token for query output"""

        def __str__(self) -> str:
            return "?"

        def __repr__(self) -> str:
            return "?"

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
    def primary_keys(self) -> List[str]:
        """List of fields marked as primary keys"""
        return [f.name for f in self.node.node.collection.fields if f.primary_key]

    @property
    def query_keys(self) -> Set[str]:
        """
        All of the possible keys that we can query for possible filter values.
        These are keys that are the ends of incoming edges.
        """
        return set(map(lambda edge: edge.f2.field, self.node.incoming_edges()))

    def filter_values(self, input_data: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Return a filtered list of key/value sets of data items that are both in
        the list of incoming edge fields, and contain data in the input data set
        """
        return {
            key: value
            for (key, value) in input_data.items()
            if key in self.query_keys
            and isinstance(value, list)
            and len(value)
            and None not in value
        }

    def query_sources(self) -> Dict[str, List[CollectionAddress]]:
        """Display the input sources for each query key"""
        data: Dict[str, List[CollectionAddress]] = {}
        for edge in self.node.incoming_edges():
            append(data, edge.f2.field, edge.f1.collection_address())

        return data

    def display_query_data(self) -> Dict[str, Any]:
        """Data to represent a display (dry-run) query. Since we don't know
        what data is available, just generate a query where the input identity
        values are assumed to be present and singulur and all other values that
        may be multiple are represented by a pair [?,?]"""

        data = {}
        t = QueryConfig.QueryToken()

        for k, v in self.query_sources().items():

            if len(v) == 1 and v[0] == ROOT_COLLECTION_ADDRESS:
                data[k] = [t]
            else:
                data[k] = [
                    t,
                    QueryConfig.QueryToken(),
                ]  # intentionally want a second instance so that set does not collapse into 1 value

        return data

    def update_value_map(self, row: Row, policy: Policy) -> Dict[str, Any]:
        """Map the relevant fields to be updated on the row with their masked values from Policy Rules

        Example return:  {'name': None, 'ccn': None, 'code': None}

        In this example, a Null Masking Strategy was used to determine that the name/ccn/code fields
        for a given customer_id will be replaced with null values.

        """
        rule_to_collection_fields = self.build_rule_target_fields(policy)

        value_map: Dict[str, Any] = {}
        for rule, field_names in rule_to_collection_fields.items():
            strategy_config = rule.masking_strategy
            strategy = get_strategy(
                strategy_config["strategy"], strategy_config["configuration"]
            )

            for field_name in field_names:
                value_map[field_name] = strategy.mask(row[field_name])
        return value_map

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

    def generate_query(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy] = None
    ) -> Optional[TextClause]:
        """Generate a retrieval query"""

        filtered_data = self.filter_values(input_data)

        if filtered_data:
            clauses = []
            query_data: Dict[str, Tuple[Any, ...]] = {}
            field_list = ",".join(self.fields)
            for field_name, data in filtered_data.items():
                if len(data) == 1:
                    clauses.append(f"{field_name} = :{field_name}")
                    query_data[field_name] = (data[0],)
                elif len(data) > 1:
                    clauses.append(f"{field_name} IN :{field_name}")
                    query_data[field_name] = tuple(set(data))
                else:
                    #  if there's no data, create no clause
                    pass
            if len(clauses) > 0:
                query_str = f"SELECT {field_list} FROM {self.node.node.collection.name} WHERE {' OR '.join(clauses)}"
                return text(query_str).params(query_data)

        logger.warning(
            f"There is not enough data to generate a valid query for {self.node.address}"
        )
        return None

    def generate_update_stmt(self, row: Row, policy: Policy) -> Optional[TextClause]:
        update_value_map = self.update_value_map(row, policy)
        update_clauses = [f"{k} = :{k}" for k in update_value_map]
        pk_clauses = [f"{k} = :{k}" for k in self.primary_keys]

        for pk in self.primary_keys:
            update_value_map[pk] = row[pk]

        valid = len(pk_clauses) > 0 and len(update_clauses) > 0
        if not valid:
            logger.warning(
                f"There is not enough data to generate a valid update statement for {self.node.address}"
            )
            return None
        query_str = f"UPDATE {self.node.address.collection} SET {','.join(update_clauses)} WHERE  {','.join(pk_clauses)}"
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
        query_data = self.display_query_data()
        text_clause = self.generate_query(query_data, None)
        if text_clause is not None:
            return self.query_to_str(text_clause, query_data)
        return None


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
    """Query config that translates paramters into mongo statements"""

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
            filtered_data = self.filter_values(input_data)
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
        pk_clauses = {k: row[k] for k in self.primary_keys}

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

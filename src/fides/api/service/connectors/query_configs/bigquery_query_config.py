from typing import Any, Dict, List, Optional, Union, cast

from fideslang.models import MaskingStrategies
from loguru import logger
from sqlalchemy import MetaData, Table, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Delete, Update  # type: ignore
from sqlalchemy.sql.elements import ColumnElement, TextClause

from fides.api.graph.config import Field, FieldPath
from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.namespace_meta.bigquery_namespace_meta import (
    BigQueryNamespaceMeta,
)
from fides.api.service.connectors.query_configs.query_config import (
    QueryStringWithoutTuplesOverrideQueryConfig,
)
from fides.api.util.collection_util import Row, filter_nonempty_values


class BigQueryQueryConfig(QueryStringWithoutTuplesOverrideQueryConfig):
    """
    Generates SQL valid for BigQuery
    """

    namespace_meta_schema = BigQueryNamespaceMeta

    @property
    def partitioning(self) -> Optional[Dict]:
        # Overriden from base implementation to allow for _only_ BQ partitioning, for now
        return self.node.collection.partitioning

    def get_partition_clauses(
        self,
    ) -> List[str]:
        """
        Returns the WHERE clauses specified in the partitioning spec

        Currently, only where-clause based partitioning is supported.

        TODO: derive partitions from a start/end/interval specification


        NOTE: when we deprecate `where_clause` partitioning in favor of a more proper partitioning DSL,
        we should be sure to still support the existing `where_clause` partition definition on
        any in-progress DSRs so that they can run through to completion.
        """
        partition_spec = self.partitioning
        if not partition_spec:
            logger.error(
                "Partitioning clauses cannot be retrieved, no partitioning specification found"
            )
            return []

        if where_clauses := partition_spec.get("where_clauses"):
            return where_clauses

        # TODO: implement more advanced partitioning support!

        raise ValueError(
            "`where_clauses` must be specified in partitioning specification!"
        )

    def _generate_table_name(self) -> str:
        """
        Prepends the dataset ID and project ID to the base table name
        if the BigQuery namespace meta is provided.
        """

        table_name = self.node.collection.name
        if self.namespace_meta:
            bigquery_namespace_meta = cast(BigQueryNamespaceMeta, self.namespace_meta)
            table_name = f"{bigquery_namespace_meta.dataset_id}.{table_name}"
            if project_id := bigquery_namespace_meta.project_id:
                table_name = f"{project_id}.{table_name}"
        return table_name

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """
        Returns a query string with backtick formatting for tables that have the same names as
        BigQuery reserved words.
        """
        return f'SELECT {field_list} FROM `{self._generate_table_name()}` WHERE ({" OR ".join(clauses)})'

    def generate_masking_stmt(
        self,
        node: ExecutionNode,
        row: Row,
        policy: Policy,
        request: PrivacyRequest,
        client: Engine,
    ) -> Union[List[Update], List[Delete]]:
        """
        Generate a masking statement for BigQuery.

        If a masking override is present, it will take precedence over the policy masking strategy.
        """

        masking_override = node.collection.masking_strategy_override
        if masking_override and masking_override.strategy == MaskingStrategies.DELETE:
            logger.info(
                f"Masking override detected for collection {node.address.value}: {masking_override.strategy.value}"
            )
            return self.generate_delete(row, client)
        return self.generate_update(row, policy, request, client)

    def generate_update(
        self, row: Row, policy: Policy, request: PrivacyRequest, client: Engine
    ) -> List[Update]:
        """
        Using TextClause to insert 'None' values into BigQuery throws an exception, so we use update clause instead.
        Returns a List of SQLAlchemy Update object. Does not actually execute the update object.

        A List of multiple Update objects are returned for partitioned tables; for a non-partitioned table,
        a single Update object is returned in a List for consistent typing.

        TODO: DRY up this method and `generate_delete` a bit
        """
        update_value_map: Dict[str, Any] = self.update_value_map(row, policy, request)
        non_empty_reference_field_keys: Dict[str, Field] = filter_nonempty_values(
            {
                fpath.string_path: fld.cast(row[fpath.string_path])
                for fpath, fld in self.reference_field_paths.items()
                if fpath.string_path in row
            }
        )

        valid = len(non_empty_reference_field_keys) > 0 and update_value_map
        if not valid:
            logger.warning(
                "There is not enough data to generate a valid update statement for {}",
                self.node.address,
            )
            return []

        table = Table(self._generate_table_name(), MetaData(bind=client), autoload=True)
        where_clauses: List[ColumnElement] = [
            getattr(table.c, k) == v for k, v in non_empty_reference_field_keys.items()
        ]

        if self.partitioning:
            partition_clauses = self.get_partition_clauses()
            partitioned_queries = []
            logger.info(
                f"Generating {len(partition_clauses)} partition queries for node '{self.node.address}' in DSR execution"
            )
            for partition_clause in partition_clauses:
                partitioned_queries.append(
                    table.update()
                    .where(*(where_clauses + [text(partition_clause)]))
                    .values(**update_value_map)
                )

            return partitioned_queries

        return [table.update().where(*where_clauses).values(**update_value_map)]

    def generate_delete(self, row: Row, client: Engine) -> List[Delete]:
        """Returns a List of SQLAlchemy DELETE statements for BigQuery. Does not actually execute the delete statement.

        Used when a collection-level masking override is present and the masking strategy is DELETE.

        A List of multiple DELETE statements are returned for partitioned tables; for a non-partitioned table,
        a single DELETE statement is returned in a List for consistent typing.

        TODO: DRY up this method and `generate_update` a bit
        """

        non_empty_reference_field_keys: Dict[str, Field] = filter_nonempty_values(
            {
                fpath.string_path: fld.cast(row[fpath.string_path])
                for fpath, fld in self.reference_field_paths.items()
                if fpath.string_path in row
            }
        )

        valid = len(non_empty_reference_field_keys) > 0
        if not valid:
            logger.warning(
                "There is not enough data to generate a valid DELETE statement for {}",
                self.node.address,
            )
            return []

        table = Table(self._generate_table_name(), MetaData(bind=client), autoload=True)
        where_clauses: List[ColumnElement] = [
            getattr(table.c, k) == v for k, v in non_empty_reference_field_keys.items()
        ]

        if self.partitioning:
            partition_clauses = self.get_partition_clauses()
            partitioned_queries = []
            logger.info(
                f"Generating {len(partition_clauses)} partition queries for node '{self.node.address}' in DSR execution"
            )

            for partition_clause in partition_clauses:
                partitioned_queries.append(
                    table.delete().where(*(where_clauses + [text(partition_clause)]))
                )

            return partitioned_queries

        return [table.delete().where(*where_clauses)]

    def format_fields_for_query(
        self,
        field_paths: List[FieldPath],
    ) -> List[str]:
        """Returns field paths in a format they can be added into SQL queries.

        Only returns non-nested fields (fields with exactly one level).
        Nested fields are skipped with a warning log.
        """
        formatted_fields = []
        for field_path in field_paths:
            if len(field_path.levels) > 1:
                logger.warning(
                    f"Skipping nested field '{'.'.join(field_path.levels)}' as nested fields are not supported"
                )
            else:
                formatted_fields.append(field_path.levels[0])
        return formatted_fields

    def generate_raw_query_without_tuples(
        self, field_list: List[str], filters: Dict[str, List[Any]]
    ) -> Optional[TextClause]:
        """
        Allows executing a somewhat raw query where the field_list and filters do not depend
        on the Node or Graph structure.

        This is an override of the base class method that supports nested fields for BigQuery.

        Examples with dot-delimited field names, notice the periods are replaced with underscores in the parameter bindings:

        1. Single value filter:
           field_list = ["id", "name", "email"]
           filters = {"user.id": [123]}

           Generates: SELECT id, name, email FROM `project_id.dataset_id.table_name` WHERE (user.id = :user_id)
           With parameter binding: user_id = 123

        2. Multiple value filter:
           field_list = ["id", "name", "email"]
           filters = {"user.status": ["active", "pending"]}

           Generates: SELECT id, name, email FROM `project_id.dataset_id.table_name` WHERE (user.status IN (:user_status_in_stmt_generated_0, :user_status_in_stmt_generated_1))
           With parameter bindings: user_status_in_stmt_generated_0 = "active", user_status_in_stmt_generated_1 = "pending"
        """
        clauses = []
        query_data = {}
        for field_name, field_value in filters.items():
            # Replace dots with underscores in field names for parameter binding
            field_binding_name = field_name.replace(".", "_")
            data = set(field_value)
            if len(data) == 1:
                clauses.append(
                    self.format_clause_for_query(field_name, "=", field_binding_name)
                )
                query_data[field_binding_name] = data.pop()
            elif len(data) > 1:
                data_vals = list(data)
                query_data_keys: List[str] = []
                for val in data_vals:
                    # appending "_in_stmt_generated_" (can be any arbitrary str) so that this name has lower chance of conflicting with pre-existing column in table
                    query_data_name = (
                        field_binding_name
                        + "_in_stmt_generated_"
                        + str(data_vals.index(val))
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

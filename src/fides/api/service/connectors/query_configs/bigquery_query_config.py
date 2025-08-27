from typing import Any, Dict, List, Optional, Union, cast

import pydash
from fideslang.models import MaskingStrategies
from loguru import logger
from sqlalchemy import MetaData, Table, or_, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Delete, Update
from sqlalchemy.sql.elements import ColumnElement, TextClause
from sqlalchemy_bigquery import BigQueryDialect

from fides.api.graph.config import Field, FieldPath
from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.namespace_meta.bigquery_namespace_meta import (
    BigQueryNamespaceMeta,
)
from fides.api.schemas.partitioning import TIME_BASED_REQUIRED_KEYS, combine_partitions
from fides.api.schemas.partitioning.time_based_partitioning import TimeBasedPartitioning
from fides.api.service.connectors.query_configs.query_config import (
    QueryStringWithoutTuplesOverrideQueryConfig,
)
from fides.api.util.collection_util import (
    Row,
    filter_nonempty_values,
    flatten_dict,
    merge_dicts,
    replace_none_arrays,
    unflatten_dict,
)


class BigQueryQueryConfig(QueryStringWithoutTuplesOverrideQueryConfig):
    """
    Generates SQL valid for BigQuery
    """

    namespace_meta_schema = BigQueryNamespaceMeta

    @property
    def partitioning(
        self,
    ) -> Optional[Union[List[TimeBasedPartitioning], Dict[str, Any]]]:
        # Overridden from base implementation to allow for _only_ BQ partitioning, for now
        return self.node.collection.partitioning

    def get_partition_clauses(
        self,
    ) -> List[str]:
        """
        Build a list of SQL `WHERE` clause strings for the collection's partitioning
        configuration.

        Supported modes:
        1. `Legacy static` - A list of `where_clauses`.
        2. `Single time-based` - A single time-based partitioning spec
        3. `Multiple time-based` - A list of time-based partitioning specs, with different intervals

        Any other combination (e.g. mixing modes or missing keys) raises a
        `ValueError` so that mis-configurations surface early.
        """

        partition_spec: Optional[Union[List[TimeBasedPartitioning], Dict[str, Any]]] = (
            self.partitioning
        )
        if not partition_spec:
            logger.warning(
                f"No partitioning specification found for node '{self.node.address}', skipping partition clauses"
            )
            return []

        # Legacy mode using `where_clauses`
        if isinstance(partition_spec, dict) and "where_clauses" in partition_spec:
            if any(k in partition_spec for k in TIME_BASED_REQUIRED_KEYS):
                # Mixed mode not allowed
                raise ValueError(
                    "Partitioning spec cannot define both `where_clauses` and time-based partitioning."
                )
            where = partition_spec.get("where_clauses") or []
            if not where:
                raise ValueError("`where_clauses` must be a non-empty list.")
            return where

        # Combine and de-duplicate boundary rows
        combined_expressions = combine_partitions(partition_spec)  # type: ignore

        dialect = BigQueryDialect()
        where_clauses = [
            str(expr.compile(dialect=dialect, compile_kwargs={"literal_binds": True}))
            for expr in combined_expressions
        ]

        return where_clauses

    def generate_table_name(self) -> str:
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
        return f'SELECT {field_list} FROM `{self.generate_table_name()}` WHERE ({" OR ".join(clauses)})'

    def generate_masking_stmt(
        self,
        node: ExecutionNode,
        row: Row,
        policy: Policy,
        request: PrivacyRequest,
        client: Engine,
        input_data: Optional[Dict[str, List[Any]]] = None,
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
            return self.generate_delete(client, input_data or {})
        return self.generate_update(row, policy, request, client)

    def generate_update(
        self, row: Row, policy: Policy, request: PrivacyRequest, client: Engine
    ) -> List[Update]:
        """
        Using TextClause to insert 'None' values into BigQuery throws an exception, so we use update clause instead.
        Returns a List of SQLAlchemy Update object. Does not actually execute the update object.

        A List of multiple Update objects are returned for partitioned tables; for a non-partitioned table,
        a single Update object is returned in a List for consistent typing.

        This implementation handles nested fields by grouping them as JSON objects rather than
        individual field updates.

        See the README.md in this directory for a detailed example of how nested data is handled.
        """

        # 1. Take update_value_map as-is (already flattened)
        update_value_map: Dict[str, Any] = self.update_value_map(row, policy, request)

        # 2. Flatten the row
        flattened_row = flatten_dict(row)

        # 3. Merge flattened_row with update_value_map (update_value_map takes precedence)
        merged_dict = merge_dicts(flattened_row, update_value_map)

        # 4. Unflatten the merged dictionary
        nested_result = unflatten_dict(merged_dict)

        # 5. Replace any arrays containing only None values with empty arrays
        nested_result = replace_none_arrays(nested_result)

        # 6. Only keep top-level keys that are in the update_value_map
        top_level_keys = {key.split(".")[0] for key in update_value_map}

        # Filter the nested result to only include those top-level keys
        final_update_map = {
            k: v for k, v in nested_result.items() if k in top_level_keys
        }

        # Use existing non-empty reference fields mechanism for WHERE clause
        non_empty_reference_field_keys: Dict[str, Field] = filter_nonempty_values(
            {
                fpath.string_path: fld.cast(pydash.get(row, fpath.string_path))
                for fpath, fld in self.reference_field_paths.items()
                if pydash.get(row, fpath.string_path) is not None
            }
        )

        valid = len(non_empty_reference_field_keys) > 0 and final_update_map
        if not valid:
            logger.warning(
                "There is not enough data to generate a valid update statement for {}",
                self.node.address,
            )
            return []

        table = Table(self.generate_table_name(), MetaData(bind=client), autoload=True)
        where_clauses: List[ColumnElement] = [
            table.c[k] == v for k, v in non_empty_reference_field_keys.items()
        ]

        # Create update values using Column objects as keys to handle column names with spaces
        update_values = {}
        for column_name, value in final_update_map.items():
            # Use bracket notation to access columns with spaces in their names
            column = table.c[column_name]
            update_values[column] = value

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
                    .values(update_values)
                )

            return partitioned_queries

        return [table.update().where(*where_clauses).values(update_values)]

    def generate_delete(
        self,
        client: Engine,
        input_data: Optional[Dict[str, List[Any]]] = None,
    ) -> List[Delete]:
        """
        Returns a List of SQLAlchemy DELETE statements for BigQuery. Does not actually execute the delete statement.

        Used when a collection-level masking override is present and the masking strategy is DELETE.

        A List of multiple DELETE statements are returned for partitioned tables; for a non-partitioned table,
        a single DELETE statement is returned in a List for consistent typing.
        """

        if not input_data:
            logger.warning(
                "No input data provided for node '{}', skipping DELETE statement generation",
                self.node.address,
            )
            return []

        filtered_data = self.node.typed_filtered_values(input_data)

        if not filtered_data:
            logger.warning(
                "There is not enough data to generate a valid DELETE statement for {}",
                self.node.address,
            )
            return []

        table = Table(self.generate_table_name(), MetaData(bind=client), autoload=True)

        # Build individual reference clauses
        where_clauses: List[ColumnElement] = []
        for column_name, values in filtered_data.items():
            if len(values) == 1:
                where_clauses.append(table.c[column_name] == values[0])
            else:
                where_clauses.append(table.c[column_name].in_(values))

        # Combine reference clauses with OR instead of AND
        combined_reference_clause = or_(*where_clauses)

        if self.partitioning:
            partition_clauses = self.get_partition_clauses()
            partitioned_queries = []
            logger.info(
                f"Generating {len(partition_clauses)} partition queries for node '{self.node.address}' in DSR execution"
            )

            for partition_clause in partition_clauses:
                partitioned_queries.append(
                    table.delete()
                    .where(combined_reference_clause)
                    .where(text(partition_clause))
                )

            return partitioned_queries

        return [table.delete().where(combined_reference_clause)]

    def uses_delete_masking_strategy(self) -> bool:
        """Check if this collection uses DELETE masking strategy.

        Returns True if masking override is present and strategy is DELETE.
        """
        masking_override = self.node.collection.masking_strategy_override
        return (
            masking_override is not None
            and masking_override.strategy == MaskingStrategies.DELETE
        )

    def format_fields_for_query(
        self,
        field_paths: List[FieldPath],
    ) -> List[str]:
        """
        Returns field paths in a format they can be added into SQL queries.
        Only returns non-nested fields (fields with exactly one level).
        """

        formatted_fields = []
        for field_path in field_paths:
            if len(field_path.levels) == 1:
                formatted_fields.append(field_path.levels[0])
        return formatted_fields

    def format_clause_for_query(
        self, string_path: str, operator: str, operand: str
    ) -> str:
        """
        Returns clauses with proper BigQuery backtick escaping for column names.
        Handles column names with spaces and nested fields (dot-separated) by escaping each part individually.
        """
        # For nested fields (containing dots), escape each part individually
        if "." in string_path:
            parts = string_path.split(".")
            escaped_field = ".".join(f"`{part}`" for part in parts)
        else:
            # For simple fields, wrap the entire name in backticks
            escaped_field = f"`{string_path}`"

        if operator == "IN":
            return f"{escaped_field} IN ({operand})"
        return f"{escaped_field} {operator} :{operand}"

    def generate_raw_query_without_tuples(
        self, field_list: List[str], filters: Dict[str, List[Any]]
    ) -> Optional[TextClause]:
        """
        Allows executing a somewhat raw query where the field_list and filters do not depend
        on the Node or Graph structure.

        This is an override of the base class method that supports nested fields for BigQuery.

        Examples with field names containing dots and spaces, notice these are replaced with underscores in the parameter bindings:

        1. Single value filter:
           field_list = ["id", "name", "email"]
           filters = {"user.id": [123]}

           Generates: SELECT id, name, email FROM `project_id.dataset_id.table_name` WHERE (`user`.`id` = :user_id)
           With parameter binding: user_id = 123

        2. Field with spaces:
           field_list = ["id", "custom id", "email"]
           filters = {"custom id": ["abc123"]}

           Generates: SELECT id, `custom id`, email FROM `project_id.dataset_id.table_name` WHERE (`custom id` = :custom_id)
           With parameter binding: custom_id = "abc123"

        3. Multiple value filter with nested field:
           field_list = ["id", "name", "email"]
           filters = {"contact_info.primary_email": ["active", "pending"]}

           Generates: SELECT id, name, email FROM `project_id.dataset_id.table_name` WHERE (`contact_info`.`primary_email` IN (:contact_info_primary_email_in_stmt_generated_0, :contact_info_primary_email_in_stmt_generated_1))
           With parameter bindings: contact_info_primary_email_in_stmt_generated_0 = "active", contact_info_primary_email_in_stmt_generated_1 = "pending"
        """
        clauses = []
        query_data = {}
        for field_name, field_value in filters.items():
            # Replace dots and spaces with underscores in field names for parameter binding
            # SQLAlchemy parameter names cannot contain spaces or special characters
            field_binding_name = field_name.replace(".", "_").replace(" ", "_")
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
            formatted_fields = ", ".join([f"`{field}`" for field in field_list])
            query_str = self.get_formatted_query_string(formatted_fields, clauses)
            return text(query_str).params(query_data)

        return None

from typing import Any, Dict, List, Optional, Union, cast

from fideslang.models import MaskingStrategies
from loguru import logger
from sqlalchemy import MetaData, Table, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Delete, Update  # type: ignore
from sqlalchemy.sql.elements import ColumnElement

from fides.api.graph.config import Field
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
        non_empty_primary_keys: Dict[str, Field] = filter_nonempty_values(
            {
                fpath.string_path: fld.cast(row[fpath.string_path])
                for fpath, fld in self.primary_key_field_paths.items()
                if fpath.string_path in row
            }
        )

        valid = len(non_empty_primary_keys) > 0 and update_value_map
        if not valid:
            logger.warning(
                "There is not enough data to generate a valid update statement for {}",
                self.node.address,
            )
            return []

        table = Table(self._generate_table_name(), MetaData(bind=client), autoload=True)
        where_clauses: List[ColumnElement] = [
            getattr(table.c, k) == v for k, v in non_empty_primary_keys.items()
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

        non_empty_primary_keys: Dict[str, Field] = filter_nonempty_values(
            {
                fpath.string_path: fld.cast(row[fpath.string_path])
                for fpath, fld in self.primary_key_field_paths.items()
                if fpath.string_path in row
            }
        )

        valid = len(non_empty_primary_keys) > 0
        if not valid:
            logger.warning(
                "There is not enough data to generate a valid DELETE statement for {}",
                self.node.address,
            )
            return []

        table = Table(self._generate_table_name(), MetaData(bind=client), autoload=True)
        where_clauses: List[ColumnElement] = [
            getattr(table.c, k) == v for k, v in non_empty_primary_keys.items()
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

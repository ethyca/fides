from typing import List, Optional

from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import (  # type: ignore
    Connection,
    Engine,
    LegacyCursorResult,
    create_engine,
)
from sqlalchemy.orm import Session
from sqlalchemy.sql import Executable  # type: ignore
from sqlalchemy.sql.elements import TextClause

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_bigquery import (
    BigQuerySchema,
)
from fides.api.service.connectors.query_configs.bigquery_query_config import (
    BigQueryQueryConfig,
)
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.util.collection_util import Row


class BigQueryConnector(SQLConnector):
    """Connector specific to Google BigQuery"""

    secrets_schema = BigQuerySchema

    @property
    def requires_primary_keys(self) -> bool:
        return False

    # Overrides BaseConnector.build_uri
    def build_uri(self) -> str:
        """Build URI of format"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        dataset = f"/{config.dataset}" if config.dataset else ""
        return f"bigquery://{config.keyfile_creds.project_id}{dataset}"  # pylint: disable=no-member

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """
        Returns a SQLAlchemy Engine that can be used to interact with Google BigQuery.

        Overrides to pass in credentials_info
        """
        secrets = self.configuration.secrets or {}
        uri = secrets.get("url") or self.build_uri()

        keyfile_creds = secrets.get("keyfile_creds", {})
        credentials_info = dict(keyfile_creds) if keyfile_creds else {}

        return create_engine(
            uri,
            credentials_info=credentials_info,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
        )

    # Overrides SQLConnector.query_config
    def query_config(self, node: ExecutionNode) -> BigQueryQueryConfig:
        """Query wrapper corresponding to the input execution_node."""

        db: Session = Session.object_session(self.configuration)
        return BigQueryQueryConfig(
            node, SQLConnector.get_namespace_meta(db, node.address.dataset)
        )

    def partitioned_retrieval(
        self,
        query_config: SQLQueryConfig,
        connection: Connection,
        stmt: TextClause,
    ) -> List[Row]:
        """
        Retrieve data against a partitioned table using the partitioning spec configured for this node to execute
        multiple queries against the partitioned table.

        This is only supported by the BigQueryConnector currently.

        NOTE: when we deprecate `where_clause` partitioning in favor of a more proper partitioning DSL,
        we should be sure to still support the existing `where_clause` partition definition on
        any in-progress DSRs so that they can run through to completion.
        """
        if not isinstance(query_config, BigQueryQueryConfig):
            raise TypeError(
                f"Unexpected query config of type '{type(query_config)}' passed to BigQueryConnector's `partitioned_retrieval`"
            )

        partition_clauses = query_config.get_partition_clauses()
        logger.info(
            f"Executing {len(partition_clauses)} partition queries for node '{query_config.node.address}' in DSR execution"
        )
        rows = []
        for partition_clause in partition_clauses:
            logger.debug(
                f"Executing partition query with partition clause '{partition_clause}'"
            )
            existing_bind_params = stmt.compile().params
            partitioned_stmt = text(f"{stmt} AND ({text(partition_clause)})").params(
                existing_bind_params
            )
            results = connection.execute(partitioned_stmt)
            rows.extend(self.cursor_result_to_rows(results))
        return rows

    # Overrides SQLConnector.test_connection
    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Overrides SQLConnector.test_connection with a BigQuery-specific connection test.

        The connection is tested using the native python client for BigQuery, since that is what's used
        by the detection and discovery workflows/codepaths.
        TODO: migrate the rest of this class, used for DSR execution, to also make use of the native bigquery client.
        """
        try:
            bq_schema = BigQuerySchema(**self.configuration.secrets or {})
            client = bq_schema.get_client()
            all_projects = [project for project in client.list_projects()]
            if all_projects:
                return ConnectionTestStatus.succeeded
            logger.error("No Bigquery Projects found with the provided credentials.")
            raise ConnectionException(
                "No Bigquery Projects found with the provided credentials."
            )
        except Exception as e:
            logger.exception(f"Error testing connection to remote BigQuery {str(e)}")
            raise ConnectionException(f"Connection error: {e}")

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """Execute a masking request. Returns the number of records updated or deleted"""
        query_config = self.query_config(node)
        update_or_delete_ct = 0
        client = self.client()
        for row in rows:
            update_or_delete_stmts: List[Executable] = (
                query_config.generate_masking_stmt(
                    node, row, policy, privacy_request, client
                )
            )
            if update_or_delete_stmts:
                with client.connect() as connection:
                    for update_or_delete_stmt in update_or_delete_stmts:
                        results: LegacyCursorResult = connection.execute(
                            update_or_delete_stmt
                        )
                        update_or_delete_ct = update_or_delete_ct + results.rowcount
        return update_or_delete_ct

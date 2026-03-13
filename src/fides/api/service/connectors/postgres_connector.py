from typing import Dict

from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine, create_engine  # type: ignore
from sqlalchemy.orm import Session

from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.connection_configuration import PostgreSQLSchema
from fides.api.service.connectors.query_configs.postgres_query_config import (
    PostgresQueryConfig,
)
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.config import get_config

CONFIG = get_config()


class PostgreSQLConnector(SQLConnector):
    """Connector specific to postgresql"""

    secrets_schema = PostgreSQLSchema

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self._database_engines: Dict[str, Engine] = {}

    @property
    def requires_primary_keys(self) -> bool:
        """Postgres allows arbitrary columns in the WHERE clause for updates so primary keys are not required."""
        return False

    def _build_uri_for_database(self, dbname: str | None = None) -> str:
        """Build a postgresql:// URI, optionally overriding the database name."""
        config = self.secrets_schema(**self.configuration.secrets or {})

        user_password = ""
        if config.username:
            user = config.username
            password = f":{config.password}" if config.password else ""
            user_password = f"{user}{password}@"

        netloc = config.host
        port = f":{config.port}" if config.port else ""
        effective_dbname = dbname or config.dbname
        db_part = f"/{effective_dbname}" if effective_dbname else ""
        query = f"?sslmode={config.ssl_mode}" if config.ssl_mode else ""
        return f"postgresql://{user_password}{netloc}{port}{db_part}{query}"

    def build_uri(self) -> str:
        """Build URI of format postgresql://[user[:password]@][netloc][:port][/dbname]"""
        return self._build_uri_for_database()

    def _build_ssh_uri_for_database(
        self, local_address: tuple, dbname: str | None = None
    ) -> str:
        """Build a postgresql:// URI via SSH tunnel, optionally overriding the database name."""
        config = self.secrets_schema(**self.configuration.secrets or {})

        user_password = ""
        if config.username:
            user = config.username
            password = f":{config.password}" if config.password else ""
            user_password = f"{user}{password}@"

        local_host, local_port = local_address
        netloc = local_host
        port = f":{local_port}" if local_port else ""
        effective_dbname = dbname or config.dbname
        db_part = f"/{effective_dbname}" if effective_dbname else ""
        query = f"?sslmode={config.ssl_mode}" if config.ssl_mode else ""
        return f"postgresql://{user_password}{netloc}{port}{db_part}{query}"

    def build_ssh_uri(self, local_address: tuple) -> str:
        """Build URI of format postgresql://[user[:password]@][ssh_host][:ssh_port][/dbname]"""
        return self._build_ssh_uri_for_database(local_address)

    def _create_engine_for_database(self, dbname: str | None = None) -> Engine:
        """Create a SQLAlchemy Engine, optionally targeting a specific database.

        When dbname is explicitly provided (from namespace_meta), we always
        build the URI ourselves so the database override takes effect. The
        ``url`` secret is only used for the default engine (no override).
        """
        if (
            self.configuration.secrets
            and self.configuration.secrets.get("ssh_required", False)
            and CONFIG.security.bastion_server_ssh_private_key
        ):
            config = self.secrets_schema(**self.configuration.secrets or {})
            self.create_ssh_tunnel(host=config.host, port=config.port)
            self.ssh_server.start()
            uri = self._build_ssh_uri_for_database(
                local_address=self.ssh_server.local_bind_address, dbname=dbname
            )
        elif dbname:
            # Explicit database override — build URI directly so the
            # override isn't silently ignored by a url secret.
            uri = self._build_uri_for_database(dbname)
        else:
            uri = (self.configuration.secrets or {}).get(
                "url"
            ) or self._build_uri_for_database()

        return create_engine(
            uri,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
        )

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a database"""
        return self._create_engine_for_database()

    def client_for_node(self, node: ExecutionNode) -> Engine:
        """Return an engine targeting the database from the dataset's namespace_meta.

        If the dataset has namespace_meta with a database_name, returns (or
        creates and caches) an engine connected to that specific database.
        Otherwise falls back to the default engine from connection secrets.
        """
        db: Session = Session.object_session(self.configuration)
        namespace_meta = SQLConnector.get_namespace_meta(db, node.address.dataset)

        if namespace_meta and namespace_meta.get("database_name"):
            target_db = namespace_meta["database_name"]
            if target_db not in self._database_engines:
                logger.info(
                    "Creating Postgres engine for database '{}' (from namespace_meta)",
                    target_db,
                )
                self._database_engines[target_db] = self._create_engine_for_database(
                    dbname=target_db
                )
            return self._database_engines[target_db]

        return self.client()

    def set_schema(self, connection: Connection) -> None:
        """Sets the search_path for a Postgres database if applicable.

        Skipped when namespace_meta is present because table names are already
        schema-qualified in the generated SQL. Only runs for the legacy
        db_schema connection secret path.
        """
        if self._current_namespace_meta:
            return

        config = self.secrets_schema(**self.configuration.secrets or {})
        if config.db_schema:
            logger.info("Setting PostgreSQL search_path before retrieving data")
            stmt = text("SET search_path to :search_path")
            stmt = stmt.bindparams(search_path=config.db_schema)
            connection.execute(stmt)

    def close(self) -> None:
        """Close held resources including per-database engines."""
        for engine in self._database_engines.values():
            engine.dispose()
        self._database_engines.clear()
        super().close()

    def query_config(self, node: ExecutionNode) -> PostgresQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        db: Session = Session.object_session(self.configuration)
        namespace_meta = SQLConnector.get_namespace_meta(db, node.address.dataset)
        self._current_namespace_meta = namespace_meta
        return PostgresQueryConfig(node, namespace_meta)

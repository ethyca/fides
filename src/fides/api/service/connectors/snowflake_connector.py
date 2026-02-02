import base64
from typing import Any, Dict, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from snowflake.sqlalchemy import URL as Snowflake_URL
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.graph.execution import ExecutionNode
from fides.api.schemas.connection_configuration import SnowflakeSchema
from fides.api.service.connectors.query_configs.snowflake_query_config import (
    SnowflakeQueryConfig,
)
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.config import get_config

CONFIG = get_config()


class SnowflakeConnector(SQLConnector):
    """Connector specific to Snowflake"""

    secrets_schema = SnowflakeSchema

    def build_uri(self) -> str:
        """Build URI of format 'snowflake://<user_login_name>:<password>@<account_identifier>/<database_name>/
        <schema_name>?warehouse=<warehouse_name>&role=<role_name>'
        """
        config = self.secrets_schema(**self.configuration.secrets or {})

        kwargs = {}

        if config.account_identifier:
            kwargs["account"] = config.account_identifier
        if config.user_login_name:
            kwargs["user"] = config.user_login_name
        if config.password:
            kwargs["password"] = config.password
        if config.database_name:
            kwargs["database"] = config.database_name
        if config.schema_name:
            kwargs["schema"] = config.schema_name
        if config.warehouse_name:
            kwargs["warehouse"] = config.warehouse_name
        if config.role_name:
            kwargs["role"] = config.role_name

        url: str = Snowflake_URL(**kwargs)
        return url

    def get_connect_args(self) -> Dict[str, Any]:
        """Get connection arguments for the engine"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        connect_args: Dict[str, Union[str, bytes]] = {}
        if config.private_key:
            raw_key = config.private_key.replace("\\n", "\n")
            # Snowflake connector expects: str = base64-encoded DER, or bytes = raw DER
            if "-----BEGIN" in raw_key:
                # PEM: decode to key, then pass as base64 DER string or raw DER bytes
                password = None
                if config.private_key_passphrase:
                    password = (
                        config.private_key_passphrase.encode()
                    )  # pylint: disable=no-member
                private_key_obj = serialization.load_pem_private_key(
                    raw_key.encode(),
                    password=password,
                    backend=default_backend(),
                )
                der_bytes = private_key_obj.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
                # Pass as base64 string so Snowflake's b64decode path is used
                connect_args["private_key"] = base64.b64encode(der_bytes).decode(
                    "ascii"
                )
            else:
                # Already base64-encoded DER: strip whitespace and pass as-is
                connect_args["private_key"] = "".join(raw_key.split())
                if config.private_key_passphrase:
                    connect_args["private_key_passphrase"] = (
                        config.private_key_passphrase.encode()  # pylint: disable=no-member
                    )
        return connect_args

    def query_config(self, node: ExecutionNode) -> SnowflakeQueryConfig:
        """Query wrapper corresponding to the input execution_node."""

        db: Session = Session.object_session(self.configuration)
        return SnowflakeQueryConfig(
            node, SQLConnector.get_namespace_meta(db, node.address.dataset)
        )

    def get_qualified_table_name(self, node: ExecutionNode) -> str:
        """Get fully qualified Snowflake table name using existing query config logic"""
        query_config = self.query_config(node)
        return query_config.generate_table_name()

    def table_exists(self, qualified_table_name: str) -> bool:
        """
        Check if table exists in Snowflake using the proper three-part naming convention.

        Snowflake supports database.schema.table naming, and the generic SQLConnector
        table_exists method doesn't handle quoted identifiers properly.
        """
        try:
            client = self.create_client()
            with client.connect() as connection:
                # Remove quotes and split the parts
                clean_name = qualified_table_name.replace('"', "")
                parts = clean_name.split(".")

                if len(parts) == 1:
                    # Simple table name - use current schema
                    table_name = parts[0]
                    result = connection.execute(text(f'DESC TABLE "{table_name}"'))
                elif len(parts) == 2:
                    # schema.table format
                    schema_name, table_name = parts
                    result = connection.execute(
                        text(f'DESC TABLE "{schema_name}"."{table_name}"')
                    )
                elif len(parts) >= 3:
                    # database.schema.table format
                    database_name, schema_name, table_name = (
                        parts[-3],
                        parts[-2],
                        parts[-1],
                    )
                    # Use the database.schema.table format
                    result = connection.execute(
                        text(
                            f'DESC TABLE "{database_name}"."{schema_name}"."{table_name}"'
                        )
                    )
                else:
                    return False

                # If we get here without an exception, the table exists
                result.close()
                return True

        except Exception:
            # Table doesn't exist or other error
            return False

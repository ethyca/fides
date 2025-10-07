"""QA scenario to create an external reference mapping table in postgres_example and generate corresponding dataset.

Usage example:
    python qa create_external_reference setup \
        --input email --input_value adrian@ethyca.com \
        --output user_id --output_value 123

After running, the scenario prints the dataset.collection.field string that can be used as an external reference in connector forms.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

import psycopg2
from psycopg2.extensions import connection as _PGConnection
from psycopg2.extras import RealDictCursor

sys.path.append(str(Path(__file__).parent.parent))

from utils import Argument, QATestScenario  # noqa: E402
from utils.fides_api import FidesAPI  # noqa: E402

TABLE_PREFIX = "ref_"
SYSTEM_NAME = "ref_system"
CONNECTION_KEY = "ref_postgres_connection"


class CreateExternalReference(QATestScenario):
    """Create a mapping table in Postgres for external references and register dataset/system/connection in Fides."""

    arguments = {
        "input": Argument(
            type=str,
            default="email",
            description="Input identity column name (e.g. email)",
        ),
        "input_value": Argument(
            type=str, default="", description="Value to insert in the input column"
        ),
        "output": Argument(
            type=str,
            default="user_id",
            description="Mapped output column name (e.g. user_id)",
        ),
        "output_value": Argument(
            type=str, default="", description="Mapped output value to insert"
        ),
    }

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.input: str = kwargs.get("input", "email")
        self.input_value: str = kwargs.get("input_value", "")
        self.output: str = kwargs.get("output", "user_id")
        self.output_value: str = kwargs.get("output_value", "")

        self.table_name = f"{TABLE_PREFIX}{self.input}_to_{self.output}"
        self.dataset_key = f"{self.table_name}"
        self.collection_name = self.table_name

        # Use FidesAPI helper
        self.api = FidesAPI(base_url)

    @property
    def description(self) -> str:
        return "Creates a postgres mapping table for external references and registers it in Fides."

    # ---------- Helper methods ----------

    def _pg_connect(self) -> _PGConnection:
        return psycopg2.connect(
            host="localhost",
            port=6432,
            dbname="postgres_example",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor,
        )

    def _create_table_and_row(self) -> None:
        with self._pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        {self.input} TEXT PRIMARY KEY,
                        {self.output} TEXT
                    );
                    """
                )
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} ({self.input}, {self.output})
                    VALUES (%s, %s)
                    ON CONFLICT ({self.input}) DO UPDATE SET {self.output} = EXCLUDED.{self.output};
                    """,
                    (self.input_value, self.output_value),
                )
            conn.commit()

    def _drop_prefixed_tables(self) -> None:
        with self._pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE %s;
                    """,
                    (f"{TABLE_PREFIX}%",),
                )
                tables = [row["tablename"] for row in cur.fetchall()]
                for table in tables:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            conn.commit()

    def _generate_dataset(self) -> Dict[str, Any]:
        return {
            "fides_key": self.dataset_key,
            "organization_fides_key": "default_organization",
            "name": f"External reference dataset for {self.table_name}",
            "description": "Mapping table used for external references",
            "collections": [
                {
                    "name": self.collection_name,
                    "fields": [
                        {
                            "name": self.input,
                            "data_categories": ["user.contact"],
                            "fides_meta": {
                                "identity": self.input,
                                "data_type": "string",
                                "primary_key": True,
                            },
                        },
                        {
                            "name": self.output,
                            "data_categories": ["user.unique_id"],
                            "fides_meta": {
                                "data_type": "string",
                            },
                        },
                    ],
                }
            ],
        }

    # ---------- QATestScenario required methods ----------

    def setup(self) -> bool:
        self.setup_phase()
        try:
            # Step 1 – create table and insert mapping
            self.step(1, "Create table and insert mapping row")
            self._create_table_and_row()
            self.success(f"Created table {self.table_name} and inserted mapping")

            # Step 2 – create dataset
            self.step(2, "Create dataset")
            dataset_data = self._generate_dataset()
            self.api.create_dataset(dataset_data)
            self.success(f"Dataset {self.dataset_key} created")

            # Step 3 – ensure system exists
            self.step(3, "Create system if missing")
            try:
                self.api.get_system_by_key(SYSTEM_NAME)
                self.info("System already exists")
            except Exception:
                self.api.create_system(
                    {
                        "fides_key": SYSTEM_NAME,
                        "organization_fides_key": "default_organization",
                        "name": "Dataset reference system",
                        "description": "System to map well-known identities to system-specific identifiers",
                        "system_type": "Service",
                        "privacy_declarations": [],
                    }
                )
                self.success("System created")

            # Step 4 – ensure connection exists & linked
            self.step(4, "Create / update Postgres connection and link dataset")
            connection_data = {
                "name": "External Reference Postgres Connection",
                "key": CONNECTION_KEY,
                "connection_type": "postgres",
                "access": "write",
                "description": "Connection to postgres_example for external ref QA.",
                "secrets": {
                    "host": "host.docker.internal",
                    "port": 6432,
                    "dbname": "postgres_example",
                    "username": "postgres",
                    "password": "postgres",
                },
            }
            # Create or update connection
            try:
                self.api.update_connection(CONNECTION_KEY, connection_data)
                self.info("Connection updated")
            except Exception:
                # create new connection linked to system
                self.api.create_system_connection(SYSTEM_NAME, connection_data)
                self.success("Connection created and linked to system")

            # Link dataset to connection
            self.api.link_datasets_to_connection(CONNECTION_KEY, [self.dataset_key])
            self.success("Dataset linked to connection")
            ref_string = f"{self.dataset_key}.{self.collection_name}.{self.output}"
            self.success(f"External reference: {ref_string}")

            self.final_success("Setup complete!")
            return True
        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        self.cleanup_phase()
        try:
            # Step 1 – drop prefixed tables
            self.step(1, "Drop external_ref_* tables")
            self._drop_prefixed_tables()
            self.success("Dropped tables with prefix ref_")

            # Step 2 – delete connection (cascade deletes dataset configs)
            self.step(2, "Delete connection")
            self.api.delete_connection(CONNECTION_KEY)
            self.success("Connection deleted or already absent")

            # Step 3 – delete system
            self.step(3, "Delete system")
            self.api.delete_system(SYSTEM_NAME)
            self.success("System deleted or already absent")

            # Step 4 – delete dataset
            self.step(4, "Delete dataset")
            self.api.delete_dataset(self.dataset_key)
            self.success("Dataset deleted or already absent")

            self.final_success("Teardown complete!")
            return True
        except Exception as e:
            self.final_error(f"Teardown failed: {e}")
            return False

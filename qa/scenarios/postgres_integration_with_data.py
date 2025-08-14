#!/usr/bin/env python3
"""
QA scenario for testing PostgreSQL integration with the postgres_example_test_dataset.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from utils import QATestScenario, Argument


class PostgresIntegrationWithData(QATestScenario):
    """QA scenario for testing PostgreSQL integration with postgres_example_test_dataset."""

    arguments = {
        "host": Argument(
            type=str,
            default="host.docker.internal",
            description="PostgreSQL host (defaults to 'host.docker.internal')",
        ),
        "port": Argument(type=int, default=6432, description="PostgreSQL port "),
        "username": Argument(
            type=str,
            default="postgres",
            description="PostgreSQL username (defaults to 'postgres')",
        ),
        "password": Argument(
            type=str,
            default="postgres",
            description="PostgreSQL password (defaults to 'postgres')",
        ),
        "dbname": Argument(
            type=str,
            default="postgres_example",
            description="PostgreSQL database name (defaults to 'postgres_example')",
        ),
        "db_schema": Argument(
            type=str,
            default="public",
            description="PostgreSQL schema name (defaults to public)",
        ),
    }

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.system_name = "qa_postgres_integration_system"
        self.connection_key = "qa_postgres_connection"
        self.dataset_key = "postgres_example_test_dataset"

        # Store credential arguments
        self.pg_host = kwargs.get("host", "host.docker.internal")
        self.pg_port = kwargs.get("port", 6432)
        self.pg_username = kwargs.get("username", "postgres")
        self.pg_password = kwargs.get("password", "postgres")
        self.pg_dbname = kwargs.get("dbname", "postgres_example")
        self.pg_db_schema = kwargs.get("db_schema", "public")

    @property
    def description(self) -> str:
        return "Creates a PostgreSQL system with Postgres integration, postgres_example_test_dataset, and links them together. You can optionally provide credentials for the PostgreSQL database."

    def setup(self) -> bool:
        """Setup PostgreSQL integration with example test dataset."""
        self.setup_phase()

        try:
            # Step 1: Load and validate environment variables
            self.step(1, "Validating PostgreSQL credentials")
            postgres_config = self._load_postgres_credentials()

            # Step 2: Load the PostgreSQL example test dataset from YAML
            self.step(2, "Loading postgres_example_test_dataset.yml")
            dataset_data = self._load_dataset_yaml()

            # Step 3: Create the dataset in Fides
            self.step(3, "Creating dataset in Fides")
            self._create_dataset(dataset_data)

            # Step 4: Create the system
            self.step(4, "Creating PostgreSQL system")
            self._create_system()

            # Step 5: Create the PostgreSQL connection
            self.step(5, "Creating PostgreSQL connection")
            self._create_postgres_connection(postgres_config)

            # Step 6: Link the dataset to the connection
            self.step(6, "Linking dataset to connection")
            self._link_dataset_to_connection()

            self.final_success(
                "PostgreSQL integration setup complete! You can now run privacy requests against the configured database."
            )
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario."""
        self.cleanup_phase()

        success = True
        deleted_counts = {"connections": 0, "systems": 0, "datasets": 0}

        try:
            # Step 1: Delete connection FIRST (cascades delete DatasetConfigs)
            self.step(1, "Deleting PostgreSQL connection")
            if self.api.delete_connection(self.connection_key):
                deleted_counts["connections"] += 1
                self.success(f"Deleted connection: {self.connection_key}")
            else:
                self.already_cleaned("Connection", self.connection_key)

            # Step 2: Delete system
            self.step(2, "Deleting PostgreSQL system")
            if self.api.delete_system(self.system_name):
                deleted_counts["systems"] += 1
                self.success(f"Deleted system: {self.system_name}")
            else:
                self.already_cleaned("System", self.system_name)

            # Step 3: Delete dataset LAST
            self.step(3, "Deleting dataset")
            if self.api.delete_dataset(self.dataset_key):
                deleted_counts["datasets"] += 1
                self.success(f"Deleted dataset: {self.dataset_key}")
            else:
                self.already_cleaned("Dataset", self.dataset_key)

            # Note about database data
            self.info(
                "Note: PostgreSQL database data is left intact - only Fides configuration was removed"
            )

            # Show results
            self.summary("Cleanup Summary", deleted_counts)

            return success

        except Exception as e:
            self.final_error(f"Teardown failed: {e}")
            return False

    def _load_postgres_credentials(self) -> Dict[str, Any]:
        """Load PostgreSQL credentials from arguments or docker-compose defaults."""
        config = {
            "host": self.pg_host,
            "port": self.pg_port,
            "username": self.pg_username,
            "password": self.pg_password,
            "dbname": self.pg_dbname,
            "db_schema": self.pg_db_schema,
        }

        self.success("PostgreSQL credentials loaded successfully")
        self.success(
            f"Connecting to: {config['host']}:{config['port']}/{config['dbname']}"
        )
        self.success(f"Using schema: {config['db_schema']}")

        # Check if using defaults
        using_defaults = (
            self.pg_host == "host.docker.internal"
            and self.pg_port == 6432
            and self.pg_username == "postgres"
            and self.pg_password == "postgres"
            and self.pg_dbname == "postgres_example"
        )

        if using_defaults:
            self.info(
                "Note: Using default docker-compose.integration-postgres.yml credentials"
            )
        else:
            self.info("Note: Using custom credential arguments")

        return config

    def _load_dataset_yaml(self) -> Dict[str, Any]:
        """Load the postgres_example_test_dataset.yml file."""
        # Path relative to the repo root
        dataset_path = (
            Path(__file__).parents[2]
            / "data"
            / "dataset"
            / "postgres_example_test_dataset.yml"
        )

        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        try:
            with open(dataset_path, "r") as file:
                dataset_data = yaml.safe_load(file)

            # Validate the structure
            if "dataset" not in dataset_data or not isinstance(
                dataset_data["dataset"], list
            ):
                raise ValueError(
                    "Invalid dataset YAML structure: expected 'dataset' key with list value"
                )

            if len(dataset_data["dataset"]) == 0:
                raise ValueError("Dataset YAML contains no datasets")

            # Get the first dataset (should be postgres_example_test_dataset)
            dataset_config = dataset_data["dataset"][0]

            if dataset_config.get("fides_key") != self.dataset_key:
                self.warning(
                    f"Expected dataset key '{self.dataset_key}', got '{dataset_config.get('fides_key')}'"
                )

            self.success(
                f"Loaded dataset with {len(dataset_config.get('collections', []))} collections"
            )
            return dataset_config

        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing dataset YAML: {e}")

    def _create_dataset(self, dataset_data: Dict[str, Any]) -> bool:
        """Create the dataset in Fides."""
        try:
            self.api.create_dataset(dataset_data)
            self.success("Dataset created successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create dataset: {e}")
            raise

    def _create_system(self) -> bool:
        """Create the PostgreSQL system."""
        try:
            system_data = {
                "fides_key": self.system_name,
                "organization_fides_key": "default_organization",
                "name": "QA PostgreSQL Integration System",
                "description": "Test system for PostgreSQL integration with example test dataset.",
                "system_type": "Service",
                "privacy_declarations": [],
                "system_dependencies": [],
            }
            self.api.create_system(system_data)
            self.success("PostgreSQL system created successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create system: {e}")
            raise

    def _create_postgres_connection(self, postgres_config: Dict[str, Any]) -> bool:
        """Create PostgreSQL connection linked to system."""
        try:
            connection_data = {
                "name": "QA PostgreSQL Connection",
                "key": self.connection_key,
                "connection_type": "postgres",
                "access": "write",
                "description": "Test PostgreSQL connection for integration testing with example dataset",
                "secrets": postgres_config,
            }

            self.api.create_system_connection(self.system_name, connection_data)
            self.success("PostgreSQL connection created and linked successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create PostgreSQL connection: {e}")
            raise

    def _link_dataset_to_connection(self) -> bool:
        """Link the postgres_example_test_dataset to the connection."""
        try:
            result = self.api.link_datasets_to_connection(
                self.connection_key, [self.dataset_key]
            )

            linked_count = len(result.get("succeeded", []))
            failed_count = len(result.get("failed", []))

            if linked_count > 0:
                self.success(f"Successfully linked {self.dataset_key} to connection")

            if failed_count > 0:
                self.error(f"Failed to link dataset: {result.get('failed', [])}")
                return False

            return True

        except Exception as e:
            self.error(f"Failed to link dataset to connection: {e}")
            raise

#!/usr/bin/env python3
"""
QA scenario for testing BigQuery integration with the example test dataset and seeded data.
"""

import ast
import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from utils import QATestScenario

class BigQueryIntegrationWithData(QATestScenario):
    """QA scenario for testing BigQuery integration with bigquery_example_test_dataset and seeded data."""

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.system_name = "qa_bigquery_integration_system"
        self.connection_key = "qa_bigquery_connection"
        self.dataset_key = "bigquery_example_test_dataset"

    @property
    def description(self) -> str:
        return "Creates a BigQuery system with BigQuery integration, bigquery_example_test_dataset, and seeds comprehensive test data (self-contained)."

    def setup(self) -> bool:
        """Setup BigQuery integration with example test dataset and seeded data."""
        self.setup_phase()

        print("Setting up BigQuery integration with data seeding...")

        try:
            # Step 1: Load and validate environment variables
            self.step(1, "Validating BigQuery credentials")
            keyfile_creds, dataset = self._load_bigquery_credentials()

            # Step 2: Load the BigQuery example test dataset from YAML
            self.step(2, "Loading bigquery_example_test_dataset.yml")
            dataset_data = self._load_dataset_yaml()

            # Step 3: Create the dataset in Fides
            self.step(3, "Creating dataset in Fides")
            self._create_dataset(dataset_data)

            # Step 4: Create the system
            self.step(4, "Creating BigQuery system")
            self._create_system()

            # Step 5: Create the BigQuery connection
            self.step(5, "Creating BigQuery connection")
            self._create_bigquery_connection(keyfile_creds, dataset)

            # Step 7: Link the dataset to the connection
            self.step(7, "Linking dataset to connection")
            self._link_dataset_to_connection()

            self.final_success("You can now run an access request for customer-1@example.com")
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario."""
        self.cleanup_phase()

        print("Cleaning up BigQuery integration resources...")
        success = True
        deleted_counts = {'connections': 0, 'systems': 0, 'datasets': 0}

        try:
            # Step 1: Delete connection FIRST (cascades delete DatasetConfigs)
            self.step(1, "Deleting BigQuery connection")
            if self.api.delete_connection(self.connection_key):
                deleted_counts["connections"] += 1
                self.success(f"Deleted connection: {self.connection_key}")
            else:
                self.already_cleaned("Connection", self.connection_key)

            # Step 2: Delete system
            self.step(2, "Deleting BigQuery system")
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

            # Note: We don't clean up the seeded BigQuery data as it may be shared across tests
            self.info("Note: BigQuery test data tables are left intact for potential reuse")

            # Show results
            self.summary("Cleanup Summary", deleted_counts)

            return success

        except Exception as e:
            self.final_error(f"Teardown failed: {e}")
            return False

    def _load_bigquery_credentials(self) -> tuple[Dict[str, Any], Optional[str]]:
        """Load BigQuery credentials from environment variables."""
        # Load keyfile credentials
        keyfile_creds_str = os.environ.get("BIGQUERY_KEYFILE_CREDS")
        if not keyfile_creds_str:
            raise ValueError(
                "BIGQUERY_KEYFILE_CREDS environment variable not found. "
                "Please set this environment variable with your BigQuery service account credentials."
            )

        try:
            # Parse the keyfile credentials (could be JSON string or dict representation)
            if keyfile_creds_str.startswith('{'):
                keyfile_creds = json.loads(keyfile_creds_str)
            else:
                keyfile_creds = ast.literal_eval(keyfile_creds_str)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid BIGQUERY_KEYFILE_CREDS format: {e}")

        # Validate required fields in keyfile_creds
        required_fields = ["project_id", "client_email"]
        missing_fields = [field for field in required_fields if field not in keyfile_creds]
        if missing_fields:
            raise ValueError(f"Missing required fields in BIGQUERY_KEYFILE_CREDS: {missing_fields}")

        # Load dataset (optional)
        dataset = os.environ.get("BIGQUERY_DATASET")

        self.success("BigQuery credentials loaded successfully")
        if dataset:
            self.success(f"Using dataset: {dataset}")
        else:
            self.info("No specific dataset provided - will use default project access")

        return keyfile_creds, dataset

    def _load_dataset_yaml(self) -> Dict[str, Any]:
        """Load the bigquery_example_test_dataset.yml file."""
        # Path relative to the repo root
        dataset_path = Path(__file__).parents[2] / "data" / "dataset" / "bigquery_example_test_dataset.yml"

        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

        try:
            with open(dataset_path, 'r') as file:
                dataset_data = yaml.safe_load(file)

            # Validate the structure
            if 'dataset' not in dataset_data or not isinstance(dataset_data['dataset'], list):
                raise ValueError("Invalid dataset YAML structure: expected 'dataset' key with list value")

            if len(dataset_data['dataset']) == 0:
                raise ValueError("Dataset YAML contains no datasets")

            # Get the first dataset (should be bigquery_example_test_dataset)
            dataset_config = dataset_data['dataset'][0]

            if dataset_config.get('fides_key') != self.dataset_key:
                self.warning(f"Expected dataset key '{self.dataset_key}', got '{dataset_config.get('fides_key')}'")

            self.success(f"Loaded dataset with {len(dataset_config.get('collections', []))} collections")
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
        """Create the BigQuery system."""
        try:
            system_data = {
                "fides_key": self.system_name,
                "organization_fides_key": "default_organization",
                "name": "QA BigQuery Integration System",
                "description": "Test system for BigQuery integration with example test dataset and seeded data.",
                "system_type": "Service",
                "privacy_declarations": [],
                "system_dependencies": []
            }
            self.api.create_system(system_data)
            self.success("BigQuery system created successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create system: {e}")
            raise

    def _create_bigquery_connection(self, keyfile_creds: Dict[str, Any], dataset: Optional[str]) -> bool:
        """Create BigQuery connection linked to system."""
        try:
            # Prepare the connection secrets
            secrets = {"keyfile_creds": keyfile_creds}
            if dataset:
                secrets["dataset"] = dataset

            connection_data = {
                "name": "QA BigQuery Connection",
                "key": self.connection_key,
                "connection_type": "bigquery",
                "access": "write",
                "description": "Test BigQuery connection for integration testing with seeded data",
                "secrets": secrets,
            }

            self.api.create_system_connection(self.system_name, connection_data)
            self.success("BigQuery connection created and linked successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create BigQuery connection: {e}")
            raise

    def _link_dataset_to_connection(self) -> bool:
        """Link the bigquery_example_test_dataset to the connection."""
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

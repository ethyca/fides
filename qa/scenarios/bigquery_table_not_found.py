#!/usr/bin/env python3
"""
QA scenario for testing BigQuery TableNotFound exception handling.
This scenario renames the customer_profile collection to test collection skipping
when a table is not found.
"""

import ast
import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from utils import QATestScenario, Argument

class BigQueryTableNotFound(QATestScenario):
    """QA scenario for testing BigQuery TableNotFound exception handling."""

    # Define available arguments for this scenario
    arguments = {
                "table": Argument(
            type=str,
            default="customer_profile",
            description="Name of the table/collection to rename with '_missing' suffix to trigger table not found"
        )
    }

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.system_name = "qa_bigquery_table_not_found_system"
        self.connection_key = "qa_bigquery_table_not_found_connection"
        self.dataset_key = "bigquery_table_not_found"

        # Get the table parameter, default to customer_profile
        self.target_table = getattr(self, 'table', 'customer_profile')

    @property
    def description(self) -> str:
        return "Tests BigQuery TableNotFound exception handling by creating a dataset where a specified table is renamed with '_missing' suffix, causing collection skipping."

    def setup(self) -> bool:
        """Setup BigQuery integration with modified dataset that causes table not found."""
        self.setup_phase()

        print("Setting up BigQuery TableNotFound scenario...")

        try:
            # Step 1: Load and validate environment variables
            self.step(1, "Validating BigQuery credentials")
            keyfile_creds, dataset = self._load_bigquery_credentials()

            # Step 2: Create modified dataset with renamed target table collection
            self.step(2, f"Creating modified dataset with renamed '{self.target_table}' collection")
            dataset_data = self._create_modified_dataset()

            # Step 3: Create the dataset in Fides
            self.step(3, "Creating dataset in Fides")
            self._create_dataset(dataset_data)

            # Step 4: Create the system
            self.step(4, "Creating BigQuery system")
            self._create_system()

            # Step 5: Create the BigQuery connection
            self.step(5, "Creating BigQuery connection")
            self._create_bigquery_connection(keyfile_creds, dataset)

            # Step 6: Link the dataset to the connection
            self.step(6, "Linking dataset to connection")
            self._link_dataset_to_connection()

            self.final_success(
                f"Setup complete! You can now run an access request for customer-1@example.com to test TableNotFound handling. "
                f"The '{self.target_table}' collection should be skipped with a 'Table not found' reason "
                f"(unless other collections depend on it, in which case the request will error)."
            )
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario."""
        self.cleanup_phase()

        print("Cleaning up BigQuery TableNotFound scenario resources...")
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

    def _create_modified_dataset(self) -> Dict[str, Any]:
        """Create a modified version of the BigQuery dataset with target table renamed."""
        # Path relative to the repo root
        original_dataset_path = Path(__file__).parents[2] / "data" / "dataset" / "bigquery_example_test_dataset.yml"

        if not original_dataset_path.exists():
            raise FileNotFoundError(f"Original dataset file not found: {original_dataset_path}")

        try:
            with open(original_dataset_path, 'r') as file:
                original_data = yaml.safe_load(file)

            # Validate the structure
            if 'dataset' not in original_data or not isinstance(original_data['dataset'], list):
                raise ValueError("Invalid dataset YAML structure: expected 'dataset' key with list value")

            if len(original_data['dataset']) == 0:
                raise ValueError("Dataset YAML contains no datasets")

            # Get the first dataset and create a modified copy
            original_dataset = original_data['dataset'][0]
            modified_dataset = {
                'fides_key': self.dataset_key,
                'name': 'BigQuery Table Not Found Dataset',
                'description': f'Modified BigQuery dataset for testing TableNotFound exception handling - {self.target_table} collection renamed.',
                'collections': []
            }

            # Copy all collections, but rename target table to target_table_missing
            # and update any internal dataset references and field references
            target_table_missing = f"{self.target_table}_missing"

            for collection in original_dataset.get('collections', []):
                if collection['name'] == self.target_table:
                    # Rename the target collection
                    modified_collection = self._deep_copy_and_update_references(
                        collection, 'bigquery_example_test_dataset', self.dataset_key, self.target_table, target_table_missing
                    )
                    modified_collection['name'] = target_table_missing
                    modified_dataset['collections'].append(modified_collection)
                    self.info(f"Renamed collection '{self.target_table}' to '{target_table_missing}'")
                else:
                    # Keep all other collections as-is, but update dataset references and field references
                    modified_collection = self._deep_copy_and_update_references(
                        collection, 'bigquery_example_test_dataset', self.dataset_key, self.target_table, target_table_missing
                    )
                    modified_dataset['collections'].append(modified_collection)

            self.success(f"Created modified dataset with {len(modified_dataset['collections'])} collections")
            self.info(f"Updated all internal dataset references from 'bigquery_example_test_dataset' to '{self.dataset_key}'")
            if self.target_table != target_table_missing:
                self.info(f"Updated any field references from '{self.target_table}.*' to '{target_table_missing}.*' in other collections")
            self.warning(
                f"'{target_table_missing}' table will NOT be found when privacy request runs"
            )

            return modified_dataset

        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing original dataset YAML: {e}")

    def _deep_copy_and_update_references(self, obj: Any, old_dataset: str, new_dataset: str, old_table: str = None, new_table: str = None) -> Any:
        """Recursively copy an object and update any dataset references and field references."""
        import copy

        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == 'dataset' and value == old_dataset:
                    result[key] = new_dataset
                elif key == 'field' and old_table and new_table and isinstance(value, str) and value.startswith(f"{old_table}."):
                    # Update field references like "customer.id" to "customer_missing.id"
                    result[key] = value.replace(f"{old_table}.", f"{new_table}.")
                else:
                    result[key] = self._deep_copy_and_update_references(value, old_dataset, new_dataset, old_table, new_table)
            return result
        elif isinstance(obj, list):
            return [self._deep_copy_and_update_references(item, old_dataset, new_dataset, old_table, new_table) for item in obj]
        else:
            return copy.deepcopy(obj)

    def _create_dataset(self, dataset_data: Dict[str, Any]) -> bool:
        """Create the dataset in Fides."""
        try:
            self.api.create_dataset(dataset_data)
            self.success("Modified dataset created successfully")
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
                "name": "QA BigQuery Table Not Found System",
                "description": "Test system for BigQuery TableNotFound exception handling.",
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
                "name": "QA BigQuery Table Not Found Connection",
                "key": self.connection_key,
                "connection_type": "bigquery",
                "access": "write",
                "description": "Test BigQuery connection for TableNotFound exception handling",
                "secrets": secrets,
            }

            self.api.create_system_connection(self.system_name, connection_data)
            self.success("BigQuery connection created and linked successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create BigQuery connection: {e}")
            raise

    def _link_dataset_to_connection(self) -> bool:
        """Link the modified dataset to the connection."""
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

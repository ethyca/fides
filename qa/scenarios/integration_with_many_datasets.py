#!/usr/bin/env python3
"""
QA scenario for testing integrations with many datasets.
"""

import time
from typing import List
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.rich_helpers import create_resources_with_progress
from utils import QATestScenario, Argument
from utils.fides_api import generate_dataset, generate_system, generate_connection
from utils.rich_helpers import delete_resources_with_progress


class IntegrationWithManyDatasets(QATestScenario):
    """QA scenario for testing integrations with many datasets."""

    arguments = {
        'datasets': Argument(
            type=int,
            default=60,
            description="Number of datasets to create"
        )
    }

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.dataset_count = kwargs.get('datasets', 60)
        self.system_name = "qa_integration_test_system"
        self.connection_key = "qa_test_postgres_connection"

    @property
    def description(self) -> str:
        return "Creates an integration with specified number of datasets."

    def setup(self) -> bool:
        """Setup integration with many datasets."""
        self.setup_phase()

        print(f"Setting up integration with {self.dataset_count} datasets...")

        try:
            # Create datasets (main script ensures clean state)
            self.step(1, "Creating datasets")
            self._create_datasets(set())

            # Create system
            self.step(2, "Creating system")
            self._create_system(set())

            # Create connection
            self.step(3, "Creating connection")
            self._create_connection(set())

            # Link datasets to connection
            self.step(4, "Linking datasets to connection")
            self._link_datasets_to_connection()

            self.final_success("Setup completed successfully!")
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario.

        IMPORTANT: Delete in correct order to avoid foreign key constraint violations:
        1. Connections first (cascades delete of DatasetConfigs)
        2. Systems second
        3. CTL Datasets last
        """
        self.cleanup_phase()

        print(f"Cleaning up integration test resources...")
        success = True
        deleted_counts = {'connections': 0, 'systems': 0, 'datasets': 0}

        try:
            # Step 1: Delete connections FIRST (cascades delete DatasetConfigs)
            self.step(1, "Deleting connections")
            if self.api.delete_connection(self.connection_key):
                deleted_counts["connections"] += 1
                self.success(f"Deleted connection: {self.connection_key}")
            else:
                self.already_cleaned("Connection", self.connection_key)

            # Step 2: Delete systems
            self.step(2, "Deleting systems")
            if self.api.delete_system(self.system_name):
                deleted_counts["systems"] += 1
                self.success(f"Deleted system: {self.system_name}")
            else:
                self.already_cleaned("System", self.system_name)

            # Step 3: Delete CTL datasets LAST (now safe since DatasetConfigs are gone)
            self.step(3, "Deleting datasets")
            dataset_keys = [
                f"qa_test_dataset_{i}" for i in range(1, self.dataset_count + 1)
            ]

            deleted_count = delete_resources_with_progress(
                self.formatter, "datasets", dataset_keys, self.api.delete_dataset
            )
            deleted_counts["datasets"] = deleted_count

            # Show results
            self.summary("Cleanup Summary", deleted_counts)

            return success

        except Exception as e:
            self.final_error(f"Teardown failed: {e}")
            return False

    def _create_datasets(self, existing_datasets: set) -> List[str]:
        """Create the specified number of datasets."""

        # Generate dataset numbers
        dataset_numbers = list(range(1, self.dataset_count + 1))

        # Use the generic create function
        result = create_resources_with_progress(
            self.formatter,
            "datasets",
            dataset_numbers,
            lambda i: self.api.create_dataset(generate_dataset(i)),
            get_key_func=lambda i: f"qa_test_dataset_{i}",
        )

        return result["created"]

    def _create_system(self, existing_systems: set) -> bool:
        """Create the system."""
        try:
            system_data = generate_system(self.system_name, self.dataset_count)
            self.api.create_system(system_data)
            self.success("System created successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create system: {e}")
            raise

    def _create_connection(self, existing_connections: set) -> bool:
        """Create connection linked to system."""
        try:
            connection_data = generate_connection()
            self.api.create_system_connection(self.system_name, connection_data)
            self.success("PostgreSQL connection created and linked successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create connection: {e}")
            raise

    def _link_datasets_to_connection(self):
        """Link the specified number of QA datasets to the connection."""
        try:
            # Link the datasets for this scenario (1 to dataset_count)
            qa_dataset_keys = [
                f"qa_test_dataset_{i}" for i in range(1, self.dataset_count + 1)
            ]

            # Link all datasets at once
            result = self.api.link_datasets_to_connection(
                self.connection_key, qa_dataset_keys
            )

            linked_count = len(result.get("succeeded", []))
            failed_count = len(result.get("failed", []))

            if linked_count > 0:
                self.success(
                    f"Successfully linked {linked_count}/{len(qa_dataset_keys)} datasets to connection"
                )

            if failed_count > 0:
                self.error(f"Failed to link {failed_count} datasets")
                # Show which datasets failed
                failed_datasets = result.get("failed", [])
                if failed_datasets:
                    self.error(
                        f"Failed datasets: {', '.join(failed_datasets[:5])}{'...' if len(failed_datasets) > 5 else ''}",
                        indent=4,
                    )

        except Exception as e:
            self.error(f"Failed to link datasets to connection: {e}")
            raise

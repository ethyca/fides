#!/usr/bin/env python3
"""
QA scenario for testing integrations with many datasets.
"""

import time
from typing import List
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils import QATestScenario, generate_dataset, generate_system, generate_connection
from utils.qa_test_scenario import Argument


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
        print(f"Setting up integration with {self.dataset_count} datasets...")

        try:
            # Create datasets (main script ensures clean state)
            self._create_datasets(set())

            # Create system
            self._create_system(set())

            # Create connection
            self._create_connection(set())

            # Link datasets to connection
            self._link_datasets_to_connection()

            print("Setup completed successfully!")
            return True

        except Exception as e:
            print(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario.

        IMPORTANT: Delete in correct order to avoid foreign key constraint violations:
        1. Connections first (cascades delete of DatasetConfigs)
        2. Systems second
        3. CTL Datasets last
        """
        print(f"Cleaning up integration test resources...")
        success = True
        deleted_counts = {'connections': 0, 'systems': 0, 'datasets': 0}

        try:
            # Get current resources to delete
            all_datasets = self.api.get_datasets()
            all_systems = self.api.get_systems()
            all_connections = self.api.get_connections()

            qa_datasets = [d for d in all_datasets if d.get('fides_key', '').startswith('qa_test_dataset_')]
            qa_systems = [s for s in all_systems if s.get('fides_key') == self.system_name]
            qa_connections = [c for c in all_connections if c.get('key') == self.connection_key]

            # Step 1: Delete connections FIRST (cascades delete DatasetConfigs)
            print("Deleting connections...")
            for connection in qa_connections:
                connection_key = connection.get('key')
                if connection_key and self.api.delete_connection(connection_key):
                    deleted_counts['connections'] += 1
                    print(f"Deleted connection: {connection_key}")

            # Step 2: Delete systems
            print("Deleting systems...")
            for system in qa_systems:
                system_key = system.get('fides_key')
                if system_key and self.api.delete_system(system_key):
                    deleted_counts['systems'] += 1
                    print(f"Deleted system: {system_key}")

            # Step 3: Delete CTL datasets LAST (now safe since DatasetConfigs are gone)
            if qa_datasets:
                print("Deleting datasets...")
                for i, dataset in enumerate(qa_datasets):
                    dataset_key = dataset.get('fides_key')
                    if dataset_key and self.api.delete_dataset(dataset_key):
                        deleted_counts['datasets'] += 1
                        print(f"Deleted dataset: {dataset_key}")
                    time.sleep(0.1)
                print()

            # Show results
            total_deleted = sum(deleted_counts.values())
            print(f"Cleanup Summary:")
            for resource_type, count in deleted_counts.items():
                print(f"  {resource_type}: {count}")
            print(f"  Total: {total_deleted}")

            return success

        except Exception as e:
            print(f"Teardown failed: {e}")
            return False

    def _create_datasets(self, existing_datasets: set) -> List[str]:
        """Create the specified number of datasets."""
        print(f"Creating {self.dataset_count} datasets...")
        created_datasets = []

        for i in range(1, self.dataset_count + 1):
            dataset_key = f"qa_test_dataset_{i}"
            try:
                dataset_data = generate_dataset(i)
                self.api.create_dataset(dataset_data)
                created_datasets.append(dataset_key)
                time.sleep(0.1)
            except Exception as e:
                print(f"Failed to create dataset {dataset_key}: {e}")
                continue

            # Simple progress indicator
            if i % 10 == 0:  # Show progress every 10 items
                print(f"Progress: {i}/{self.dataset_count} datasets created")

        print(f"Created {len(created_datasets)}/{self.dataset_count} datasets")
        return created_datasets

    def _create_system(self, existing_systems: set) -> bool:
        """Create the system."""
        print("Creating system...")
        try:
            system_data = generate_system(self.system_name, self.dataset_count)
            self.api.create_system(system_data)
            print("System created successfully")
            return True
        except Exception as e:
            print(f"Failed to create system: {e}")
            raise

    def _create_connection(self, existing_connections: set) -> bool:
        """Create connection linked to system."""
        print("Creating PostgreSQL connection linked to system...")
        try:
            connection_data = generate_connection()
            self.api.create_system_connection(self.system_name, connection_data)
            print("PostgreSQL connection created and linked successfully")
            return True
        except Exception as e:
            print(f"Failed to create connection: {e}")
            raise

    def _link_datasets_to_connection(self):
        """Link the specified number of QA datasets to the connection."""
        print("Linking datasets to PostgreSQL connection...")
        try:
            # Only link the datasets for this scenario (1 to dataset_count)
            qa_dataset_keys = [
                f"qa_test_dataset_{i}" for i in range(1, self.dataset_count + 1)
            ]

            # Verify these datasets exist before trying to link them
            all_datasets = self.api.get_datasets()
            existing_dataset_keys = {
                d.get("fides_key") for d in all_datasets if d.get("fides_key")
            }

            # Filter to only datasets that actually exist
            datasets_to_link = [
                key for key in qa_dataset_keys if key in existing_dataset_keys
            ]

            if datasets_to_link:
                result = self.api.link_datasets_to_connection(
                    self.connection_key, datasets_to_link
                )
                linked_count = len(result.get('succeeded', []))
                failed_count = len(result.get('failed', []))
                print(
                    f"Linked {linked_count}/{len(datasets_to_link)} datasets to connection (failed: {failed_count})"
                )
            else:
                print("No matching QA datasets found to link")
        except Exception as e:
            print(f"Failed to link datasets to connection: {e}")
            print("Datasets may need manual linking in the UI")

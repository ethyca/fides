#!/usr/bin/env python3
"""
QA scenario for testing dataset creation with nested fields.
Creates 100 datasets, each with 100 collections, 10 fields each, and random field nesting up to 3 levels.
"""

import random
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root and qa directory to path for imports
project_root = Path(__file__).parent.parent.parent
qa_dir = project_root / "qa"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(qa_dir) not in sys.path:
    sys.path.insert(0, str(qa_dir))

from utils import QATestScenario, Argument
from utils.rich_helpers import create_resources_with_progress, delete_resources_with_progress


class NestedDatasetsGeneration(QATestScenario):
    """QA scenario for testing nested dataset generation."""

    arguments = {
        'datasets': Argument(
            type=int,
            default=100,
            description="Number of datasets to create"
        ),
        'collections': Argument(
            type=int,
            default=100,
            description="Number of collections per dataset"
        ),
        'fields': Argument(
            type=int,
            default=10,
            description="Number of fields per collection"
        ),
        'max_nesting_level': Argument(
            type=int,
            default=3,
            description="Maximum nesting level for fields"
        )
    }

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.dataset_count = kwargs.get('datasets', 100)
        self.collection_count = kwargs.get('collections', 100)
        self.field_count = kwargs.get('fields', 10)
        self.max_nesting_level = kwargs.get('max_nesting_level', 3)
        self.system_name = "nested_qa_test_system"
        self.connection_key = "nested_qa_test_connection"

        # Statistics tracking
        self.redact_stats = {
            'datasets': 0,
            'collections': 0,
            'fields': 0
        }

    @property
    def description(self) -> str:
        return f"Creates {self.dataset_count} datasets with {self.collection_count} collections each, {self.field_count} fields per collection, with up to {self.max_nesting_level} levels of field nesting. Randomly adds fides_meta.redact: name annotations. Links datasets to a connection via DatasetConfig."

    def setup(self) -> bool:
        """Setup datasets with nested field structures."""
        self.setup_phase()

        print(f"Setting up {self.dataset_count} datasets with nested field structures...")
        print(f"Each dataset will have {self.collection_count} collections with {self.field_count} fields each")

        try:
            # Create datasets with nested fields
            self.step(1, "Creating datasets with nested field structures")
            self._create_nested_datasets()

            # Create system
            self.step(2, "Creating system")
            self._create_system()

            # Create connection
            self.step(3, "Creating connection")
            self._create_connection()

            # Link datasets to connection
            self.step(4, "Linking datasets to connection")
            self._link_datasets_to_connection()

            self.success(f"Setup completed successfully! Created {self.dataset_count} datasets with DatasetConfig.")
            self.info(f"Redact annotations added:")
            self.info(f"  - Datasets: {self.redact_stats['datasets']}")
            self.info(f"  - Collections: {self.redact_stats['collections']}")
            self.info(f"  - Fields: {self.redact_stats['fields']}")
            return True

        except Exception as e:
            self.error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario.

        IMPORTANT: Delete in correct order to avoid foreign key constraint violations:
        1. Connections first (cascades delete of DatasetConfigs)
        2. Systems second
        3. CTL Datasets last
        """
        self.cleanup_phase()

        print(f"Cleaning up nested datasets integration test resources...")
        success = True
        deleted_counts = {'connections': 0, 'systems': 0, 'datasets': 0}

        try:
            # Step 1: Delete connections FIRST (cascades delete DatasetConfigs)
            self.step(1, "Deleting connections")
            if self.api.delete_connection(self.connection_key):
                deleted_counts["connections"] += 1
                self.success(f"Deleted connection: {self.connection_key}")
            else:
                self.info(f"Connection {self.connection_key} already cleaned or not found")

            # Step 2: Delete systems
            self.step(2, "Deleting systems")
            if self.api.delete_system(self.system_name):
                deleted_counts["systems"] += 1
                self.success(f"Deleted system: {self.system_name}")
            else:
                self.info(f"System {self.system_name} already cleaned or not found")

            # Step 3: Delete CTL datasets LAST (now safe since DatasetConfigs are gone)
            self.step(3, "Deleting datasets")
            dataset_keys = [
                f"nested_qa_dataset_{i}" for i in range(1, self.dataset_count + 1)
            ]

            deleted_count = delete_resources_with_progress(
                self.formatter, "datasets", dataset_keys, self.api.delete_dataset
            )
            deleted_counts["datasets"] = deleted_count

            # Show results
            self.success(f"Cleanup completed! Deleted {deleted_counts['connections']} connections, {deleted_counts['systems']} systems, {deleted_counts['datasets']} datasets.")

            return success

        except Exception as e:
            self.error(f"Teardown failed: {e}")
            return False

    def _create_nested_datasets(self) -> List[str]:
        """Create datasets with nested field structures."""

        # Generate dataset numbers
        dataset_numbers = list(range(1, self.dataset_count + 1))

        # Use the generic create function
        result = create_resources_with_progress(
            self.formatter,
            "datasets",
            dataset_numbers,
            lambda i: self.api.create_dataset(self._generate_nested_dataset(i)),
            get_key_func=lambda i: f"nested_qa_dataset_{i}",
        )

        return result["created"]

    def _generate_nested_dataset(self, index: int) -> Dict[str, Any]:
        """Generate a dataset with nested field structures."""
        collections = []

        for collection_idx in range(1, self.collection_count + 1):
            collection = {
                "name": f"collection_{collection_idx}",
                "description": f"Collection {collection_idx} with nested fields",
                "data_categories": [],
                "fields": self._generate_nested_fields(collection_idx)
            }

            # Add random redact annotation to collection (20% chance)
            if random.random() < 0.2:
                collection["fides_meta"] = {"redact": "name"}
                self.redact_stats['collections'] += 1

            collections.append(collection)

        dataset = {
            "fides_key": f"nested_qa_dataset_{index}",
            "organization_fides_key": "default_organization",
            "name": f"Nested QA Dataset {index}",
            "description": f"Test dataset {index} with nested field structures for QA testing.",
            "meta": None,
            "data_categories": [],
            "collections": collections
        }

        # Add random redact annotation to dataset (15% chance)
        if random.random() < 0.15:
            dataset["fides_meta"] = {"redact": "name"}
            self.redact_stats['datasets'] += 1

        return dataset

    def _generate_nested_fields(self, collection_idx: int) -> List[Dict[str, Any]]:
        """Generate fields with random nesting up to max_nesting_level."""
        fields = []

        for field_idx in range(1, self.field_count + 1):
            # Decide if this field should be nested (30% chance for each level)
            nesting_level = 0
            while nesting_level < self.max_nesting_level and random.random() < 0.3:
                nesting_level += 1

            field = self._create_field(f"field_{field_idx}", field_idx, collection_idx, nesting_level)
            fields.append(field)

        return fields

    def _create_field(self, field_name: str, field_idx: int, collection_idx: int, nesting_level: int) -> Dict[str, Any]:
        """Create a field with the specified nesting level."""

        # Base field structure
        field = {
            "name": field_name,
            "description": f"Field {field_idx} in collection {collection_idx}",
            "data_categories": self._get_random_data_categories()
        }

        # Add metadata for some fields
        fides_meta = {}

        if field_idx == 1:  # Make first field a primary key
            fides_meta["primary_key"] = True
        elif field_idx == 2 and collection_idx % 5 == 0:  # Add identity field occasionally
            fides_meta.update({
                "identity": "email",
                "data_type": "string"
            })
        elif field_idx == 3 and collection_idx % 7 == 0:  # Add references occasionally
            fides_meta["references"] = [{
                "dataset": f"nested_qa_dataset_{(collection_idx % 10) + 1}",
                "field": f"collection_{(collection_idx % 5) + 1}.field_1",
                "direction": "to"
            }]

        # Add random redact annotation to field (25% chance)
        if random.random() < 0.25:
            fides_meta["redact"] = "name"
            self.redact_stats['fields'] += 1

        # Only add fides_meta if it has content
        if fides_meta:
            field["fides_meta"] = fides_meta

        # Add nested fields if nesting_level > 0
        if nesting_level > 0:
            nested_fields = []
            num_nested_fields = random.randint(2, 5)  # 2-5 nested fields

            for nested_idx in range(1, num_nested_fields + 1):
                nested_field = self._create_field(
                    f"{field_name}_nested_{nested_idx}",
                    nested_idx,
                    collection_idx,
                    nesting_level - 1
                )
                nested_fields.append(nested_field)

            field["fields"] = nested_fields

            # Fields with sub-fields must have data_type: "object"
            if "fides_meta" not in field:
                field["fides_meta"] = {}
            field["fides_meta"]["data_type"] = "object"

        return field

    def _get_random_data_categories(self) -> List[str]:
        """Get random data categories for fields."""
        categories = [
            ["user.unique_id"],
            ["user.name"],
            ["user.contact.email"],
            ["user.contact.phone_number"],
            ["user.contact.address.street"],
            ["user.contact.address.city"],
            ["user.contact.address.state"],
            ["user.contact.address.postal_code"],
            ["user.financial"],
            ["user.financial.bank_account"],
            ["user.demographic"],
            ["user.demographic.age_range"],
            ["user.demographic.gender"],
            ["user.behavior"],
            ["user.behavior.browsing_history"],
            ["user.sensor"],
            ["user.device"],
            ["user.device.cookie_id"],
            ["system.operations"],
        ]

        # Return a random category
        return random.choice(categories)

    def _create_system(self) -> bool:
        """Create the system."""
        try:
            system_data = self._generate_system()
            self.api.create_system(system_data)
            self.success("System created successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create system: {e}")
            raise

    def _create_connection(self) -> bool:
        """Create connection linked to system."""
        try:
            connection_data = self._generate_connection()
            self.api.create_system_connection(self.system_name, connection_data)
            self.success("PostgreSQL connection created and linked successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create connection: {e}")
            raise

    def _link_datasets_to_connection(self):
        """Link all nested datasets to the connection."""
        try:
            # Link the datasets for this scenario (1 to dataset_count)
            dataset_keys = [
                f"nested_qa_dataset_{i}" for i in range(1, self.dataset_count + 1)
            ]

            # Link all datasets at once
            result = self.api.link_datasets_to_connection(
                self.connection_key, dataset_keys
            )

            linked_count = len(result.get("succeeded", []))
            failed_count = len(result.get("failed", []))

            if linked_count > 0:
                self.success(
                    f"Successfully linked {linked_count}/{len(dataset_keys)} datasets to connection"
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

    def _generate_system(self) -> Dict[str, Any]:
        """Generate a system for the nested datasets."""
        return {
            "fides_key": self.system_name,
            "organization_fides_key": "default_organization",
            "name": "Nested QA Test System",
            "description": f"Test system with {self.dataset_count} nested datasets for QA testing.",
            "system_type": "Service",
            "privacy_declarations": [],
            "system_dependencies": []
        }

    def _generate_connection(self) -> Dict[str, Any]:
        """Generate a connection for the nested datasets."""
        return {
            "name": "Nested QA Test PostgreSQL Connection",
            "key": self.connection_key,
            "connection_type": "postgres",
            "access": "write",
            "description": "Test PostgreSQL connection for nested datasets QA testing",
            "secrets": {"host": "localhost"},
        }

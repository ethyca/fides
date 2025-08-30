#!/usr/bin/env python3
"""
QA scenario for testing redact: name annotations on Postgres and MongoDB datasets.

This scenario creates:
1. Postgres and MongoDB systems with integrations
2. Modified versions of existing datasets with redact: name annotations
3. Deterministic selection of collections and fields for redaction testing
"""

import copy
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List

sys.path.append(str(Path(__file__).parent.parent))
from utils import QATestScenario, Argument
from utils.fides_api import FidesAPI


class RedactAnnotationScenario(QATestScenario):
    """QA scenario for testing redact: name annotations on datasets."""

    arguments = {}

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)

        # Resource names
        self.postgres_system_key = "qa_postgres_redact_system"
        self.mongo_system_key = "qa_mongo_redact_system"
        self.postgres_connection_key = "qa_postgres_redact_connection"
        self.mongo_connection_key = "qa_mongo_redact_connection"
        self.postgres_dataset_key = "postgres_redact_test_dataset"
        self.mongo_dataset_key = "mongo_test"

    @property
    def description(self) -> str:
        return "Creates Postgres and MongoDB systems with datasets containing redact: name annotations for testing DSR report redaction."

    def _load_original_datasets(self) -> Dict[str, Any]:
        """Load the original dataset files from the repository."""
        # Get the path to the fides repository root
        fides_root = Path(__file__).parent.parent.parent

        postgres_dataset_path = fides_root / "data" / "dataset" / "postgres_example_test_dataset.yml"
        mongo_dataset_path = fides_root / "data" / "dataset" / "mongo_example_test_dataset.yml"

        datasets = {}

        # Load Postgres dataset
        with open(postgres_dataset_path, 'r') as f:
            postgres_data = yaml.safe_load(f)
            datasets['postgres'] = postgres_data['dataset'][0]  # Get the first dataset from the list

        # Load MongoDB dataset
        with open(mongo_dataset_path, 'r') as f:
            mongo_data = yaml.safe_load(f)
            datasets['mongo'] = mongo_data['dataset'][0]  # Get the first dataset from the list

        return datasets

    def setup(self) -> bool:
        """Setup the redact annotation test scenario."""
        self.setup_phase()

        try:
            # Step 1: Create modified datasets with redact annotations
            self.step(1, "Creating datasets with redact annotations")
            self._create_datasets()

            # Step 2: Create systems
            self.step(2, "Creating systems")
            self._create_systems()

            # Step 3: Create connections
            self.step(3, "Creating connections")
            self._create_connections()

            # Step 4: Link datasets to connections
            self.step(4, "Linking datasets to connections")
            self._link_datasets_to_connections()

            self.success("Setup completed successfully!")
            return True

        except Exception as e:
            self.error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario."""
        self.cleanup_phase()

        success = True
        deleted_counts = {'connections': 0, 'systems': 0, 'datasets': 0}

        try:
            # Step 1: Delete connections first (cascades delete DatasetConfigs)
            self.step(1, "Deleting connections")
            for connection_key in [self.postgres_connection_key, self.mongo_connection_key]:
                if self.api.delete_connection(connection_key):
                    deleted_counts["connections"] += 1
                    self.success(f"Deleted connection: {connection_key}")

            # Step 2: Delete systems
            self.step(2, "Deleting systems")
            for system_key in [self.postgres_system_key, self.mongo_system_key]:
                if self.api.delete_system(system_key):
                    deleted_counts["systems"] += 1
                    self.success(f"Deleted system: {system_key}")

            # Step 3: Delete datasets and restore original mongo_test
            self.step(3, "Deleting datasets and restoring originals")

            # Delete Postgres dataset
            if self.api.delete_dataset(self.postgres_dataset_key):
                deleted_counts["datasets"] += 1
                self.success(f"Deleted dataset: {self.postgres_dataset_key}")

            # Delete the modified mongo_test dataset and restore the original
            if self.api.delete_dataset(self.mongo_dataset_key):
                deleted_counts["datasets"] += 1
                self.success(f"Deleted modified dataset: {self.mongo_dataset_key}")

                # Restore the original mongo_test dataset
                try:
                    original_datasets = self._load_original_datasets()
                    original_mongo = original_datasets['mongo']
                    self.api.create_dataset(original_mongo)
                    self.success("Restored original mongo_test dataset")
                except Exception as e:
                    self.warning(f"Could not restore original mongo_test dataset: {e}")

            # Show results
            self.info(f"Cleanup completed: {deleted_counts}")
            return success

        except Exception as e:
            self.error(f"Teardown failed: {e}")
            return False

    def _create_datasets(self):
        """Create modified versions of existing datasets with redact annotations."""
        # Load original datasets
        original_datasets = self._load_original_datasets()

        # Create Postgres dataset with redact annotations
        postgres_dataset = self._add_redact_annotations_to_postgres(original_datasets['postgres'])
        self.api.create_dataset(postgres_dataset)
        self.success(f"Created Postgres dataset: {self.postgres_dataset_key}")

        # For MongoDB, we need to delete the existing mongo_test dataset first if it exists
        # since we're going to replace it with our redacted version
        existing_mongo = self.api.get_dataset("mongo_test")
        if existing_mongo:
            self.api.delete_dataset("mongo_test")
            self.info("Deleted existing mongo_test dataset to replace with redacted version")

        # Create MongoDB dataset with redact annotations
        mongo_dataset = self._add_redact_annotations_to_mongo(original_datasets['mongo'])
        self.api.create_dataset(mongo_dataset)
        self.success(f"Created MongoDB dataset: {self.mongo_dataset_key}")

    def _add_redact_annotations_to_postgres(self, original_dataset: Dict[str, Any]) -> Dict[str, Any]:
        """Add redact annotations to a copy of the original Postgres dataset."""
        dataset = copy.deepcopy(original_dataset)

        # Update dataset metadata
        dataset["fides_key"] = self.postgres_dataset_key
        dataset["name"] = "Postgres Redact Test Dataset"
        dataset["description"] = "Modified Postgres dataset with redact: name annotations for testing DSR report redaction"
        dataset["fides_meta"] = {"redact": "name"}  # Redact the dataset name itself

        # Deterministically select collections and fields to redact
        collections_to_redact = ["address", "employee", "payment_card"]  # Always these 3
        fields_to_redact = {
            "address": ["state"],
            "customer": ["email"],
            "employee": ["name"],
            "payment_card": ["ccn"]
        }

        # Apply redact annotations
        for collection in dataset.get("collections", []):
            collection_name = collection.get("name", "")

            # Redact collection names
            if collection_name in collections_to_redact:
                if "fides_meta" not in collection:
                    collection["fides_meta"] = {}
                collection["fides_meta"]["redact"] = "name"

            # Redact field names
            if collection_name in fields_to_redact:
                for field in collection.get("fields", []):
                    field_name = field.get("name", "")
                    if field_name in fields_to_redact[collection_name]:
                        if "fides_meta" not in field:
                            field["fides_meta"] = {}
                        field["fides_meta"]["redact"] = "name"

        # Update all dataset references using deep copy method
        dataset = self._deep_copy_and_update_references(dataset, original_dataset["fides_key"], self.postgres_dataset_key)

        return dataset

    def _add_redact_annotations_to_mongo(self, original_dataset: Dict[str, Any]) -> Dict[str, Any]:
        """Add redact annotations to a copy of the original MongoDB dataset."""
        dataset = copy.deepcopy(original_dataset)

        # Update dataset metadata
        dataset["fides_key"] = self.mongo_dataset_key
        dataset["name"] = "MongoDB Redact Test Dataset"
        dataset["description"] = "Modified MongoDB dataset with redact: name annotations for testing DSR report redaction"

        # Deterministically select collections and fields to redact
        collections_to_redact = ["customer_details", "customer_feedback"]  # Always these 2
        fields_to_redact = {
            "customer_details": ["gender"],
            "customer_feedback": [],  # Will handle nested fields separately
            "conversations": []  # Will handle nested fields separately
        }
        nested_fields_to_redact = {
            "customer_details.workplace_info": ["employer"],
            "customer_feedback.customer_information": ["phone"],
            "conversations.thread": ["chat_name"]
        }

        # Apply redact annotations
        for collection in dataset.get("collections", []):
            collection_name = collection.get("name", "")

            # Redact collection names
            if collection_name in collections_to_redact:
                if "fides_meta" not in collection:
                    collection["fides_meta"] = {}
                collection["fides_meta"]["redact"] = "name"

            # Redact top-level field names
            if collection_name in fields_to_redact:
                for field in collection.get("fields", []):
                    field_name = field.get("name", "")
                    if field_name in fields_to_redact[collection_name]:
                        if "fides_meta" not in field:
                            field["fides_meta"] = {}
                        field["fides_meta"]["redact"] = "name"

            # Redact nested field names
            self._apply_nested_redact_annotations(collection, collection_name, nested_fields_to_redact)

        # Update all dataset references using deep copy method
        dataset = self._deep_copy_and_update_references(dataset, original_dataset["fides_key"], self.mongo_dataset_key)

        # Also update any cross-references to the Postgres dataset
        dataset = self._deep_copy_and_update_references(dataset, "postgres_example_test_dataset", self.postgres_dataset_key)

        return dataset

    def _apply_nested_redact_annotations(self, collection: Dict[str, Any], collection_name: str, nested_fields_to_redact: Dict[str, List[str]]):
        """Apply redact annotations to nested fields."""
        for field in collection.get("fields", []):
            field_name = field.get("name", "")
            field_path = f"{collection_name}.{field_name}"

            if field_path in nested_fields_to_redact:
                # This field has nested fields that need redaction
                for nested_field in field.get("fields", []):
                    nested_field_name = nested_field.get("name", "")
                    if nested_field_name in nested_fields_to_redact[field_path]:
                        if "fides_meta" not in nested_field:
                            nested_field["fides_meta"] = {}
                        nested_field["fides_meta"]["redact"] = "name"

    def _deep_copy_and_update_references(self, obj: Any, old_dataset: str, new_dataset: str) -> Any:
        """Recursively copy an object and update any dataset references."""
        import copy

        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == 'dataset' and value == old_dataset:
                    result[key] = new_dataset
                elif key == "erase_after" and isinstance(value, list):
                    # Update erase_after references like ["postgres_example_test_dataset.customer"]
                    updated_erase_after = []
                    for item in value:
                        if isinstance(item, str) and item.startswith(f"{old_dataset}."):
                            updated_item = item.replace(f"{old_dataset}.", f"{new_dataset}.")
                            updated_erase_after.append(updated_item)
                        else:
                            updated_erase_after.append(item)
                    result[key] = updated_erase_after
                else:
                    result[key] = self._deep_copy_and_update_references(value, old_dataset, new_dataset)
            return result
        elif isinstance(obj, list):
            return [self._deep_copy_and_update_references(item, old_dataset, new_dataset) for item in obj]
        else:
            return copy.deepcopy(obj)

    def _create_systems(self):
        """Create Postgres and MongoDB systems."""
        # Create Postgres system
        postgres_system = {
            "fides_key": self.postgres_system_key,
            "organization_fides_key": "default_organization",
            "name": "QA Postgres Redact Test System",
            "description": "Test PostgreSQL system for redact annotation testing",
            "system_type": "Database",
            "privacy_declarations": [],
            "system_dependencies": []
        }
        self.api.create_system(postgres_system)
        self.success(f"Created Postgres system: {self.postgres_system_key}")

        # Create MongoDB system
        mongo_system = {
            "fides_key": self.mongo_system_key,
            "organization_fides_key": "default_organization",
            "name": "QA MongoDB Redact Test System",
            "description": "Test MongoDB system for redact annotation testing",
            "system_type": "Database",
            "privacy_declarations": [],
            "system_dependencies": []
        }
        self.api.create_system(mongo_system)
        self.success(f"Created MongoDB system: {self.mongo_system_key}")

    def _create_connections(self):
        """Create Postgres and MongoDB connections."""
        # Create Postgres connection
        postgres_connection = {
            "name": "QA Postgres Redact Test Connection",
            "key": self.postgres_connection_key,
            "connection_type": "postgres",
            "access": "write",
            "description": "Test PostgreSQL connection for redact annotation testing",
            "secrets": {"host": "host.docker.internal", "port": 6432, "dbname": "postgres_example", "username": "postgres", "password": "postgres"}
        }
        self.api.create_system_connection(self.postgres_system_key, postgres_connection)
        self.success(f"Created Postgres connection: {self.postgres_connection_key}")

        # Create MongoDB connection
        mongo_connection = {
            "name": "QA MongoDB Redact Test Connection",
            "key": self.mongo_connection_key,
            "connection_type": "mongodb",
            "access": "write",
            "description": "Test MongoDB connection for redact annotation testing",
            "secrets": {"host": "mongodb_example", "port": 27017, "defaultauthdb": "mongo_test", "username": "mongo_user", "password": "mongo_pass"}
        }
        self.api.create_system_connection(self.mongo_system_key, mongo_connection)
        self.success(f"Created MongoDB connection: {self.mongo_connection_key}")

    def _link_datasets_to_connections(self):
        """Link datasets to their respective connections."""
        # Link Postgres dataset to Postgres connection
        postgres_result = self.api.link_datasets_to_connection(
            self.postgres_connection_key, [self.postgres_dataset_key]
        )
        if postgres_result.get("succeeded"):
            self.success(f"Linked Postgres dataset to connection")
        else:
            self.error(f"Failed to link Postgres dataset: {postgres_result.get('failed', [])}")

        # Link MongoDB dataset to MongoDB connection
        mongo_result = self.api.link_datasets_to_connection(
            self.mongo_connection_key, [self.mongo_dataset_key]
        )
        if mongo_result.get("succeeded"):
            self.success(f"Linked MongoDB dataset to connection")
        else:
            self.error(f"Failed to link MongoDB dataset: {mongo_result.get('failed', [])}")

    def get_redacted_entities_summary(self) -> Dict[str, List[str]]:
        """Return a summary of which entities have redact annotations for verification."""
        return {
            "postgres_dataset": ["postgres_redact_test_dataset"],  # Dataset-level redaction
            "postgres_collections": ["address", "employee", "payment_card"],
            "postgres_fields": [
                "address.state",
                "customer.email",
                "employee.name",
                "payment_card.ccn"
            ],
            "mongo_collections": ["customer_details", "customer_feedback"],
            "mongo_fields": [
                "customer_details.gender",
                "customer_details.workplace_info.employer",
                "customer_feedback.customer_information.phone",
                "conversations.thread.chat_name"
            ]
        }

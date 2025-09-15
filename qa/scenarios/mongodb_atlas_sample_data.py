#!/usr/bin/env python3
"""
QA scenario for testing MongoDB Atlas integration using the actual data from nox -s dev -- mongodb.
This scenario replicates the exact seed data and dataset configuration used by the dev environment.
"""

import copy
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4

import yaml
from bson import Binary
from pymongo import MongoClient

sys.path.append(os.path.join(os.path.dirname(__file__), '../../tests/ops/integration_tests/mongodb_atlas'))
from mongo_sample import mongo_sample_data
from utils import QATestScenario


def load_dataset_configs():
    """Load the actual dataset YAML files and return them as dictionaries."""
    # Get the path to the dataset files
    script_dir = Path(__file__).parent
    fides_root = script_dir.parent.parent

    postgres_dataset_path = fides_root / "data" / "dataset" / "postgres_example_test_dataset.yml"
    mongo_dataset_path = fides_root / "data" / "dataset" / "mongo_example_test_dataset.yml"

    # Load postgres dataset
    with open(postgres_dataset_path, 'r') as f:
        postgres_data = yaml.safe_load(f)

    # Load mongo dataset
    with open(mongo_dataset_path, 'r') as f:
        mongo_data = yaml.safe_load(f)

    return postgres_data['dataset'][0], mongo_data['dataset'][0]


def create_qa_datasets(postgres_dataset_key, mongo_dataset_key):
    """
    Create datasets using actual YAML files but with dynamic QA keys.
    Similar to create_atlas_datasets in test_mongo_atlas_task.py
    """
    postgres_dataset_config, mongo_dataset_config = load_dataset_configs()

    # Update postgres dataset with QA key
    postgres_dataset_config = copy.deepcopy(postgres_dataset_config)
    postgres_dataset_config["fides_key"] = postgres_dataset_key
    postgres_dataset_config["name"] = f"QA {postgres_dataset_config['name']}"
    postgres_dataset_config["description"] = f"QA version of {postgres_dataset_config['description']}"

    # Update mongo dataset with QA key and replace all references
    mongo_dataset_config = copy.deepcopy(mongo_dataset_config)
    mongo_dataset_config["fides_key"] = mongo_dataset_key
    mongo_dataset_config["name"] = f"QA {mongo_dataset_config['name']}"
    mongo_dataset_config["description"] = f"QA version of {mongo_dataset_config['description']}"

    # Recursively replace all dataset references with QA keys
    def replace_dataset_references(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "dataset":
                    if value == "postgres_example_test_dataset":
                        obj[key] = postgres_dataset_key
                    elif value == "mongo_test":
                        obj[key] = mongo_dataset_key
                else:
                    replace_dataset_references(value)
        elif isinstance(obj, list):
            for item in obj:
                replace_dataset_references(item)

    replace_dataset_references(postgres_dataset_config)
    replace_dataset_references(mongo_dataset_config)

    return postgres_dataset_config, mongo_dataset_config


class MongoDBAtlasSampleData(QATestScenario):
    """
    QA scenario for MongoDB Atlas integration using the actual nox dev sample data.

    This scenario:
    1. Seeds the same data as 'nox -s dev -- mongodb'
    2. Uses the same dataset configurations as the dev environment
    3. Creates the same system and connection structure
    4. Supports full graph traversal for privacy requests
    """

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)

        # Get or generate unique identifiers for this QA run (persisted via lock file)
        unique_suffix = self._get_unique_suffix()
        self.unique_db_name = f"mongo_qa_{unique_suffix}" if unique_suffix else None

        # All resources use the same unique suffix for proper cleanup
        self.system_name = "mongo_qa_atlas_system"
        self.connection_key = "mongo_qa_atlas_connection"

        self.postgres_system_name = "mongo_qa_postgres_system"
        self.postgres_connection_key = "mongo_qa_postgres_connection"

        # MongoDB dataset name must match database name for connector to work
        self.mongo_dataset_key = self.unique_db_name
        self.postgres_dataset_key = "mongo_qa_postgres"

        # MongoDB client (will be set during setup)
        self.mongo_client = None

        # API client will be available as self.api from parent class

    def _get_unique_suffix(self) -> str:
        """Get existing unique suffix from lock file."""
        lock_file_path = Path.home() / ".fides_mongodb_atlas_qa.lock"
        if lock_file_path.exists():
            with open(lock_file_path, "r") as f:
                return f.read().strip()
        return None

    def _create_unique_suffix(self) -> str:
        """Create a new unique suffix and save to lock file."""
        suffix = str(uuid4())[:8]
        lock_file_path = Path.home() / ".fides_mongodb_atlas_qa.lock"
        with open(lock_file_path, "w") as f:
            f.write(suffix)
        return suffix

    def _remove_lock_file(self):
        """Remove the lock file after successful teardown."""
        lock_file_path = Path.home() / ".fides_mongodb_atlas_qa.lock"
        try:
            if lock_file_path.exists():
                lock_file_path.unlink()
                print("Removed lock file after successful cleanup")
        except Exception as e:
            print(f"Could not remove lock file: {e}")

    @property
    def description(self) -> str:
        return "Creates a MongoDB Atlas system using the actual YAML dataset configurations and sample data from the repository. Uses mongo_qa_* prefixed names for all resources to avoid conflicts. Supports full graph traversal for privacy requests."

    def _validate_environment_variables(self):
        """Validate that required MongoDB Atlas environment variables are set."""
        required_vars = [
            "MONGODB_ATLAS_HOST",
            "MONGODB_ATLAS_USERNAME",
            "MONGODB_ATLAS_PASSWORD",
            "MONGODB_ATLAS_DEFAULT_AUTH_DB",
        ]

        missing_vars = []
        env_config = {}

        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            else:
                env_config[var] = value

        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            self.error(error_msg)
            raise ValueError(error_msg)

        return env_config

    def _create_mongo_client(self, atlas_config):
        """Create MongoDB client using Atlas credentials."""
        connection_string = (
            f"mongodb+srv://{atlas_config['MONGODB_ATLAS_USERNAME']}:"
            f"{atlas_config['MONGODB_ATLAS_PASSWORD']}@"
            f"{atlas_config['MONGODB_ATLAS_HOST']}/"
            f"?retryWrites=true&w=majority"
        )

        return MongoClient(connection_string)

    def _get_sample_data(self):
        """Get the actual sample data used by nox -s dev -- mongodb."""
        # Convert UUID objects to BSON Binary for MongoDB compatibility
        converted_data = {}

        for collection_name, documents in mongo_sample_data.items():
            converted_documents = []
            for doc in documents:
                converted_doc = self._convert_uuids_to_binary(doc)
                converted_documents.append(converted_doc)
            converted_data[collection_name] = converted_documents

        return converted_data

    def _convert_uuids_to_binary(self, obj):
        """Recursively convert UUID objects to BSON Binary."""
        if isinstance(obj, UUID):
            return Binary.from_uuid(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_uuids_to_binary(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_uuids_to_binary(item) for item in obj]
        else:
            return obj

    def _seed_sample_data(self, client, database_name, sample_data):
        """Seed sample data into MongoDB collections.

        IMPORTANT: The database_name here must match the dataset name used in the
        dataset configuration, because MongoDB connector uses dataset name as database name.
        """
        database = client[database_name]
        inserted_counts = {}

        for collection_name, documents in sample_data.items():
            collection = database[collection_name]

            # Insert documents
            if documents:  # Only insert if there are documents
                result = collection.insert_many(documents)
                inserted_counts[collection_name] = len(result.inserted_ids)
                self.info(f"  Inserted {len(result.inserted_ids)} documents into '{collection_name}'")
            else:
                inserted_counts[collection_name] = 0
                self.info(f"  No documents to insert for collection '{collection_name}'")

        return inserted_counts

    def _create_postgres_system(self):
        """Create PostgreSQL system (needed for graph references)."""
        postgres_system = {
            "fides_key": self.postgres_system_name,
            "organization_fides_key": "default_organization",
            "name": "QA PostgreSQL System (for MongoDB Atlas QA)",
            "description": "Test PostgreSQL system to support MongoDB Atlas graph references",
            "system_type": "Database",
            "privacy_declarations": [],
            "system_dependencies": []
        }

        try:
            response = self.api.create_system(postgres_system)
            self.success(f"PostgreSQL system '{self.postgres_system_name}' created")
            return response
        except Exception as e:
            self.error(f"Failed to create PostgreSQL system: {e}")
            raise

    def _create_postgres_dataset(self):
        """Create PostgreSQL dataset using actual YAML configuration."""
        postgres_dataset, _ = create_qa_datasets(self.postgres_dataset_key, self.mongo_dataset_key)
        postgres_dataset["organization_fides_key"] = "default_organization"

        try:
            response = self.api.create_dataset(postgres_dataset)
            self.success(f"PostgreSQL dataset '{self.postgres_dataset_key}' created")
            return response
        except Exception as e:
            self.error(f"Failed to create PostgreSQL dataset: {e}")
            raise

    def _create_postgres_connection(self):
        """Create PostgreSQL connection (needed for graph references)."""
        postgres_connection = {
            "name": "QA PostgreSQL Connection (for MongoDB Atlas QA)",
            "key": self.postgres_connection_key,
            "connection_type": "postgres",
            "access": "write",
            "description": "Test PostgreSQL connection to support MongoDB Atlas graph references",
            "secrets": {
                "host": "host.docker.internal",
                "port": 6432,
                "dbname": "postgres_example",
                "username": "postgres",
                "password": "postgres"
            }
        }

        try:
            response = self.api.create_system_connection(self.postgres_system_name, postgres_connection)
            self.success(f"PostgreSQL connection '{self.postgres_connection_key}' created and linked to system")
            return response
        except Exception as e:
            self.error(f"Failed to create PostgreSQL connection: {e}")
            raise

    def _create_system(self):
        """Create MongoDB Atlas system."""
        system_data = {
            "fides_key": self.system_name,
            "organization_fides_key": "default_organization",
            "name": "MongoDB Atlas QA",
            "description": f"QA MongoDB Atlas system with sample data (Database: {self.unique_db_name})",
            "system_type": "Database",
            "privacy_declarations": [],
            "system_dependencies": []
        }

        try:
            response = self.api.create_system(system_data)
            self.success(f"System '{self.system_name}' created")
            return response
        except Exception as e:
            self.error(f"Failed to create system: {e}")
            raise

    def _create_mongo_dataset(self):
        """Create MongoDB dataset using actual YAML configuration."""
        _, mongo_dataset = create_qa_datasets(self.postgres_dataset_key, self.mongo_dataset_key)
        mongo_dataset["organization_fides_key"] = "default_organization"

        try:
            response = self.api.create_dataset(mongo_dataset)
            self.success(f"MongoDB dataset '{self.mongo_dataset_key}' created")
            return response
        except Exception as e:
            self.error(f"Failed to create MongoDB dataset: {e}")
            raise

    def _create_connection(self):
        """Create MongoDB Atlas connection."""
        connection_data = {
            "name": "MongoDB Atlas QA Connection",
            "key": self.connection_key,
            "connection_type": "mongodb",
            "access": "write",
            "description": f"QA MongoDB Atlas connection (Database: {self.unique_db_name})",
            "secrets": {
                "host": os.getenv("MONGODB_ATLAS_HOST"),
                "username": os.getenv("MONGODB_ATLAS_USERNAME"),
                "password": os.getenv("MONGODB_ATLAS_PASSWORD"),
                "defaultauthdb": os.getenv("MONGODB_ATLAS_DEFAULT_AUTH_DB"),
                "use_srv": True,
                "ssl_enabled": True,
            }
        }

        try:
            response = self.api.create_system_connection(self.system_name, connection_data)
            self.success(f"Connection '{self.connection_key}' created and linked to system")
            return response
        except Exception as e:
            self.error(f"Failed to create connection: {e}")
            raise

    def _link_datasets_to_connections(self):
        """Link datasets to their respective connections."""
        try:
            # Link MongoDB dataset to MongoDB connection
            self.api.link_datasets_to_connection(self.connection_key, [self.mongo_dataset_key])
            self.success(f"MongoDB dataset '{self.mongo_dataset_key}' linked to connection '{self.connection_key}'")

            # Link PostgreSQL dataset to PostgreSQL connection
            self.api.link_datasets_to_connection(self.postgres_connection_key, [self.postgres_dataset_key])
            self.success(f"PostgreSQL dataset '{self.postgres_dataset_key}' linked to connection '{self.postgres_connection_key}'")

        except Exception as e:
            self.warning(f"Failed to link datasets to connections: {e}")

    def setup(self) -> bool:
        """Setup MongoDB Atlas integration with sample data seeding."""
        self.setup_phase()

        unique_suffix = self._create_unique_suffix()
        self.unique_db_name = f"mongo_qa_{unique_suffix}"
        print(f"Setting up MongoDB Atlas integration using actual YAML datasets and sample data (MongoDB Atlas Database: {self.unique_db_name})")

        try:
            # Step 1: Validate environment variables
            self.step(1, "Validating MongoDB Atlas environment variables")
            atlas_config = self._validate_environment_variables()
            self.success("All required environment variables are present")

            # Step 2: Create MongoDB client and test connection
            self.step(2, "Creating MongoDB client and testing connection")
            self.mongo_client = self._create_mongo_client(atlas_config)
            # Test connection by listing databases
            self.mongo_client.list_database_names()
            self.success("MongoDB Atlas connection successful")

            # Step 3: Seed sample data using the actual mongo_sample.py data
            self.mongo_dataset_key = self.unique_db_name
            self.step(3, f"Seeding sample data from mongo_sample.py into database: {self.unique_db_name}")
            sample_data = self._get_sample_data()
            inserted_counts = self._seed_sample_data(self.mongo_client, self.unique_db_name, sample_data)

            total_documents = sum(inserted_counts.values())
            self.success(f"Successfully seeded {total_documents} total documents across {len(inserted_counts)} collections")

            # Step 4: Create PostgreSQL system (needed for graph references)
            self.step(4, "Creating PostgreSQL system")
            self._create_postgres_system()

            # Step 5: Create PostgreSQL dataset using YAML configuration
            self.step(5, "Creating PostgreSQL dataset from YAML")
            self._create_postgres_dataset()

            # Step 6: Create PostgreSQL connection
            self.step(6, "Creating PostgreSQL connection")
            self._create_postgres_connection()

            # Step 7: Create MongoDB Atlas system
            self.step(7, "Creating MongoDB Atlas system")
            self._create_system()

            # Step 8: Create MongoDB dataset using YAML configuration (with proper graph references)
            self.step(8, "Creating MongoDB dataset from YAML")
            self._create_mongo_dataset()

            # Step 9: Create MongoDB connection
            self.step(9, "Creating MongoDB connection")
            self._create_connection()

            # Step 10: Link datasets to connections
            self.step(10, "Linking datasets to connections")
            self._link_datasets_to_connections()

            self.success("✅ MongoDB Atlas QA scenario setup completed successfully!")
            self.info(f"Database: {self.unique_db_name}")
            self.info(f"System: {self.system_name}")
            self.info(f"Connection: {self.connection_key}")
            self.info(f"MongoDB Dataset: {self.mongo_dataset_key}")
            self.info(f"PostgreSQL Dataset: {self.postgres_dataset_key}")
            self.info(f"Lock file: ~/.fides_mongodb_atlas_qa.lock (preserves unique suffix for teardown)")
            self.info(f"You can now run access and erasure requests for jane@example.com")

            return True

        except Exception as e:
            self.error(f"Setup failed: {e}")
            return False
        finally:
            if self.mongo_client:
                self.mongo_client.close()

    def teardown(self) -> bool:
        """Clean up MongoDB Atlas resources."""
        self.cleanup_phase()

        unique_suffix = self._get_unique_suffix()

        print(f"Cleaning up MongoDB Atlas QA resources")

        success = True

        try:
            # Step 1: Create client for cleanup
            self.step(1, "Creating MongoDB client for cleanup")
            atlas_config = self._validate_environment_variables()
            self.mongo_client = self._create_mongo_client(atlas_config)

            # Step 2: Delete MongoDB database
            self.step(2, f"Dropping MongoDB database")
            try:
                if unique_suffix:
                    unique_db_name = f"mongo_qa_{unique_suffix}"
                    self.mongo_client.drop_database(unique_db_name)
                    self.success(f"Successfully dropped database: {unique_db_name}")
                else:
                    self.warning(" No unique suffix found, skipping database cleanup")
            except Exception as e:
                self.warning(f"Failed to drop database {unique_db_name}: {e}")
                success = False

            # Step 3: Delete connections
            self.step(3, "Deleting connections")
            try:
                self.api.delete_connection(self.connection_key)
                self.success(f"MongoDB connection '{self.connection_key}' deleted")
            except Exception as e:
                self.warning(f"Failed to delete MongoDB connection: {e}")
                success = False

            try:
                self.api.delete_connection(self.postgres_connection_key)
                self.success(
                    f"PostgreSQL connection '{self.postgres_connection_key}' deleted"
                )
            except Exception as e:
                self.warning(f"Failed to delete PostgreSQL connection: {e}")
                success = False

            # Step 4: Delete datasets
            self.step(4, "Deleting datasets")
            try:
                if unique_suffix:
                    unique_mongo_dataset_key = f"mongo_qa_{unique_suffix}"
                    self.api.delete_dataset(unique_mongo_dataset_key)
                    self.success(f"MongoDB dataset '{unique_mongo_dataset_key}' deleted")
                else:
                    self.warning(" No unique suffix found, skipping MongoDB dataset cleanup")
            except Exception as e:
                self.warning(f"Failed to delete MongoDB dataset: {e}")
                success = False

            try:
                self.api.delete_dataset(self.postgres_dataset_key)
                self.success(
                    f"PostgreSQL dataset '{self.postgres_dataset_key}' deleted"
                )
            except Exception as e:
                self.warning(f"Failed to delete PostgreSQL dataset: {e}")
                success = False

            # Step 5: Delete systems
            self.step(5, "Deleting systems")
            try:
                self.api.delete_system(self.system_name)
                self.success(f"MongoDB system '{self.system_name}' deleted")
            except Exception as e:
                self.warning(f"Failed to delete MongoDB system: {e}")
                success = False

            try:
                self.api.delete_system(self.postgres_system_name)
                self.success(
                    f"PostgreSQL system '{self.postgres_system_name}' deleted"
                )
            except Exception as e:
                self.warning(f"Failed to delete PostgreSQL system: {e}")
                success = False

            if success:
                self.success("✅ All MongoDB Atlas QA resources cleaned up successfully!")
                # Remove lock file after successful cleanup
                self._remove_lock_file()
            else:
                self.warning("⚠️ Some cleanup operations failed - manual cleanup may be required")
                self.warning("Lock file preserved for potential retry")

            return success

        except Exception as e:
            self.error(f"Teardown failed: {e}")
            return False
        finally:
            if self.mongo_client:
                self.mongo_client.close()

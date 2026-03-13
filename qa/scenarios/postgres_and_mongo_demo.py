#!/usr/bin/env python3
"""
QA scenario that sets up Postgres and MongoDB connections using the local demo databases.

Requires the demo databases to be running (via nox -s dev -- postgres mongodb).
- Postgres: host.docker.internal:6432 (postgres_example)
- MongoDB: host.docker.internal:27017 (mongo_test)

Reuses the existing mongo_test dataset (created by fides sample data loading) and creates
a separate QA Postgres dataset. This avoids colliding with or deleting the demo dataset.
"""

import copy
import sys
from pathlib import Path

import yaml

sys.path.append(str(Path(__file__).parent.parent))
from utils import QATestScenario

FIDES_ROOT = Path(__file__).parent.parent.parent


def _load_dataset_yaml(filename: str) -> dict:
    path = (
        FIDES_ROOT
        / "src"
        / "fides"
        / "data"
        / "sample_project"
        / "sample_resources"
        / filename
    )
    with open(path) as f:
        return yaml.safe_load(f)["dataset"][0]


class PostgresAndMongoDemo(QATestScenario):
    """
    Sets up Postgres + MongoDB connections against the local demo databases
    so you can submit privacy requests and observe the execution graph.

    Reuses the existing ``mongo_test`` dataset (loaded by sample data) and
    creates a QA-prefixed Postgres dataset to avoid conflicts.
    """

    POSTGRES_SYSTEM = "qa_demo_postgres_system"
    MONGO_SYSTEM = "qa_demo_mongo_system"
    POSTGRES_CONNECTION = "qa_demo_postgres_connection"
    MONGO_CONNECTION = "qa_demo_mongo_connection"
    POSTGRES_DATASET = "qa_demo_postgres_dataset"
    MONGO_DATASET = "mongo_test"

    @property
    def description(self) -> str:
        return (
            "Sets up Postgres + MongoDB connections against local demo databases. "
            "Reuses the existing mongo_test dataset. Submit a privacy request for "
            "jane@example.com to see the execution graph."
        )

    def setup(self) -> bool:
        self.setup_phase()

        try:
            self.step(1, "Creating PostgreSQL system")
            self.api.create_system(
                {
                    "fides_key": self.POSTGRES_SYSTEM,
                    "organization_fides_key": "default_organization",
                    "name": "QA Demo PostgreSQL System",
                    "description": "Local demo Postgres for execution graph QA",
                    "system_type": "Database",
                    "privacy_declarations": [],
                }
            )
            self.success(f"System '{self.POSTGRES_SYSTEM}' created")

            self.step(2, "Creating MongoDB system")
            self.api.create_system(
                {
                    "fides_key": self.MONGO_SYSTEM,
                    "organization_fides_key": "default_organization",
                    "name": "QA Demo MongoDB System",
                    "description": "Local demo MongoDB for execution graph QA",
                    "system_type": "Database",
                    "privacy_declarations": [],
                }
            )
            self.success(f"System '{self.MONGO_SYSTEM}' created")

            self.step(3, "Creating PostgreSQL dataset from YAML")
            pg_dataset = _load_dataset_yaml("postgres_example_test_dataset.yml")
            pg_dataset["fides_key"] = self.POSTGRES_DATASET
            pg_dataset["name"] = "QA Demo " + pg_dataset["name"]
            self._replace_dataset_refs(pg_dataset)
            pg_dataset["organization_fides_key"] = "default_organization"
            self.api.create_dataset(pg_dataset)
            self.success(f"Dataset '{self.POSTGRES_DATASET}' created")

            self.step(4, "Ensuring MongoDB dataset exists")
            existing = self.api.get_dataset(self.MONGO_DATASET)
            if existing:
                self.success(f"Dataset '{self.MONGO_DATASET}' already exists (reusing)")
            else:
                mongo_dataset = _load_dataset_yaml("mongo_example_test_dataset.yml")
                self._replace_dataset_refs(mongo_dataset)
                mongo_dataset["organization_fides_key"] = "default_organization"
                self.api.create_dataset(mongo_dataset)
                self.success(f"Dataset '{self.MONGO_DATASET}' created")

            self.step(5, "Creating PostgreSQL connection")
            self.api.create_system_connection(
                self.POSTGRES_SYSTEM,
                {
                    "name": "QA Demo PostgreSQL Connection",
                    "key": self.POSTGRES_CONNECTION,
                    "connection_type": "postgres",
                    "access": "write",
                    "secrets": {
                        "host": "host.docker.internal",
                        "port": 6432,
                        "dbname": "postgres_example",
                        "username": "postgres",
                        "password": "postgres",
                    },
                },
            )
            self.success(f"Connection '{self.POSTGRES_CONNECTION}' created")

            self.step(6, "Creating MongoDB connection")
            self.api.create_system_connection(
                self.MONGO_SYSTEM,
                {
                    "name": "QA Demo MongoDB Connection",
                    "key": self.MONGO_CONNECTION,
                    "connection_type": "mongodb",
                    "access": "write",
                    "secrets": {
                        "host": "host.docker.internal",
                        "port": 27017,
                        "defaultauthdb": "mongo_test",
                        "username": "mongo_user",
                        "password": "mongo_pass",
                    },
                },
            )
            self.success(f"Connection '{self.MONGO_CONNECTION}' created")

            self.step(7, "Linking datasets to connections")
            self.api.link_datasets_to_connection(
                self.POSTGRES_CONNECTION, [self.POSTGRES_DATASET]
            )
            self.success(
                f"'{self.POSTGRES_DATASET}' linked to '{self.POSTGRES_CONNECTION}'"
            )
            self.api.link_datasets_to_connection(
                self.MONGO_CONNECTION, [self.MONGO_DATASET]
            )
            self.success(f"'{self.MONGO_DATASET}' linked to '{self.MONGO_CONNECTION}'")

            self.final_success("Setup complete!")
            self.info(
                "Submit an access request for jane@example.com to see the execution graph."
            )
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        self.cleanup_phase()
        success = True

        self.step(1, "Deleting connections")
        for key in (self.POSTGRES_CONNECTION, self.MONGO_CONNECTION):
            if self.api.delete_connection(key):
                self.success(f"Deleted connection '{key}'")
            else:
                self.already_cleaned("Connection", key)

        self.step(2, "Deleting systems")
        for key in (self.POSTGRES_SYSTEM, self.MONGO_SYSTEM):
            if self.api.delete_system(key):
                self.success(f"Deleted system '{key}'")
            else:
                self.already_cleaned("System", key)

        self.step(3, "Deleting QA datasets (preserving mongo_test)")
        if self.api.delete_dataset(self.POSTGRES_DATASET):
            self.success(f"Deleted dataset '{self.POSTGRES_DATASET}'")
        else:
            self.already_cleaned("Dataset", self.POSTGRES_DATASET)
        self.info(
            f"Skipping '{self.MONGO_DATASET}' (shared with demo, not owned by QA)"
        )

        if success:
            self.final_success("Cleanup complete!")
        return success

    def _replace_dataset_refs(self, obj: object) -> None:
        """Replace original dataset fides_keys with QA-prefixed keys."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "dataset":
                    if value == "postgres_example_test_dataset":
                        obj[key] = self.POSTGRES_DATASET
                    elif value == "mongo_test":
                        obj[key] = self.MONGO_DATASET
                else:
                    self._replace_dataset_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                self._replace_dataset_refs(item)

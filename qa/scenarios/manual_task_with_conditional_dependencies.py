#!/usr/bin/env python3
"""
QA scenario for testing ManualTask and ManualTaskConditionalDependencies with postgres-example database.
"""
# Enable DSR 3.0 execution BEFORE any other imports
from fides.config import CONFIG
CONFIG.execution.use_dsr_3_0 = True
print(f"🔧 DSR 3.0 enabled at startup: {CONFIG.execution.use_dsr_3_0}")

import sys
import argparse
import yaml
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session, sessionmaker
from uuid import uuid4

# Add project root and qa directory to path for imports
project_root = Path(__file__).parent.parent.parent
qa_dir = project_root / "qa"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(qa_dir) not in sys.path:
    sys.path.insert(0, str(qa_dir))


from utils import QATestScenario, Argument

from fides.api.db.ctl_session import sync_engine
from fides.api.db.base import *
from fides.api.db.database import seed_db
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConditionalDependency,
    ManualTaskConditionalDependencyType,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskParentEntityType,
    ManualTaskType,
    ManualTaskExecutionTiming,
)
from fides.api.models.policy import Policy, Rule, RuleTarget, ActionType
from fides.api.models.storage import StorageConfig
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.models.datasetconfig import DatasetConfig
from fideslang.models import Dataset as FideslangDataset
from fides.api.task.manual.manual_task_utils import get_manual_task_addresses, get_connection_configs_with_manual_tasks

# Set up the manual test with python qa manual_task_with_conditional_dependencies setup
# Teardown with python python qa manual_task_with_conditional_dependencies teardown

POSTGRES_DATASET_KEY = "postgres_example_test_dataset"
POSTGRES_HOST = "postgres_example"
POSTGRES_PORT = 5432
POSTGRES_DBNAME = "postgres_example"
POSTGRES_USERNAME = "postgres"
POSTGRES_PASSWORD = "postgres"

DATA_CATEGORIES = [
    "user.contact.email",
    "user.name",
    "user.unique_id",
    "user.contact.address.city",
    "user.contact.address.street",
    "user.contact.address.state",
    "user.contact.address.postal_code"
]

FIELDS_DATA = [
    {
        "field_key": "customer_verification",
        "field_type": ManualTaskFieldType.checkbox,
        "field_metadata": {
            "label": "Customer Verification Required",
            "required": True,
            "help_text": "Check if customer identity needs verification"
        }
    },
    {
        "field_key": "data_scope",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Data Scope Description",
            "required": False,
            "help_text": "Describe the scope of data to be processed"
        }
    },
    {
        "field_key": "approval_notes",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Approval Notes",
            "required": False,
            "help_text": "Additional notes for approval process"
        }
    }
]

DEPENDENCIES_DATA = [
    # Root group condition (AND)
    {
        "parent_id": None,
        "condition_type": ManualTaskConditionalDependencyType.group,
        "logical_operator": "and",
        "sort_order": 0
    },
    # Customer name exists condition (leaf) - references postgres dataset field
    {
        "parent_id": None,  # Will be updated after root group is created
        "condition_type": ManualTaskConditionalDependencyType.leaf,
        "field_address": f"{POSTGRES_DATASET_KEY}:customer:name",
        "operator": "exists",
        "value": None,  # exists operator doesn't need a value
        "sort_order": 1
    },
    # Customer email contains specific value condition (leaf) - references postgres dataset field
    {
        "parent_id": None,  # Will be updated after root group is created
        "condition_type": ManualTaskConditionalDependencyType.leaf,
        "field_address": f"{POSTGRES_DATASET_KEY}:customer:email",
        "operator": "starts_with",
        "value": "customer-1",
        "sort_order": 2
    },
    # Nested group condition (OR)
    {
        "parent_id": None,  # Will be updated after root group is created
        "condition_type": ManualTaskConditionalDependencyType.group,
        "logical_operator": "or",
        "sort_order": 3
    },
    # Customer ID condition (leaf) - references postgres dataset field
    {
        "parent_id": None,  # Will be updated after nested group is created
        "condition_type": ManualTaskConditionalDependencyType.leaf,
        "field_address": f"{POSTGRES_DATASET_KEY}:customer:id",
        "operator": "gt",
        "value": 0,
        "sort_order": 4
    },
    # Customer address city starts with Example condition (leaf) - references postgres dataset field
    {
        "parent_id": None,  # Will be updated after nested group is created
        "condition_type": ManualTaskConditionalDependencyType.leaf,
        "field_address": f"{POSTGRES_DATASET_KEY}:address:city",
        "operator": "starts_with",
        "value": "Example",
        "sort_order": 5
    }
]


def create_dependencies_data(manual_task_id: str) -> list[dict]:
    return [
        {
            "manual_task_id": manual_task_id,
            **dependency_data,
        }
        for dependency_data in DEPENDENCIES_DATA
    ]


def create_fields_data(manual_task_id: str, manual_task_config_id: str) -> list[dict]:
    return [
        {
            "task_id": manual_task_id,
            "config_id": manual_task_config_id,
            **field_data,
        }
        for field_data in FIELDS_DATA
    ]

# Initialize database
SessionLocal = sessionmaker(bind=sync_engine)
with SessionLocal() as db:
    seed_db(db)


class ManualTaskWithConditionalDependencies(QATestScenario):
    """QA scenario for testing ManualTask and ManualTaskConditionalDependencies with a ManualTask connection."""

    arguments = {
        'connection_key': Argument(
            type=str,
            default="manual_task_connection",
            description="Connection key for the ManualTask connection"
        ),
        'postgres_connection_key': Argument(
            type=str,
            default="postgres_example_connection",
            description="Connection key for the postgres-example connection"
        )
    }

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.connection_key = kwargs.get('connection_key', 'manual_task_connection')
        self.postgres_connection_key = kwargs.get('postgres_connection_key', 'postgres_example_connection')
        self.manual_task = None
        self.manual_task_config = None
        self.manual_task_fields = []
        self.conditional_dependencies = []
        self.connection_config_id = None
        self.postgres_connection_config_id = None
        self.storage_config = None
        self.policy = None
        self.access_rule = None
        self.privacy_requests = [] # Added to store privacy requests for cleanup

    @property
    def description(self) -> str:
        return "Creates a ManualTask with ManualTaskConditionalDependencies and tests both scenarios: one privacy request where conditions are met (manual task created) and one where conditions are not met (no manual task created)."

    def setup(self) -> bool:
        """Setup ManualTask with conditional dependencies."""
        self.setup_phase()

        print(f"Setting up ManualTask with conditional dependencies for connection: {self.connection_key}")

        try:

            # Step 1: Create or verify postgres connection exists
            self.step(1, "Creating/verifying postgres connection")
            if not self._create_or_verify_postgres_connection():
                self.error(f"Failed to create/verify postgres connection {self.postgres_connection_key}")
                return False

            # Step 2: Create or verify postgres database exists and seed it
            self.step(2, "Creating/verifying postgres database and seeding data")
            if not self._create_or_verify_postgres_database():
                self.error(f"Failed to create/verify postgres database {POSTGRES_DBNAME}")
                return False

            # Step 3: Create or verify dataset config exists
            self.step(3, "Creating/verifying dataset config")
            if not self._create_or_verify_dataset_config():
                self.error(f"Failed to create/verify dataset config {POSTGRES_DATASET_KEY}")
                return False

            # Step 4: Create or verify ManualTask connection exists
            self.step(4, "Creating/verifying ManualTask connection")
            if not self._create_or_verify_manual_task_connection():
                self.error(f"Failed to create/verify connection {self.connection_key}")
                return False

            # Step 5: Create ManualTask
            self.step(5, "Creating ManualTask")
            if not self._create_manual_task():
                self.error("Failed to create ManualTask")
                return False

            # Step 6: Create ManualTaskConfig
            self.step(6, "Creating ManualTaskConfig")
            if not self._create_manual_task_config():
                self.error("Failed to create ManualTaskConfig")
                return False

            # Step 7: Create ManualTaskConfigFields
            self.step(7, "Creating ManualTaskConfigFields")
            if not self._create_manual_task_config_fields():
                self.error("Failed to create ManualTaskConfigFields")
                return False

            # Step 8: Create ManualTaskConditionalDependencies
            self.step(8, "Creating ManualTaskConditionalDependencies")
            if not self._create_conditional_dependencies():
                self.error("Failed to create ManualTaskConditionalDependencies")
                return False

            # Step 9: Create Policy
            self.step(9, "Creating Policy")
            if not self._create_policy():
                self.error("Failed to create Policy")
                return False

            # Step 10: Create Privacy Requests
            self.step(10, "Creating Privacy Requests")
            if not self._create_privacy_request():
                self.error("Failed to create Privacy Requests")
                return False

            # Step 11: Debug - Check manual task integration
            self.step(11, "Debug - Checking manual task integration")
            self._debug_manual_task_integration()

            self.final_success("Setup completed successfully!")
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up resources created by this scenario."""
        self.cleanup_phase()

        print(f"Cleaning up ManualTask test resources...")
        deleted_counts = {'manual_tasks': 0, 'conditional_dependencies': 0, 'manual_task_connections': 0, 'storage_configs': 0, 'policies': 0, 'rules': 0, 'privacy_requests': 0}

        try:
            # Step 1: Delete ManualTask (this will cascade delete related records)
            self.step(1, "Deleting ManualTask")
            if self.manual_task and self._delete_manual_task():
                deleted_counts["manual_tasks"] += 1
                self.success(f"Deleted ManualTask: {self.manual_task.id}")
            else:
                self.already_cleaned("ManualTask", self.manual_task.id if self.manual_task else "unknown")

            # Step 2: Clean up any remaining conditional dependencies
            self.step(2, "Cleaning up conditional dependencies")
            for dep in self.conditional_dependencies:
                if self._delete_conditional_dependency(dep):
                    deleted_counts["conditional_dependencies"] += 1
                    self.success(f"Deleted conditional dependency: {dep.id}")

            # Step 3: Delete manual task connection config (only the manual task connection, not postgres)
            self.step(3, "Deleting manual task connection config")
            if self.connection_key and self._delete_connection_config(self.connection_key):
                deleted_counts["manual_task_connections"] += 1
                self.success(f"Deleted manual task connection config: {self.connection_key}")
            else:
                self.already_cleaned("ConnectionConfig", self.connection_key)

            # Step 4: Delete storage config (created for testing)
            self.step(4, "Deleting storage config")
            if self._delete_storage_config():
                deleted_counts["storage_configs"] += 1
                self.success("Deleted storage config")
            else:
                self.already_cleaned("StorageConfig", "storage config")

            # Step 5: Delete rule (created for testing)
            self.step(5, "Deleting rule")
            if self._delete_rule():
                deleted_counts["rules"] += 1
                self.success("Deleted rule")
            else:
                self.already_cleaned("Rule", "rule")

            # Step 6: Delete policy (created for testing)
            self.step(6, "Deleting policy")
            if self._delete_policy():
                deleted_counts["policies"] += 1
                self.success("Deleted policy")
            else:
                self.already_cleaned("Policy", "policy")

            # Step 7: Delete privacy requests (created for testing)
            self.step(7, "Deleting privacy requests")
            if hasattr(self, 'privacy_requests') and self.privacy_requests:
                for privacy_request in self.privacy_requests:
                    if self._delete_privacy_request(privacy_request):
                        deleted_counts["privacy_requests"] += 1
                        self.success(f"Deleted privacy request: {privacy_request.id}")
            else:
                self.already_cleaned("PrivacyRequest", "privacy requests")

            # Note: We intentionally do NOT delete:
            # - postgres_example_connection (shared resource)
            # - postgres_example_test_dataset config (shared resource)
            # - CTL dataset (shared resource)
            # - postgres_example database (keeping test data for other runs)
            # These are used by other tests and should persist

            self.summary("Cleanup Summary", deleted_counts)
            self.final_success("Cleanup completed successfully!")
            return True

        except Exception as e:
            self.final_error(f"Cleanup failed: {e}")
            return False

    def _get_db_session(self) -> Session:
        SessionLocal = sessionmaker(bind=sync_engine)
        with SessionLocal() as db:
            return db

    def _create_or_verify_postgres_connection(self) -> bool:
        """Create or verify that the postgres-example connection exists."""
        try:
            db = self._get_db_session()
            # First check if connection already exists
            connection = db.query(ConnectionConfig).filter_by(key=self.postgres_connection_key).first()
            if connection:
                self.success(f"Found existing connection: {self.postgres_connection_key}")
                self.postgres_connection_config_id = connection.id
                return True

            # Connection doesn't exist, create it
            self.info(f"Connection {self.postgres_connection_key} not found, creating it...")

            connection_data = {
                "name": "Postgres Example Connection",
                "key": self.postgres_connection_key,
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.write,
                "secrets": {
                    "host": POSTGRES_HOST,  # Docker service name
                    "port": POSTGRES_PORT,  # Internal Docker port
                    "dbname": POSTGRES_DBNAME,
                    "username": POSTGRES_USERNAME,
                    "password": POSTGRES_PASSWORD,
                },
                "disabled": False,
                "description": "Postgres example database for testing"
            }

            # Create connection first
            connection = ConnectionConfig.create(db=db, data=connection_data)
            self.postgres_connection_config_id = connection.id

            self.success(f"Created postgres connection config: {self.postgres_connection_key}")
            return True

        except Exception as e:
            self.error(f"Error creating/verifying postgres connection: {e}")
            return False

    def _create_or_verify_postgres_database(self) -> bool:
        """Create and seed the postgres_example database using the existing setup script."""
        try:
            import subprocess
            import os

            # Path to the postgres setup script
            setup_script_path = "tests/ops/integration_tests/setup_scripts/postgres_setup.py"

            if not os.path.exists(setup_script_path):
                self.error(f"Postgres setup script not found at: {setup_script_path}")
                return False

            self.info("Running postgres setup script...")

            # Run the setup script
            result = subprocess.run(
                [sys.executable, setup_script_path],
                capture_output=True,
                text=True,
                cwd=project_root
            )

            if result.returncode == 0:
                self.success("Postgres setup script completed successfully")
                return True
            else:
                self.error(f"Postgres setup script failed with return code {result.returncode}")
                self.error(f"stdout: {result.stdout}")
                self.error(f"stderr: {result.stderr}")
                return False

        except Exception as e:
            self.error(f"Error running postgres setup script: {e}")
            return False

    def _create_or_verify_dataset_config(self) -> bool:
        """Create or verify that the dataset configuration exists for the postgres connection."""
        try:
            db = self._get_db_session()

            # First check if dataset config already exists
            existing_config = db.query(DatasetConfig).filter_by(
                connection_config_id=self.postgres_connection_config_id,
                fides_key=POSTGRES_DATASET_KEY
            ).first()

            if existing_config:
                self.success(f"Found existing dataset config: {POSTGRES_DATASET_KEY}")
                return True

            # Dataset config doesn't exist, create it
            self.info(f"Dataset config {POSTGRES_DATASET_KEY} not found, creating it...")

            # Load the dataset from the YAML file
            import os

            dataset_yaml_path = "data/dataset/postgres_example_test_dataset.yml"
            if not os.path.exists(dataset_yaml_path):
                self.error(f"Dataset YAML file not found: {dataset_yaml_path}")
                return False

            with open(dataset_yaml_path, "r") as file:
                dataset_data = yaml.safe_load(file).get("dataset", [])[0]

                        # Check if CTL dataset already exists
            from fides.api.models.sql_models import Dataset as CtlDataset
            existing_ctl_dataset = db.query(CtlDataset).filter_by(fides_key=POSTGRES_DATASET_KEY).first()

            if existing_ctl_dataset:
                self.info(f"Found existing CTL dataset: {POSTGRES_DATASET_KEY}")
                # Update the existing CTL dataset with the complete dataset data
                self.info(f"Updating existing CTL dataset with complete field definitions")
                # Use the update method to update the existing CTL dataset
                validated_dataset = FideslangDataset(**dataset_data)
                data_dict = validated_dataset.model_dump(mode="json")
                existing_ctl_dataset.update(db, data=data_dict)
                ctl_dataset = existing_ctl_dataset
            else:
                # Create CTL dataset if it doesn't exist
                self.info(f"Creating new CTL dataset: {POSTGRES_DATASET_KEY}")
                ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_data)

            # Create dataset config
            dataset_config_data = {
                "connection_config_id": self.postgres_connection_config_id,
                "fides_key": POSTGRES_DATASET_KEY,
                "ctl_dataset_id": ctl_dataset.id,
            }

            dataset_config = DatasetConfig.create(db=db, data=dataset_config_data)
            self.success(f"Created dataset config: {POSTGRES_DATASET_KEY}")
            return True

        except Exception as e:
            self.error(f"Error creating/verifying dataset config: {e}")
            return False

    def _create_or_verify_manual_task_connection(self) -> bool:
        """Create or verify that the ManualTask connection exists."""
        try:
            db = self._get_db_session()
            # First check if connection already exists
            connection = db.query(ConnectionConfig).filter_by(key=self.connection_key).first()
            if connection:
                self.success(f"Found existing connection: {self.connection_key}")
                self.connection_config_id = connection.id
                return True

            # Connection doesn't exist, create it
            self.info(f"Connection {self.connection_key} not found, creating it...")

            connection_data = {
                "name": "Manual Task Connection",
                "key": self.connection_key,
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
                "secrets": {},  # ManualTask connections don't need secrets
                "disabled": False,
                "description": "ManualTask connection for testing ManualTask and ManualTaskConditionalDependencies",
            }

            connection = ConnectionConfig.create(db=db, data=connection_data)
            self.connection_config_id = connection.id
            self.success(f"Created ManualTask connection config: {self.connection_key}")
            return True

        except Exception as e:
            self.error(f"Error creating/verifying connection: {e}")
            return False

    def _create_manual_task(self) -> bool:
        """Create a ManualTask for the ManualTask connection."""
        try:
            db = self._get_db_session()
            # First check if manual task already exists
            existing_task = db.query(ManualTask).filter(
                ManualTask.parent_entity_id == self.connection_config_id,
                ManualTask.parent_entity_type == ManualTaskParentEntityType.connection_config
            ).first()

            if existing_task:
                self.manual_task = existing_task
                self.success(f"Found existing ManualTask: {self.manual_task.id}")
                return True

            # Create new manual task if it doesn't exist
            manual_task_data = {
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": self.connection_config_id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config
            }

            self.manual_task = ManualTask.create(db=db, data=manual_task_data)
            self.success(f"Created new ManualTask: {self.manual_task.id}")
            return True

        except Exception as e:
            self.error(f"Error creating ManualTask: {e}")
            return False

    def _create_manual_task_config(self) -> bool:
        """Create a ManualTaskConfig for the ManualTask."""
        try:
            db = self._get_db_session()
            config_data = {
                "task_id": self.manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "version": 1,
                "is_current": True,
                "execution_timing": ManualTaskExecutionTiming.post_execution
            }

            self.manual_task_config = ManualTaskConfig.create(db=db, data=config_data)
            self.success(f"Created ManualTaskConfig: {self.manual_task_config.id}")
            return True

        except Exception as e:
            self.error(f"Error creating ManualTaskConfig: {e}")
            return False

    def _create_manual_task_config_fields(self) -> bool:
        """Create ManualTaskConfigFields for the config."""
        try:
            db = self._get_db_session()
            # Create fields based on ManualTask requirements
            fields_data = create_fields_data(self.manual_task.id, self.manual_task_config.id)
            for field_data in fields_data:
                field = ManualTaskConfigField.create(db=db, data=field_data)
                self.manual_task_fields.append(field)
                self.info(f"Created field: {field.field_key}")

            self.success(f"Created {len(self.manual_task_fields)} ManualTaskConfigFields")
            return True

        except Exception as e:
            self.error(f"Error creating ManualTaskConfigFields: {e}")
            return False

    def _create_conditional_dependencies(self) -> bool:
        """Create ManualTaskConditionalDependencies based on ManualTask fields."""
        try:
            db = self._get_db_session()

            dependencies_data = create_dependencies_data(self.manual_task.id)

            # Create dependencies in order and establish parent-child relationships
            root_group = None
            nested_group = None

            for i, dep_data in enumerate(dependencies_data):
                dep = ManualTaskConditionalDependency.create(db=db, data=dep_data)
                self.conditional_dependencies.append(dep)

                # Set up parent-child relationships
                if i == 0:  # Root group
                    root_group = dep
                    self.info(f"Created root group dependency: {dep.id}")
                elif i == 3:  # Nested group
                    nested_group = dep
                    # Update parent to root group
                    dep.parent_id = root_group.id
                    db.commit()
                    self.info(f"Created nested group dependency: {dep.id}")
                elif i in [1, 2]:  # Leaf conditions under root group
                    # Update parent to root group
                    dep.parent_id = root_group.id
                    db.commit()
                    self.info(f"Created leaf dependency under root: {dep.id}")
                elif i in [4, 5]:  # Leaf conditions under nested group
                    # Update parent to nested group
                    dep.parent_id = nested_group.id
                    db.commit()
                    self.info(f"Created leaf dependency under nested group: {dep.id}")

            self.success(f"Created {len(self.conditional_dependencies)} ManualTaskConditionalDependencies")
            return True

        except Exception as e:
            self.error(f"Error creating ManualTaskConditionalDependencies: {e}")
            return False

    def _create_policy(self) -> bool:
        """Create a policy for the privacy request."""
        try:
            db = self._get_db_session()
            # Create storage config for access rule
            storage_config = StorageConfig.create(
                db=db,
                data={
                    "name": f"Test Storage Config {str(uuid4())[:8]}",
                    "type": "local",
                    "details": {
                        "naming": "request_id",
                    },
                    "key": f"test_storage_config_{str(uuid4())[:8]}",
                    "format": "json",
                },
            )
            self.storage_config = storage_config

            # Create policy
            policy = Policy.create(
                db=db,
                data={
                    "name": f"Test Policy {str(uuid4())[:8]}",
                    "key": f"test_policy_{str(uuid4())[:8]}",
                },
            )
            self.policy = policy

            # Create access rule
            self.access_rule = Rule.create(
                db=db,
                data={
                    "action_type": ActionType.access.value,
                    "name": f"Access Rule {str(uuid4())[:8]}",
                    "key": f"access_rule_{str(uuid4())[:8]}",
                    "policy_id": policy.id,
                    "storage_destination_id": storage_config.id,
                },
            )

            # Create rule targets for all relevant data categories
            for category in DATA_CATEGORIES:
                RuleTarget.create(
                    db=db,
                    data={
                        "data_category": category,
                        "rule_id": self.access_rule.id,
                    },
                )

            self.success(f"Created policy: {policy.id}")
            return True

        except Exception as e:
            self.error(f"Error creating policy: {e}")
            return False

    def _create_privacy_request(self) -> bool:
        """Create two privacy requests - one where conditions are met and one where they aren't."""
        try:
            db = self._get_db_session()

            # Create first privacy request - conditions WILL be met
            # This email exists in the postgres example data and matches our conditional dependencies
            privacy_request_1 = PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"ext-conditions-met-{str(uuid4())}",
                    "started_processing_at": datetime.now(timezone.utc),
                    "requested_at": datetime.now(timezone.utc),
                    "status": "pending",
                    "origin": "https://example.com/",
                    "policy_id": self.policy.id,
                    "client_id": self.policy.client_id,
                },
            )

            # Cache identity for first request - this should trigger manual task creation
            identity_kwargs_1 = {"email": "customer-1@example.com"}
            privacy_request_1.cache_identity(identity_kwargs_1)
            privacy_request_1.persist_identity(
                db=db,
                identity={"email": "customer-1@example.com"},
            )

            self.success(f"Created privacy request (conditions met): {privacy_request_1.id}")

            # Create second privacy request - conditions will NOT be met
            # This email doesn't exist in the postgres example data, so manual task won't be created
            privacy_request_2 = PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"ext-conditions-not-met-{str(uuid4())}",
                    "started_processing_at": datetime.now(timezone.utc),
                    "requested_at": datetime.now(timezone.utc),
                    "status": "pending",
                    "origin": "https://example.com/",
                    "policy_id": self.policy.id,
                    "client_id": self.policy.client_id,
                },
            )

            # Cache identity for second request - this should NOT trigger manual task creation
            identity_kwargs_2 = {"email": "nonexistent@example.com"}
            privacy_request_2.cache_identity(identity_kwargs_2)
            privacy_request_2.persist_identity(
                db=db,
                identity={"email": "nonexistent@example.com"},
            )

            self.success(f"Created privacy request (conditions not met): {privacy_request_2.id}")

            # Store both privacy requests for cleanup
            self.privacy_requests = [privacy_request_1, privacy_request_2]

            return True

        except Exception as e:
            self.error(f"Error creating privacy requests: {e}")
            return False

    def _delete_manual_task(self) -> bool:
        """Delete the ManualTask."""
        try:
            db = self._get_db_session()
            if self.manual_task:
                db.delete(self.manual_task)
                db.commit()
                self.success(f"Deleted ManualTask: {self.manual_task.id}")
                return True
            return False
        except Exception as e:
            self.error(f"Error deleting ManualTask: {e}")
            return False

    def _delete_conditional_dependency(self, dep) -> bool:
        """Delete a conditional dependency."""
        try:
            db = self._get_db_session()
            db.delete(dep)
            db.commit()
            self.success(f"Deleted conditional dependency: {dep.id}")
            return True
        except Exception as e:
            self.error(f"Error deleting conditional dependency {dep.id}: {e}")
            return False

    def _delete_connection_config(self, connection_key: str) -> bool:
        """Delete a connection config."""
        try:
            db = self._get_db_session()
            connection = db.query(ConnectionConfig).filter_by(key=connection_key).first()
            if connection:
                db.delete(connection)
                db.commit()
                self.success(f"Deleted connection config: {connection_key}")
                return True
            else:
                self.warning(f"Connection config {connection_key} was already deleted")
                return True

        except Exception as e:
            self.error(f"Error deleting connection config: {e}")
            return False

    def _delete_dataset_config(self) -> bool:
        """Delete the dataset config and associated CTL dataset."""
        try:
            if not self.postgres_connection_config_id:
                return False

            db = self._get_db_session()

            # Delete dataset config
            dataset_config = db.query(DatasetConfig).filter_by(
                connection_config_id=self.postgres_connection_config_id,
                fides_key=POSTGRES_DATASET_KEY
            ).first()

            if dataset_config:
                db.delete(dataset_config)
                self.success(f"Deleted dataset config: {POSTGRES_DATASET_KEY}")
            else:
                self.warning(f"Dataset config {POSTGRES_DATASET_KEY} was already deleted")

            # Delete associated CTL dataset
            from fides.api.models.sql_models import Dataset as CtlDataset
            ctl_dataset = db.query(CtlDataset).filter_by(fides_key=POSTGRES_DATASET_KEY).first()

            if ctl_dataset:
                db.delete(ctl_dataset)
                self.success(f"Deleted CTL dataset: {POSTGRES_DATASET_KEY}")
            else:
                self.warning(f"CTL dataset {POSTGRES_DATASET_KEY} was already deleted")

            db.commit()
            return True

        except Exception as e:
            self.error(f"Error deleting dataset config: {e}")
            return False

    def _delete_storage_config(self) -> bool:
        """Delete the storage config."""
        try:
            if not self.storage_config:
                return False

            db = self._get_db_session()
            storage_config = db.query(StorageConfig).filter_by(id=self.storage_config.id).first()
            if storage_config:
                db.delete(storage_config)
                db.commit()
                self.success(f"Deleted storage config: {storage_config.key}")
                return True
            else:
                self.warning(f"Storage config was already deleted")
                return True
        except Exception as e:
            self.error(f"Error deleting storage config: {e}")
            return False

    def _delete_policy(self) -> bool:
        """Delete the policy."""
        try:
            if not self.policy:
                return False

            db = self._get_db_session()
            policy = db.query(Policy).filter_by(id=self.policy.id).first()
            if policy:
                db.delete(policy)
                db.commit()
                self.success(f"Deleted policy: {policy.key}")
                return True
            else:
                self.warning(f"Policy was already deleted")
                return True
        except Exception as e:
            self.error(f"Error deleting policy: {e}")
            return False

    def _delete_rule(self) -> bool:
        """Delete the access rule."""
        try:
            if not self.access_rule:
                return False

            db = self._get_db_session()
            rule = db.query(Rule).filter_by(id=self.access_rule.id).first()
            if rule:
                db.delete(rule)
                db.commit()
                self.success(f"Deleted rule: {rule.key}")
                return True
            else:
                self.warning(f"Rule was already deleted")
                return True
        except Exception as e:
            self.error(f"Error deleting rule: {e}")
            return False

    def _delete_privacy_request(self, privacy_request) -> bool:
        """Delete a privacy request."""
        try:
            db = self._get_db_session()
            if privacy_request:
                db.delete(privacy_request)
                db.commit()
                self.success(f"Deleted privacy request: {privacy_request.id}")
                return True
            return False
        except Exception as e:
            self.error(f"Error deleting privacy request {privacy_request.id if privacy_request else 'unknown'}: {e}")
            return False

    def _debug_manual_task_integration(self) -> None:
        """Debug method to check manual task integration."""
        try:
            db = self._get_db_session()

            # Show information about the two privacy requests
            if hasattr(self, 'privacy_requests') and self.privacy_requests:
                self.info(f"📋 Created {len(self.privacy_requests)} privacy requests:")
                for i, pr in enumerate(self.privacy_requests, 1):
                    self.info(f"   Request {i}: {pr.id} (external_id: {pr.external_id})")
                    if "conditions-met" in pr.external_id:
                        self.info(f"     → Expected: Manual task SHOULD be created (email: customer-1@example.com)")
                    else:
                        self.info(f"     → Expected: Manual task should NOT be created (email: nonexistent@example.com)")

            # Check if manual task addresses are being generated
            manual_addresses = get_manual_task_addresses(db)
            self.info(f"🎯 Manual task addresses found: {len(manual_addresses)}")
            for addr in manual_addresses:
                self.info(f"   - {addr.value}")

            # Check if our connection has manual tasks
            connections_with_manual_tasks = get_connection_configs_with_manual_tasks(db)
            self.info(f"🔗 Connections with manual tasks: {len(connections_with_manual_tasks)}")
            for conn in connections_with_manual_tasks:
                self.info(f"   - {conn.key} (type: {conn.connection_type})")

            # Check DSR 3.0 configuration
            self.info(f"🔧 DSR 3.0 configuration: {CONFIG.execution.use_dsr_3_0}")

        except Exception as e:
            self.error(f"Error in debug method: {e}")


if __name__ == "__main__":
    """Run the scenario directly."""
    parser = argparse.ArgumentParser(description="Run ManualTask with Conditional Dependencies QA Scenario")
    parser.add_argument("--teardown", action="store_true", help="Run teardown only")
    parser.add_argument("--setup", action="store_true", help="Run setup only (default)")
    args = parser.parse_args()

    scenario = ManualTaskWithConditionalDependencies()

    print("ManualTask with Conditional Dependencies QA Scenario")
    print("=" * 60)
    print("This scenario tests ManualTask conditional dependencies by creating:")
    print("1. A privacy request with email 'customer-1@example.com' (conditions SHOULD be met)")
    print("2. A privacy request with email 'nonexistent@example.com' (conditions should NOT be met)")
    print("=" * 60)

    if args.teardown:
        # Run teardown only
        print("\n🧹 Running teardown...")
        teardown_success = scenario.teardown()

        if teardown_success:
            print("\n✅ Teardown completed successfully!")
        else:
            print("\n❌ Teardown failed!")
    else:
        # Run setup
        print("\n🔄 Running setup...")
        setup_success = scenario.setup()

        if setup_success:
            print("\n✅ Setup completed successfully!")
            print("\nℹ️  To clean up resources later, run this script with --teardown flag:")
            print("    python qa/scenarios/manual_task_with_conditional_dependencies.py --teardown")
        else:
            print("\n❌ Setup failed!")

    print("\n" + "=" * 60)
    print("Scenario execution completed!")

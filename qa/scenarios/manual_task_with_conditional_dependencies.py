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
from datetime import datetime
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


from qa.utils import QATestScenario, Argument

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
from fides.api.task.manual.manual_task_utils import get_manual_task_addresses, get_connection_configs_with_manual_tasks

# Set up the manual test with python qa/scenarios/manual_task_with_conditional_dependencies.py
# Teardown with python python qa/scenarios/manual_task_with_conditional_dependencies.py --teardown

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
        "sort_order": 0
    },
    # Customer email contains specific value condition (leaf) - references postgres dataset field
    {
        "parent_id": None,  # Will be updated after root group is created
        "condition_type": ManualTaskConditionalDependencyType.leaf,
        "field_address": f"{POSTGRES_DATASET_KEY}:customer:email",
        "operator": "list_contains",
        "value": "customer-1",
        "sort_order": 1
    },
    # Nested group condition (OR)
    {
        "parent_id": None,  # Will be updated after root group is created
        "condition_type": ManualTaskConditionalDependencyType.group,
        "logical_operator": "or",
        "sort_order": 2
    },
    # Customer ID condition (leaf) - references postgres dataset field
    {
        "parent_id": None,  # Will be updated after nested group is created
        "condition_type": ManualTaskConditionalDependencyType.leaf,
        "field_address": f"{POSTGRES_DATASET_KEY}:customer:id",
        "operator": ">",
        "value": 0,
        "sort_order": 0
    },
    # Customer email not empty condition (leaf) - references postgres dataset field
    {
        "parent_id": None,  # Will be updated after nested group is created
        "condition_type": ManualTaskConditionalDependencyType.leaf,
        "field_address": f"{POSTGRES_DATASET_KEY}:customer:email",
        "operator": "!=",
        "value": "",
        "sort_order": 1
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
        ),
        'teardown': Argument(
            type=bool,
            default=False,
            description="Whether to run teardown after setup"
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

    @property
    def description(self) -> str:
        return "Creates a ManualTask with ManualTaskConditionalDependencies using a ManualTask connection."

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

            # Step 2: Create or verify ManualTask connection exists
            self.step(2, "Creating/verifying ManualTask connection")
            if not self._create_or_verify_manual_task_connection():
                self.error(f"Failed to create/verify connection {self.connection_key}")
                return False

            # Step 3: Create ManualTask
            self.step(3, "Creating ManualTask")
            if not self._create_manual_task():
                self.error("Failed to create ManualTask")
                return False

            # Step 4: Create ManualTaskConfig
            self.step(4, "Creating ManualTaskConfig")
            if not self._create_manual_task_config():
                self.error("Failed to create ManualTaskConfig")
                return False

            # Step 5: Create ManualTaskConfigFields
            self.step(5, "Creating ManualTaskConfigFields")
            if not self._create_manual_task_config_fields():
                self.error("Failed to create ManualTaskConfigFields")
                return False

            # Step 6: Create ManualTaskConditionalDependencies
            self.step(6, "Creating ManualTaskConditionalDependencies")
            if not self._create_conditional_dependencies():
                self.error("Failed to create ManualTaskConditionalDependencies")
                return False

            # Step 7: Create Policy
            self.step(7, "Creating Policy")
            if not self._create_policy():
                self.error("Failed to create Policy")
                return False

            # Step 8: Create Privacy Request
            self.step(8, "Creating Privacy Request")
            if not self._create_privacy_request():
                self.error("Failed to create Privacy Request")
                return False

            # Step 9: Debug - Check manual task integration
            self.step(9, "Debug - Checking manual task integration")
            self._debug_manual_task_integration()

            self.final_success("Setup completed successfully!")
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario."""
        self.cleanup_phase()

        print(f"Cleaning up ManualTask test resources...")
        deleted_counts = {'manual_tasks': 0, 'conditional_dependencies': 0, 'connections': 0, 'storage_configs': 0, 'policies': 0, 'rules': 0}

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

            # Step 3: Delete manual task connection config via API
            self.step(3, "Deleting manual task connection config")
            if self.connection_key and self._delete_connection_config(self.connection_key):
                deleted_counts["connections"] += 1
                self.success(f"Deleted manual task connection config: {self.connection_key}")
            else:
                self.already_cleaned("ConnectionConfig", self.connection_key)

            # Step 4: Delete postgres connection config via API
            self.step(4, "Deleting postgres connection config")
            if self.postgres_connection_key and self._delete_connection_config(self.postgres_connection_key):
                deleted_counts["connections"] += 1
                self.success(f"Deleted postgres connection config: {self.postgres_connection_key}")
            else:
                self.already_cleaned("ConnectionConfig", self.postgres_connection_key)

            # Step 5: Delete storage config
            self.step(5, "Deleting storage config")
            if self._delete_storage_config():
                deleted_counts["storage_configs"] += 1
                self.success("Deleted storage config")
            else:
                self.already_cleaned("StorageConfig", "storage config")

            # Step 6: Delete rule
            self.step(6, "Deleting rule")
            if self._delete_rule():
                deleted_counts["rules"] += 1
                self.success("Deleted rule")
            else:
                self.already_cleaned("Rule", "rule")

            # Step 7: Delete policy
            self.step(7, "Deleting policy")
            if self._delete_policy():
                deleted_counts["policies"] += 1
                self.success("Deleted policy")
            else:
                self.already_cleaned("Policy", "policy")

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

            # Get the CTL dataset
            ctl_dataset = db.query(CtlDataset).filter_by(
                fides_key=POSTGRES_DATASET_KEY
            ).first()

            if not ctl_dataset:
                self.error("CTL dataset not found")
                return False

            # Create dataset config linked to both
            DatasetConfig.create(
                db=db,
                data={
                    "fides_key": POSTGRES_DATASET_KEY,
                    "connection_config_id": connection.id,
                    "ctl_dataset_id": ctl_dataset.id,
                },
            )

            self.success(f"Created postgres connection config: {self.postgres_connection_key}")
            return True

        except Exception as e:
            self.error(f"Error creating/verifying postgres connection: {e}")
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
        """Create a privacy request."""
        try:
            db = self._get_db_session()
            # Create privacy request
            privacy_request = PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"ext-{str(uuid4())}",
                    "started_processing_at": datetime.utcnow(),
                    "requested_at": datetime.utcnow(),
                    "status": "pending",
                    "origin": "https://example.com/",
                    "policy_id": self.policy.id,
                    "client_id": self.policy.client_id,
                },
            )

            # Cache identity - this email exists in the postgres example data and matches our conditional dependencies
            identity_kwargs = {"email": "customer-1@example.com"}
            privacy_request.cache_identity(identity_kwargs)
            privacy_request.persist_identity(
                db=db,
                identity={"email": "customer-1@example.com"},
            )

            self.success(f"Created privacy request: {privacy_request.id}")
            return True

        except Exception as e:
            self.error(f"Error creating privacy request: {e}")
            return False

    def _debug_manual_task_integration(self) -> None:
        """Debug method to check manual task integration."""
        try:
            db = self._get_db_session()
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

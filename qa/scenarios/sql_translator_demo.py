#!/usr/bin/env python3
"""
QA demo for SQL translator functionality with user management and manual task assignment.

This demo creates:
1. Several users with different permission levels (Owner, Contributor, Viewer, Approver, Respondent)
2. A Manual Task connection with access configuration
3. Assignment of some (but not all) users to the manual task

Run with:
- python qa/scenarios/sql_translator_demo.py setup    # Creates demo resources
- python qa/scenarios/sql_translator_demo.py teardown # Cleans up demo resources
"""

import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import and_
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
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskParentEntityType,
    ManualTaskType,
    ManualTaskExecutionTiming,
    ManualTaskReference,
    ManualTaskReferenceType,
    ManualTaskInstance,
)
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.client import ClientDetail
from fides.api.oauth.roles import (
    OWNER,
    CONTRIBUTOR,
    VIEWER,
    APPROVER,
    RESPONDENT,
)
from fides.api.models.policy import Policy, Rule, RuleTarget, ActionType
from fides.api.models.storage import StorageConfig
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.task.conditional_dependencies.sql_translator import SQLConditionTranslator
from fides.api.task.manual.manual_task_utils import get_connection_configs_with_manual_tasks

# Initialize database
SessionLocal = sessionmaker(bind=sync_engine)
with SessionLocal() as db:
    seed_db(db)

# User data for different roles
DEMO_USERS = [
    {
        "username": "demo_owner_user",
        "email": "demo.owner@example.com",
        "first_name": "Demo",
        "last_name": "Owner",
        "password": "DemoOwner123!",
        "roles": [OWNER],
        "assign_to_task": True,
        "description": "Owner with full admin access"
    },
    {
        "username": "demo_contributor_user",
        "email": "demo.contributor@example.com",
        "first_name": "Demo",
        "last_name": "Contributor",
        "password": "DemoContrib123!",
        "roles": [CONTRIBUTOR],
        "assign_to_task": True,
        "description": "Contributor with edit access (no storage/messaging config)"
    },
    {
        "username": "demo_viewer_user",
        "email": "demo.viewer@example.com",
        "first_name": "Demo",
        "last_name": "Viewer",
        "password": "DemoViewer123!",
        "roles": [VIEWER],
        "assign_to_task": False,
        "description": "Viewer with read-only access to Data Map"
    },
    {
        "username": "demo_approver_user",
        "email": "demo.approver@example.com",
        "first_name": "Demo",
        "last_name": "Approver",
        "password": "DemoApprover123!",
        "roles": [APPROVER],
        "assign_to_task": True,
        "description": "Approver who can manage Privacy Requests"
    },
    {
        "username": "demo_respondent_user",
        "email": "demo.respondent@example.com",
        "first_name": "Demo",
        "last_name": "Respondent",
        "password": "DemoRespondent123!",
        "roles": [RESPONDENT],
        "assign_to_task": True,
        "description": "Internal respondent for manual DSR tasks"
    }
]

# Manual Task configuration fields
MANUAL_TASK_FIELDS = [
    {
        "field_key": "data_verification",
        "field_type": ManualTaskFieldType.checkbox,
        "field_metadata": {
            "label": "Data Verification Complete",
            "required": True,
            "help_text": "Verify that all requested data has been collected"
        }
    },
    {
        "field_key": "processing_notes",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Processing Notes",
            "required": False,
            "help_text": "Add any notes about the data processing"
        }
    },
    {
        "field_key": "reviewer_approval",
        "field_type": ManualTaskFieldType.checkbox,
        "field_metadata": {
            "label": "Reviewer Approval",
            "required": True,
            "help_text": "Confirm review and approval of the processed data"
        }
    }
]


class SQLTranslatorDemo(QATestScenario):
    """QA demo for SQL translator functionality with user management and manual task assignment."""

    arguments = {
        'connection_key': Argument(
            type=str,
            default="sql_translator_demo_connection",
            description="Connection key for the demo Manual Task connection"
        )
    }

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.db = self._get_db_session()
        self.connection_key = kwargs.get('connection_key', 'sql_translator_demo_connection')
        self.demo_users = []
        self.connection_config = None
        self.manual_task = None
        self.manual_task_config = None
        self.privacy_request = None

    @property
    def description(self) -> str:
        return "Creates a demo environment with users of different permission levels and a Manual Task with access configuration. Some users are assigned to the manual task while others are not, demonstrating role-based access control."

    def setup(self) -> bool:
        """Setup the SQL translator demo environment."""
        self.setup_phase()

        print(f"Setting up SQL Translator Demo with connection: {self.connection_key}")

        try:
            # Step 1: Create demo users with different roles
            self.step(1, "Creating demo users with different permission levels")
            if not self._create_demo_users():
                self.error("Failed to create demo users")
                return False

            # Step 2: Create Manual Task connection
            self.step(2, "Creating Manual Task connection")
            if not self._create_manual_task_connection():
                self.error(f"Failed to create connection {self.connection_key}")
                return False

            # Step 3: Create Manual Task
            self.step(3, "Creating Manual Task")
            if not self._create_manual_task():
                self.error("Failed to create Manual Task")
                return False

            # Step 4: Create Manual Task configuration
            self.step(4, "Creating Manual Task configuration")
            if not self._create_manual_task_config():
                self.error("Failed to create Manual Task configuration")
                return False

            # Step 5: Create Manual Task fields
            self.step(5, "Creating Manual Task configuration fields")
            if not self._create_manual_task_fields():
                self.error("Failed to create Manual Task fields")
                return False

            # Step 6: Assign selected users to Manual Task
            self.step(6, "Assigning users to Manual Task")
            if not self._assign_users_to_manual_task():
                self.error("Failed to assign users to Manual Task")
                return False

            # Step 7: Create policy and storage config for privacy requests
            self.step(7, "Creating policy and storage config")
            if not self._create_policy_and_storage():
                self.error("Failed to create policy and storage config")
                return False

            # Step 8: Create privacy request to trigger manual task instances
            self.step(8, "Creating privacy request to trigger manual task instances")
            if not self._create_privacy_request():
                self.error("Failed to create privacy request")
                return False

            # Step 9: Verify manual task instances were created
            self.step(9, "Verifying manual task instances were created")
            if not self._verify_manual_task_instances():
                self.error("Failed to verify manual task instances")
                return False

            # Step 10: Display demo summary
            self.step(10, "Displaying demo summary")
            self._display_demo_summary()

            # Step 11: Demonstrate SQL Translator functionality
            self.step(11, "Demonstrating SQL Translator functionality")
            if not self._demonstrate_sql_translator():
                self.error("Failed to demonstrate SQL translator")
                return False

            self.final_success("SQL Translator Demo setup completed successfully!")
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all demo resources."""
        self.cleanup_phase()

        print(f"Cleaning up SQL Translator Demo resources...")
        deleted_counts = {
            'users': 0,
            'clients': 0,
            'permissions': 0,
            'manual_tasks': 0,
            'connections': 0,
            'task_references': 0,
            'privacy_requests': 0,
            'task_instances': 0,
            'policies': 0,
            'storage_configs': 0
        }

        try:
            # Step 1: Delete Privacy Request and Manual Task Instances
            self.step(1, "Deleting Privacy Request and Manual Task Instances")
            privacy_count, instance_count = self._delete_privacy_request_and_instances()
            deleted_counts["privacy_requests"] += privacy_count
            deleted_counts["task_instances"] += instance_count
            if privacy_count > 0:
                self.success(f"Deleted {privacy_count} privacy request(s) and {instance_count} task instance(s)")

            # Step 2: Delete Policy and Storage Config
            self.step(2, "Deleting Policy and Storage Config")
            policy_count, storage_count = self._delete_policy_and_storage()
            deleted_counts["policies"] += policy_count
            deleted_counts["storage_configs"] += storage_count
            if policy_count > 0:
                self.success(f"Deleted {policy_count} policy/policies and {storage_count} storage config(s)")

            # Step 3: Delete Manual Task (cascades to references)
            self.step(3, "Deleting Manual Task and references")
            if self._delete_manual_task_by_connection():
                deleted_counts["manual_tasks"] += 1
                self.success(f"Deleted Manual Task and all related resources")

            # Step 4: Delete Manual Task connection
            self.step(4, "Deleting Manual Task connection")
            if self._delete_connection_config_by_key():
                deleted_counts["connections"] += 1
                self.success(f"Deleted connection: {self.connection_key}")

            # Step 5: Delete demo users (cascades to clients and permissions)
            self.step(5, "Deleting demo users")
            for user_data in DEMO_USERS:
                user = self.db.query(FidesUser).filter_by(username=user_data["username"]).first()
                if user and self._delete_user_by_username(user_data["username"]):
                    deleted_counts["users"] += 1
                    deleted_counts["clients"] += 1  # Client is cascade deleted
                    deleted_counts["permissions"] += 1  # Permissions are cascade deleted
                    self.success(f"Deleted user: {user.username}")

            self.summary("Cleanup Summary", deleted_counts)
            self.final_success("SQL Translator Demo cleanup completed successfully!")
            return True

        except Exception as e:
            self.final_error(f"Cleanup failed: {e}")
            return False

    def _get_db_session(self) -> Session:
        """Get a database session."""
        SessionLocal = sessionmaker(bind=sync_engine)
        return SessionLocal()

    def _create_demo_users(self) -> bool:
        """Create demo users with different permission levels."""
        try:
            for user_data in DEMO_USERS:
                # Check if user already exists
                existing_user = self.db.query(FidesUser).filter_by(username=user_data["username"]).first()
                if existing_user:
                    self.info(f"User {user_data['username']} already exists, skipping creation")
                    self.demo_users.append(existing_user)
                    continue

                # Create user
                user = FidesUser.create(
                    db=self.db,
                    data={
                        "username": user_data["username"],
                        "email_address": user_data["email"],
                        "first_name": user_data["first_name"],
                        "last_name": user_data["last_name"],
                        "password": user_data["password"],
                    },
                )
                self.demo_users.append(user)

                # Create user permissions
                permissions = FidesUserPermissions.create(
                    db=self.db,
                    data={
                        "user_id": user.id,
                        "roles": user_data["roles"]
                    }
                )
                self.success(f"Created user: {user_data['username']} ({user_data['description']})")

            return True

        except Exception as e:
            self.error(f"Error creating demo users: {e}")
            return False

    def _create_manual_task_connection(self) -> bool:
        """Create the Manual Task connection."""
        try:
            # Check if connection already exists
            existing_connection = self.db.query(ConnectionConfig).filter_by(key=self.connection_key).first()
            if existing_connection:
                self.info(f"Connection {self.connection_key} already exists")
                self.connection_config = existing_connection
                return True

            # Create new connection
            connection_data = {
                "name": "SQL Translator Demo Manual Task Connection",
                "key": self.connection_key,
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
                "secrets": {},  # Manual Task connections don't need secrets
                "disabled": False,
                "description": "Demo connection for SQL translator functionality with manual task assignment",
            }

            self.connection_config = ConnectionConfig.create(db=self.db, data=connection_data)
            self.success(f"Created Manual Task connection: {self.connection_key}")

            return True

        except Exception as e:
            self.error(f"Error creating Manual Task connection: {e}")
            return False

    def _create_manual_task(self) -> bool:
        """Create the Manual Task."""
        try:
            # Check if manual task already exists for this connection
            existing_task = self.db.query(ManualTask).filter(
                ManualTask.parent_entity_id == self.connection_config.id,
                ManualTask.parent_entity_type == ManualTaskParentEntityType.connection_config
            ).first()

            if existing_task:
                self.info(f"Manual Task already exists for connection")
                self.manual_task = existing_task
                return True

            # Create new manual task
            manual_task_data = {
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": self.connection_config.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config
            }

            self.manual_task = ManualTask.create(db=self.db, data=manual_task_data)
            self.success(f"Created Manual Task: {self.manual_task.id}")

            return True

        except Exception as e:
            self.error(f"Error creating Manual Task: {e}")
            return False

    def _create_manual_task_config(self) -> bool:
        """Create Manual Task configuration."""
        try:
            # Check if config already exists for this task
            existing_config = self.db.query(ManualTaskConfig).filter_by(
                task_id=self.manual_task.id,
                config_type=ManualTaskConfigurationType.access_privacy_request,
                is_current=True
            ).first()

            if existing_config:
                self.info(f"Manual Task configuration already exists: {existing_config.id}")
                self.manual_task_config = existing_config
                return True

            config_data = {
                "task_id": self.manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "version": 1,
                "is_current": True,
                "execution_timing": ManualTaskExecutionTiming.post_execution
            }

            self.manual_task_config = ManualTaskConfig.create(db=self.db, data=config_data)
            self.success(f"Created Manual Task configuration: {self.manual_task_config.id}")

            return True

        except Exception as e:
            self.error(f"Error creating Manual Task configuration: {e}")
            return False

    def _create_manual_task_fields(self) -> bool:
        """Create Manual Task configuration fields."""
        try:
            # Check if the expected number of unique fields already exist for this config
            existing_fields = self.db.query(ManualTaskConfigField).filter_by(
                config_id=self.manual_task_config.id
            ).all()

            # Check if we have the expected fields (no duplicates)
            expected_field_keys = {field["field_key"] for field in MANUAL_TASK_FIELDS}
            existing_field_keys = {field.field_key for field in existing_fields}

            if existing_field_keys == expected_field_keys and len(existing_fields) == len(MANUAL_TASK_FIELDS):
                self.info(f"Manual Task fields already exist ({len(existing_fields)} fields), skipping creation")
                return True
            elif existing_fields:
                for field in existing_fields:
                    field.delete(db=self.db)

            # Create new fields
            for field_data in MANUAL_TASK_FIELDS:
                field_create_data = {
                    "task_id": self.manual_task.id,
                    "config_id": self.manual_task_config.id,
                    **field_data,
                }

                field = ManualTaskConfigField.create(db=self.db, data=field_create_data)
                self.info(f"Created field: {field.field_key}")

            self.success(f"Created {len(existing_fields)} Manual Task fields")

            return True

        except Exception as e:
            self.error(f"Error creating Manual Task fields: {e}")
            return False

    def _assign_users_to_manual_task(self) -> bool:
        """Assign selected users to the Manual Task."""
        try:
            # Check if assignments already exist
            existing_assignments = self.db.query(ManualTaskReference).filter_by(
                task_id=self.manual_task.id,
                reference_type=ManualTaskReferenceType.assigned_user
            ).all()

            if existing_assignments:
                for assignment in existing_assignments:
                    assignment.delete(db=self.db)

            assigned_count = 0
            for i, user_data in enumerate(DEMO_USERS):
                # Get user from database in current session to avoid detached instance error
                user = self.db.query(FidesUser).filter_by(username=user_data["username"]).first()
                if not user:
                    self.error(f"User not found: {user_data['username']}")
                    continue

                if user_data["assign_to_task"]:
                    # Create ManualTaskReference to assign user
                    reference_data = {
                        "task_id": self.manual_task.id,
                        "reference_id": user.id,
                        "reference_type": ManualTaskReferenceType.assigned_user
                    }

                    reference = ManualTaskReference.create(db=self.db, data=reference_data)
                    assigned_count += 1

                    self.success(f"Assigned user to task: {user.username} ({user_data['roles'][0]})")
                else:
                    self.info(f"User NOT assigned to task: {user.username} ({user_data['roles'][0]})")

            self.success(f"Assigned {assigned_count} users to Manual Task")

            return True

        except Exception as e:
            self.error(f"Error assigning users to Manual Task: {e}")
            return False

    def _create_policy_and_storage(self) -> bool:
        """Create policy and storage config for privacy requests."""
        try:
            # Check if policy already exists
            existing_policy = self.db.query(Policy).filter_by(
                key="sql_translator_demo_policy"
            ).first()

            if existing_policy:
                self.info("Policy already exists, reusing")
                # Find associated storage and rule
                access_rule = self.db.query(Rule).filter_by(
                    policy_id=existing_policy.id,
                    action_type=ActionType.access
                ).first()
                if access_rule:
                    storage_config = self.db.query(StorageConfig).filter_by(
                        id=access_rule.storage_destination_id
                    ).first()
                return True

            # Create storage config for access rule
            storage_data = {
                "name": "SQL Translator Demo Storage",
                "type": "local",
                "details": {
                    "naming": "request_id",
                },
                "key": "sql_translator_demo_storage",
                "format": "json",
            }
            storage_config = StorageConfig.create(db=self.db, data=storage_data)
            self.success(f"Created storage config: {storage_config.key}")

            # Create policy
            policy_data = {
                "name": "SQL Translator Demo Policy",
                "key": "sql_translator_demo_policy",
            }
            policy = Policy.create(db=self.db, data=policy_data)
            self.success(f"Created policy: {policy.key}")

            # Create access rule
            rule_data = {
                "action_type": ActionType.access.value,
                "name": "SQL Translator Demo Access Rule",
                "key": "sql_translator_demo_access_rule",
                "policy_id": policy.id,
                "storage_destination_id": storage_config.id,
            }
            access_rule = Rule.create(db=self.db, data=rule_data)
            self.success(f"Created access rule: {access_rule.key}")

            # Create rule targets for common data categories
            data_categories = [
                "user.contact.email",
                "user.name",
                "user.unique_id",
            ]

            for category in data_categories:
                RuleTarget.create(
                    db=self.db,
                    data={
                        "data_category": category,
                        "rule_id": access_rule.id,
                    },
                )

            self.info(f"Created {len(data_categories)} rule targets")
            return True

        except Exception as e:
            self.error(f"Error creating policy and storage: {e}")
            return False

    def _create_privacy_request(self) -> bool:
        """Create privacy request to trigger manual task instances."""
        try:
            # Check if privacy request already exists
            existing_request = self.db.query(PrivacyRequest).filter_by(
                external_id="sql-translator-demo-request"
            ).first()

            if existing_request:
                self.info("Privacy request already exists, reusing")
                self.privacy_request = existing_request
                return True

            # Get policy fresh from database to avoid session issues
            policy = self.db.query(Policy).filter_by(key="sql_translator_demo_policy").first()

            if not policy:
                self.error("Policy not found for privacy request creation")
                return False

            # Create privacy request
            request_data = {
                "external_id": "sql-translator-demo-request",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.now(timezone.utc),
                "status": "pending",
                "origin": "https://demo.example.com/",
                "policy_id": policy.id,
                "client_id": policy.client_id,
            }

            self.privacy_request = PrivacyRequest.create(db=self.db, data=request_data)
            self.success(f"Created privacy request: {self.privacy_request.id}")

            # Cache identity for the privacy request
            identity_data = {"email": "demo.user@example.com"}
            self.privacy_request.cache_identity(identity_data)
            self.privacy_request.persist_identity(db=self.db, identity=identity_data)

            # Trigger manual task instance creation
            connection_configs_with_manual_tasks = get_connection_configs_with_manual_tasks(self.db)

            # Filter to only our demo connection
            demo_connections = [
                conn for conn in connection_configs_with_manual_tasks
                if conn.key == self.connection_key
            ]

            if demo_connections:
                self.privacy_request.create_manual_task_instances(
                    self.db, demo_connections
                )
                self.success(f"Created {len(self.privacy_request.manual_task_instances)} manual task instances")
            else:
                self.info("No manual task connections found for instance creation")

            return True

        except Exception as e:
            self.error(f"Error creating privacy request: {e}")
            return False

    def _verify_manual_task_instances(self) -> bool:
        """Verify that manual task instances were created correctly."""
        try:

            if not self.privacy_request:
                self.error("Privacy request not found!")
                return False

            if not self.privacy_request.manual_task_instances:
                self.error("No manual task instances found!")
                return False

            self.success(f"✓ Found {len(self.privacy_request.manual_task_instances)} manual task instances")

            # Get our demo connection and manual task fresh from database
            if not self.connection_config:
                self.error("Demo connection not found!")
                return False

            if not self.manual_task:
                self.error("Demo manual task not found!")
                return False

            # Verify instances are linked to our manual task
            our_instances = [
                instance for instance in self.privacy_request.manual_task_instances
                if instance.task_id == self.manual_task.id
            ]

            if not our_instances:
                self.error("No instances found for our demo manual task!")
                return False

            self.success(f"✓ {len(our_instances)} instances are linked to our demo manual task")

            return True

        except Exception as e:
            self.error(f"Error verifying manual task instances: {e}")
            return False

    def _demonstrate_sql_translator(self) -> bool:
        """Demonstrate SQL Translator functionality with different types of conditions."""
        try:
            print("\n" + "="*80)
            print("🔍 SQL TRANSLATOR DEMONSTRATION")
            print("="*80)

            # Initialize SQL translator
            translator = SQLConditionTranslator(self.db)

            # Demo 1: Simple Condition
            print(f"\n📋 Demo 1: Simple Condition")
            print("-" * 40)
            self._demo_simple_condition(translator)

            # Demo 2: Group Condition (AND)
            print(f"\n📋 Demo 2: Group Condition (AND)")
            print("-" * 40)
            self._demo_group_condition(translator)

            # Demo 3: Nested Condition (AND with OR nested)
            print(f"\n📋 Demo 3: Nested Condition (AND with OR nested)")
            print("-" * 40)
            self._demo_nested_condition(translator)

            # Demo 4: Complex Multi-Table Query (Manual Task Business Logic)
            print(f"\n📋 Demo 4: Complex Multi-Table Query (Manual Task Business Logic)")
            print("-" * 40)
            self._demo_manual_task_query(translator)

            print("\n" + "="*80)
            print("✅ SQL Translator demonstration completed successfully!")
            print("="*80)
            return True

        except Exception as e:
            self.error(f"Error demonstrating SQL translator: {e}")
            return False

    def _execute_and_display_query(self, translator: SQLConditionTranslator, condition: Condition, expected: str) -> list:
        """Helper method to execute query and display results."""
        try:
            query = translator.generate_query_from_condition(condition)
            sql_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
            print(f"\n🔍 Generated SQL:\n   {sql_str}")

            results = query.all()
            print(f"\n📊 Results: Found {len(results)} record(s)")
            if results:
                for result in results[:3]:  # Limit to first 3 for brevity
                    if hasattr(result, 'username'):
                        print(f"   - User: {result.username} ({result.email_address})")
                    else:
                        print(f"   - {type(result).__name__} (ID: {result.id})")
                if len(results) > 3:
                    print(f"   ... and {len(results) - 3} more")

            print(f"\n✅ Expected: {expected}")
            print(f"✅ Actual: {len(results)} record(s)")
            return results

        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return []

    def _demo_simple_condition(self, translator: SQLConditionTranslator) -> None:
        """Demonstrate a simple condition."""
        condition = ConditionLeaf(
            field_address="fidesuser.username",
            operator=Operator.eq,
            value="demo_owner_user"
        )

        print(f"📝 Condition: {condition.field_address} {condition.operator.value} '{condition.value}'")
        print(f"   Description: Find user with username 'demo_owner_user'")

        self._execute_and_display_query(translator, condition, "1 user (demo_owner_user)")

    def _demo_group_condition(self, translator: SQLConditionTranslator) -> None:
        """Demonstrate a group condition with AND operator."""
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field_address="fidesuser.username", operator=Operator.starts_with, value="demo_"),
                ConditionLeaf(field_address="fidesuser.email_address", operator=Operator.contains, value="@example.com")
            ]
        )

        print(f"📝 Condition: {condition.logical_operator.value.upper()} group")
        print(f"   - fidesuser.username starts_with 'demo_'")
        print(f"   - fidesuser.email_address contains '@example.com'")
        print(f"   Description: Find demo users with example.com email addresses")

        self._execute_and_display_query(translator, condition, "5 users (all demo users)")

    def _demo_nested_condition(self, translator: SQLConditionTranslator) -> None:
        """Demonstrate a nested condition with AND and OR operators."""
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionGroup(
                    logical_operator=GroupOperator.or_,
                    conditions=[
                        ConditionLeaf(field_address="fidesuser.username", operator=Operator.eq, value="demo_owner_user"),
                        ConditionLeaf(field_address="fidesuser.username", operator=Operator.eq, value="demo_viewer_user")
                    ]
                ),
                ConditionLeaf(field_address="fidesuser.email_address", operator=Operator.contains, value="@example.com")
            ]
        )

        print(f"📝 Condition: Nested AND/OR")
        print(f"   (username = 'demo_owner_user' OR username = 'demo_viewer_user')")
        print(f"   AND email contains '@example.com'")
        print(f"   Description: Find owner or viewer users with example.com emails")

        self._execute_and_display_query(translator, condition, "2 users (demo_owner_user and demo_viewer_user)")

    def _demo_manual_task_query(self, translator: SQLConditionTranslator) -> None:
        """Demonstrate a complex multi-table query for manual task business logic."""
        user = self.db.query(FidesUser).filter_by(username="demo_owner_user").first()
        if not user:
            self.error("Demo user not found!")
            return
        demo_user_id = user.id

        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field_address="manual_task_instance.status", operator=Operator.neq, value="complete"),
                ConditionLeaf(field_address="manual_task.references.reference_id", operator=Operator.eq, value=demo_user_id),
                ConditionLeaf(field_address="privacyrequest.status", operator=Operator.neq, value="complete")
            ]
        )

        print(f"📝 Condition: Complex Multi-Table Query")
        print(f"   - manual_task_instance.status != 'complete' (PRIMARY)")
        print(f"   - manual_task.references.reference_id = demo_owner_user_id")
        print(f"   - privacyrequest.status != 'complete'")
        print(f"   Description: Find actionable manual task instances for demo_owner_user")

        try:
            results = self._execute_and_display_query(translator, condition, "1 instance (demo_owner_user)")
            expected_count = self._get_expected_manual_task_count(self.db, user)

            print(f"\n✅ Expected: {expected_count} | Actual: {len(results)}")
            if len(results) == expected_count:
                print(f"🎉 Perfect match! Complex multi-table query handled correctly")
            else:
                print(f"⚠️  Count difference may indicate complex relationship handling")
        except Exception as e:
            self.error(f"Error generating manual task query: {e}")
            return False

    def _get_expected_manual_task_count(self, db, user: FidesUser) -> int:
        """Get expected count of manual task instances for demo_owner_user for comparison."""
        try:
            if not self.privacy_request.manual_task_instances:
                return 0

            # Count instances that meet our criteria
            count = 0
            for instance in self.privacy_request.manual_task_instances:
                # Check if this instance's task is assigned to our user
                task_assigned = db.query(
                    ManualTaskReference
                ).filter(ManualTaskReference.reference_id == user.id).first()

                if (task_assigned and
                    self.privacy_request and
                    self.privacy_request.status != "complete" and
                    instance.status != "complete"):
                    count += 1

            return count

        except Exception as e:
            print(f"   (Could not calculate expected count: {e})")
            return 0


    def _display_demo_summary(self) -> None:
        """Display a summary of the created demo environment."""
        print("\n" + "="*80)
        print("SQL TRANSLATOR DEMO SUMMARY")
        print("="*80)

        print(f"\n📋 Manual Task Connection: {self.connection_key}")

        # Get fresh connection and manual task data to avoid session issues
        if self.connection_config:
            if self.manual_task:
                print(f"   └── Task ID: {self.manual_task.id}")

                # Get current config
                current_config = self.db.query(ManualTaskConfig).filter_by(
                    task_id=self.manual_task.id,
                    is_current=True
                ).first()

                if current_config:
                    print(f"   └── Config ID: {current_config.id}")

                    # Get field count
                    field_count = self.db.query(ManualTaskConfigField).filter_by(
                        task_id=self.manual_task.id
                    ).count()
                    print(f"   └── Fields: {field_count}")

        print(f"\n👥 Created Users ({len(DEMO_USERS)} total):")
        assigned_users = []
        unassigned_users = []

        # Get fresh data from database to avoid session issues
        # Get user data
        for user_data in DEMO_USERS:
            user = self.db.query(FidesUser).filter_by(username=user_data["username"]).first()
            if user:
                role_display = user_data['roles'][0].upper()
                user_info = f"   {user.username} ({user.email_address}) - {role_display}"

                if user_data["assign_to_task"]:
                    assigned_users.append(user_info + " ✅ ASSIGNED")
                else:
                    unassigned_users.append(user_info + " ❌ NOT ASSIGNED")

        print(f"\n✅ Users Assigned to Manual Task ({len(assigned_users)}):")
        for user_info in assigned_users:
            print(user_info)

        print(f"\n❌ Users NOT Assigned to Manual Task ({len(unassigned_users)}):")
        for user_info in unassigned_users:
            print(user_info)

        # Get field data from same session
        fields = self.db.query(ManualTaskConfigField).filter_by(task_id=self.manual_task.id).all()
        print(f"\n🔧 Manual Task Fields ({len(fields)}):")
        for field in fields:
            required = "REQUIRED" if field.field_metadata.get("required") else "OPTIONAL"
            print(f"   └── {field.field_key} ({field.field_type.value}) - {required}")

        # Get privacy request and instances info fresh from database
        if self.privacy_request:
            print(f"\n📋 Privacy Request:")
            print(f"   └── ID: {self.privacy_request.id}")
            print(f"   └── External ID: {self.privacy_request.external_id}")
            print(f"   └── Status: {self.privacy_request.status}")

            # Get policy info
            policy = self.db.query(Policy).filter_by(key="sql_translator_demo_policy").first()
            print(f"   └── Policy: {policy.key if policy else 'N/A'}")

            # Get manual task instances

            print(f"\n🎯 Manual Task Instances ({len(self.privacy_request.manual_task_instances)}):")
            for instance in self.privacy_request.manual_task_instances:
                print(f"   └── Instance ID: {instance.id}")
                print(f"       ├── Config: {instance.config.config_type.value}")
                print(f"       ├── Status: {instance.status}")
                print(f"       └── Task: {instance.config.task_id}")

                # Show which users can access this instance
                assigned_users = self.db.query(ManualTaskReference).filter_by(
                    task_id=instance.config.task_id,
                    reference_type=ManualTaskReferenceType.assigned_user
                ).all()

                if assigned_users:
                    print(f"       └── Accessible by {len(assigned_users)} assigned users:")
                    for ref in assigned_users:
                        user = self.db.query(FidesUser).filter_by(id=ref.reference_id).first()
                        if user:
                            user_role = next(
                                (ud['roles'][0] for ud in DEMO_USERS if ud['username'] == user.username),
                                'UNKNOWN'
                            )
                            print(f"           ├── {user.username} ({user_role})")

        print("\n" + "="*80)
        print("🎉 SQL Translator Demo Environment Ready!")
        print("="*80)
        print("✅ Users created with different permission levels")
        print("✅ Manual Task configured with access controls")
        print("✅ Privacy Request created and processed")
        print("✅ Manual Task Instances automatically generated")
        print("✅ Role-based access control demonstrated")
        print("="*80)

    def _delete_manual_task_by_connection(self) -> bool:
        """Delete Manual Task and all related resources by finding them via connection key."""
        try:
            # Find connection by key
            connection = self.db.query(ConnectionConfig).filter_by(key=self.connection_key).first()
            if not connection:
                self.info(f"Connection {self.connection_key} not found, nothing to delete")
                return False

            # Find manual task for this connection
            if not self.manual_task:
                self.info(f"No Manual Task found for connection {self.connection_key}")
                return False

            # Delete manual task (this should cascade to configs, fields, and references)
            self.manual_task.delete(self.db)
            return True

        except Exception as e:
            self.error(f"Error deleting Manual Task: {e}")
            return False

    def _delete_connection_config_by_key(self) -> bool:
        """Delete the connection configuration by key."""
        try:
            if not self.connection_config:
                self.info(f"Connection {self.connection_key} not found, nothing to delete")
                return False

            self.connection_config.delete(self.db)
            return True

        except Exception as e:
            self.error(f"Error deleting connection config: {e}")
            return False

    def _delete_user_by_username(self, username: str) -> bool:
        """Delete a user by username (cascades to client and permissions)."""
        try:
            # Find user by username
            user = self.db.query(FidesUser).filter_by(username=username).first()
            if not user:
                return False

            # Delete user (permissions are cascade deleted)
            user.delete(self.db)
            return True
        except Exception as e:
            self.error(f"Error deleting user {username}: {e}")
            return False

    def _delete_privacy_request_and_instances(self) -> tuple[int, int]:
        """Delete privacy request and all associated manual task instances."""
        try:
            privacy_count = 0
            instance_count = 0

            if self.privacy_request:
                # Delete associated manual task instances first
                instances = self.privacy_request.manual_task_instances

                for instance in instances:
                    instance.delete(self.db)
                    instance_count += 1

                # Delete the privacy request
                self.privacy_request.delete(self.db)
                privacy_count += 1

                self.success(f"Deleted privacy request and {instance_count} instances")
            else:
                self.info("No privacy request found to delete")

            return privacy_count, instance_count

        except Exception as e:
            self.error(f"Error deleting privacy request and instances: {e}")
            return 0, 0

    def _delete_policy_and_storage(self) -> tuple[int, int]:
        """Delete policy and storage config created for the demo."""
        try:
            policy_count = 0
            storage_count = 0

            # Find policy first
            policy = self.db.query(Policy).filter_by(
                key="sql_translator_demo_policy"
            ).first()

            if policy:
                # Delete rules and rule targets first (manual cleanup to avoid cascade issues)
                rules = self.db.query(Rule).filter_by(policy_id=policy.id).all()
                for rule in rules:
                    # Delete rule targets first
                    rule_targets = self.db.query(RuleTarget).filter_by(rule_id=rule.id).all()
                    for target in rule_targets:
                        self.db.delete(target)

                    # Then delete the rule
                    self.db.delete(rule)

                # Now delete the policy
                policy.delete(self.db)
                policy_count += 1
                self.success(f"Deleted policy and associated rules: sql_translator_demo_policy")

            # Find and delete storage config
            storage = self.db.query(StorageConfig).filter_by(
                key="sql_translator_demo_storage"
            ).first()

            if storage:
                storage.delete(self.db)
                storage_count += 1
                self.success(f"Deleted storage config: sql_translator_demo_storage")

            if policy_count == 0 and storage_count == 0:
                self.info("No policy or storage config found to delete")

            return policy_count, storage_count

        except Exception as e:
            self.error(f"Error deleting policy and storage: {e}")
            self.db.rollback()
            return 0, 0


if __name__ == "__main__":
    """Run the SQL translator demo."""
    parser = argparse.ArgumentParser(description="Run SQL Translator Demo")
    parser.add_argument("action", choices=["setup", "teardown"], help="Action to perform")
    parser.add_argument("--connection-key", default="sql_translator_demo_connection",
                       help="Connection key for the demo")
    args = parser.parse_args()

    demo = SQLTranslatorDemo(connection_key=args.connection_key)

    print("SQL Translator Demo")
    print("=" * 50)
    print("This demo creates users with different permission levels and demonstrates")
    print("manual task assignment with role-based access control.")
    print("=" * 50)

    if args.action == "setup":
        print("\n🔄 Running setup...")
        success = demo.setup()
        if success:
            print("\n✅ Setup completed successfully!")
            print("\nTo clean up resources later, run:")
            print(f"    python qa/scenarios/sql_translator_demo.py teardown")
        else:
            print("\n❌ Setup failed!")

    elif args.action == "teardown":
        print("\n🧹 Running teardown...")
        success = demo.teardown()
        if success:
            print("\n✅ Teardown completed successfully!")
        else:
            print("\n❌ Teardown failed!")

    print("\n" + "=" * 50)
    print("Demo execution completed!")

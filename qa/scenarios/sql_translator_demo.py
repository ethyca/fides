#!/usr/bin/env python3
"""
QA scenario for demonstrating SQLConditionTranslator functionality.
This scenario demonstrates various SQL query generation capabilities without creating complex model instances.
"""

import sys
import argparse
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
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
from sqlalchemy.orm import Session, sessionmaker
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType, AccessLevel
from fides.api.models.sql_models import FidesUser, ClientDetail
from fides.api.models.policy import Policy, ActionType, Rule, RuleTarget
from fides.api.models.privacy_request.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.models.manual_task import (
    ManualTaskConfig,
    ManualTaskConfigurationType,
    ManualTaskExecutionTiming,
    ManualTaskInstance,
    ManualTask,
    ManualTaskReference,
    ManualTaskReferenceType,
    ManualTaskParentEntityType,
    ManualTaskType
)
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.conditional_dependencies.sql_translator import SQLConditionTranslator
from fides.api.task.conditional_dependencies.sql_schemas import OPERATOR_MAP
from fides.api.task.conditional_dependencies.schemas import ConditionLeaf, Operator, ConditionGroup, GroupOperator
from fides.config import get_config


DATA_CATEGORIES = [
    "user.contact.email",
    "user.name",
    "user.unique_id",
    "user.contact.address.city",
    "user.contact.address.street",
    "user.contact.address.state",
    "user.contact.address.postal_code"
]

class SQLTranslatorDemo(QATestScenario):
    """QA scenario for demonstrating SQLConditionTranslator functionality."""

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.connection_key = 'connection_key'
        self.test_manual_tasks = []
        self.test_manual_task_references = []

    @property
    def description(self) -> str:
        return "Demonstrates SQLConditionTranslator functionality with various condition types and SQL query generation."

    def _get_db_session(self) -> Session:
        """Get a database session."""
        SessionLocal = sessionmaker(bind=sync_engine)
        with SessionLocal() as db:
            return db

    def setup(self) -> bool:
        """Demonstrate SQL translator functionality."""
        self.setup_phase()
        print("Setting up SQLConditionTranslator demo...")

        try:
            # Step 1: Create test data
            print("Step 1: Creating test data")
            self._create_test_data()

            # Demo 1: Basic conditions
            print("Step 2: Demonstrating basic conditions")
            self._demo_basic_conditions()

            # Demo 2: String operations
            print("Step 3: Demonstrating string operations")
            self._demo_string_operations()

            # Demo 3: Complex conditions
            print("Step 4: Demonstrating complex conditions")
            self._demo_complex_conditions()

            # Demo 4: Relationship queries
            print("Step 5: Demonstrating relationship queries")
            self._demo_relationship_queries()

            # Demo 5: All operators
            print("Step 6: Demonstrating all available operators")
            self._demo_all_operators()

            # Demo 6: Real-world examples
            print("Step 7: Real-world examples")
            self._demo_real_world_examples()

            print("✅ SQLConditionTranslator demo completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error during setup: {e}")
            traceback.print_exc()
            return False

    def teardown(self) -> bool:
        """Clean up test data."""
        try:
            db = self._get_db_session()

            # Clean up test data
            for pr in getattr(self, 'test_privacy_requests', []):
                try:
                    pr.delete(db)
                except Exception:
                    pass

            # Clean up manual task references first (due to foreign key constraints)
            for ref in getattr(self, 'test_manual_task_references', []):
                try:
                    db.delete(ref)
                    db.commit()
                except Exception:
                    pass

            # Clean up manual tasks
            for task in getattr(self, 'test_manual_tasks', []):
                try:
                    task.delete(db)
                except Exception:
                    pass

            for user in getattr(self, 'test_users', []):
                try:
                    user.delete(db)
                except Exception:
                    pass

            if hasattr(self, 'test_client') and self.test_client:
                try:
                    self.test_client.delete(db)
                except Exception:
                    pass

            if hasattr(self, 'test_policy') and self.test_policy:
                try:
                    self.test_policy.delete(db)
                except Exception:
                    pass

            print("✅ Cleanup completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error during teardown: {e}")
            return False

    def _create_test_data(self):
        """Create test data for the demo."""
        print("  Creating test users...")

        # Get database session
        db = self._get_db_session()

        # Create test users
        self.test_users = []
        timestamp = int(time.time())
        for i, user_data in enumerate([
            {
                "username": f"demo_user_{timestamp}_{i+1}",
                "email_address": f"user{timestamp}_{i+1}@example.com",
                "first_name": f"User{i+1}",
                "last_name": "Demo",
                "hashed_password": f"hashed_password_{i+1}",
                "salt": f"salt_{i+1}",
            }
            for i in range(3)
        ]):
            user = FidesUser.create(
                db=db,
                data=user_data,
            )
            self.test_users.append(user)

        # Store the first user's ID to avoid detached instance issues later
        if self.test_users:
            self.first_test_user_id = self.test_users[0].id

        # Create test manual tasks and assign users
        print("  Creating test manual tasks...")
        self.test_manual_tasks = []
        self.test_manual_task_references = []
        connection = db.query(ConnectionConfig).filter_by(key=self.connection_key).first()
        if connection:
            self.success(f"Found existing connection: {self.connection_key}")
            self.connection_config_id = connection.id

        # Connection doesn't exist, create it
        else:
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

        try:
            manual_task = db.query(ManualTask).filter_by(parent_entity_id=self.connection_config_id, parent_entity_type=ManualTaskParentEntityType.connection_config).first()
            if manual_task:
                self.test_manual_tasks.append(manual_task)
                self.success(f"Found existing manual task: {manual_task.id}")
                config_data = {
                    "task_id": manual_task.id,
                    "config_type": ManualTaskConfigurationType.access_privacy_request,
                    "version": 1,
                    "is_current": True,
                    "execution_timing": ManualTaskExecutionTiming.post_execution
                }

                self.manual_task_config = ManualTaskConfig.create(db=db, data=config_data)
            else:
                manual_task = ManualTask.create(
                    db=db,
                    data={
                        "task_type": ManualTaskType.privacy_request,
                        "parent_entity_id": self.connection_config_id,
                        "parent_entity_type": ManualTaskParentEntityType.connection_config
                    }
                )
                self.test_manual_tasks.append(manual_task)
                config_data = {
                    "task_id": manual_task.id,
                    "config_type": ManualTaskConfigurationType.access_privacy_request,
                    "version": 1,
                    "is_current": True,
                    "execution_timing": ManualTaskExecutionTiming.post_execution
                }

                self.manual_task_config = ManualTaskConfig.create(db=db, data=config_data)

            # Assign the first user to the manual task (whether new or existing)
            # First check if this assignment already exists
            existing_reference = db.query(ManualTaskReference).filter_by(
                task_id=manual_task.id,
                reference_id=self.first_test_user_id,
                reference_type=ManualTaskReferenceType.assigned_user
            ).first()

            if not existing_reference:
                reference = ManualTaskReference.create(
                    db=db,
                    data={
                        "task_id": manual_task.id,
                        "reference_id": self.first_test_user_id,
                        "reference_type": ManualTaskReferenceType.assigned_user
                    }
                )
                self.test_manual_task_references.append(reference)
                print(f"    Assigned user {self.first_test_user_id} to manual task {manual_task.id}")
            else:
                self.test_manual_task_references.append(existing_reference)
                print(f"    User {self.first_test_user_id} already assigned to manual task {manual_task.id}")

            # Create a ManualTaskInstance for testing
            try:
                existing_instance = db.query(ManualTaskInstance).filter_by(task_id=manual_task.id).first()
                if not existing_instance:
                    # We need a ManualTaskConfig to create an instance
                    config = db.query(ManualTaskConfig).first()
                    if not config:
                        print("    ⚠️  No ManualTaskConfig found, cannot create ManualTaskInstance")
                    else:
                        instance = ManualTaskInstance.create(
                            db=db,
                            data={
                                "task_id": manual_task.id,
                                "config_id": config.id,
                                "entity_id": "test_entity_123",
                                "entity_type": "privacy_request",
                                "status": "pending"
                            }
                        )
                        print(f"    Created ManualTaskInstance {instance.id} for task {manual_task.id}")
                else:
                    print(f"    Found existing ManualTaskInstance {existing_instance.id} for task {manual_task.id}")
            except ImportError:
                print("    ⚠️  ManualTaskInstance model not available")
            except Exception as e:
                print(f"    ⚠️  Could not create ManualTaskInstance: {e}")

        except ImportError:
            print("  ⚠️  Manual task models not available - skipping manual task creation")
            self.test_manual_tasks = []
            self.test_manual_task_references = []

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

        print("  Creating test policy...")
        self.test_policy = Policy.create(
            db=db,
            data={
                "name": f"demo_policy_{timestamp}",
                "key": f"demo_policy_key_{timestamp}",
            },
        )
        # Create access rule
        self.access_rule = Rule.create(
            db=db,
            data={
                "action_type": ActionType.access.value,
                "name": f"Access Rule {str(uuid4())[:8]}",
                "key": f"access_rule_{str(uuid4())[:8]}",
                "policy_id": self.test_policy.id,
                "storage_destination_id": self.storage_config.id,
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

        print("  Creating test privacy requests...")
        now = datetime.now(timezone.utc)

        self.test_privacy_requests = []
        for i, status in enumerate([PrivacyRequestStatus.in_processing, PrivacyRequestStatus.approved, PrivacyRequestStatus.complete]):
            pr = PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"ext-demo-{timestamp}-{i+1}",
                    "started_processing_at": now,
                    "requested_at": now - timedelta(days=i+1),
                    "status": status,
                    "origin": "https://example.com/demo",
                    "policy_id": self.test_policy.id,
                    "submitted_by": self.test_users[i].id,
                },
            )
            self.test_privacy_requests.append(pr)

        print("  Creating test client...")
        self.test_client = ClientDetail(
            hashed_secret="demo_secret",
            salt="demo_salt",
            roles=["approver"],
            scopes=[],
            user_id=self.test_users[0].id,
        )
        db.add(self.test_client)
        db.commit()
        db.refresh(self.test_client)

        # Now create ManualTaskInstances linked to the Privacy Requests
        print("  Linking Manual Tasks to Privacy Requests...")
        try:
            if self.test_manual_tasks and self.test_privacy_requests:
                manual_task = self.test_manual_tasks[0]  # Use the first manual task

                # Create ManualTaskInstances for each Privacy Request
                for i, pr in enumerate(self.test_privacy_requests):
                    existing_instance = db.query(ManualTaskInstance).filter_by(
                        task_id=manual_task.id,
                        entity_id=pr.id,
                        entity_type="privacy_request"
                    ).first()

                    if not existing_instance:
                        instance = ManualTaskInstance.create(
                            db=db,
                            data={
                                "task_id": manual_task.id,
                                "config_id": self.manual_task_config.id,
                                "entity_id": pr.id,  # Link to actual Privacy Request ID
                                "entity_type": "privacy_request",
                                "status": "pending"
                            }
                        )
                        print(f"    Created ManualTaskInstance {instance.id} linking task {manual_task.id} to Privacy Request {pr.id}")
                    else:
                        print(f"    Found existing ManualTaskInstance {existing_instance.id} for task {manual_task.id} and PR {pr.id}")
        except Exception as e:
            print(f"    ⚠️  Error linking Manual Tasks to Privacy Requests: {e}")

        print(f"  ✅ Created {len(self.test_users)} users, 1 policy, {len(self.test_privacy_requests)} privacy requests, and 1 client")

    def _demo_basic_conditions(self):
        """Demonstrate basic equality and comparison conditions."""
        print("  🔍 Basic Conditions Demo")
        print("  " + "-" * 40)

        # Demo 1: Equality condition
        print("  📝 Demo 1: Find user by exact email")
        condition = ConditionLeaf(
            field_address="fidesuser.email_address",
            operator=Operator.eq,
            value="alice@example.com"
        )

        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

        # Demo 2: Numeric comparison
        print("  📝 Demo 2: Find privacy requests by status")
        condition = ConditionLeaf(
            field_address="privacyrequest.status",
            operator=Operator.eq,
            value="in_processing"
        )

        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

        # Demo 3: Greater than comparison
        print("  📝 Demo 3: Find users created after a certain date")
        condition = ConditionLeaf(
            field_address="fidesuser.created_at",
            operator=Operator.gt,
            value="2024-01-01T00:00:00Z"
        )

        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

    def _demo_string_operations(self):
        """Demonstrate string pattern matching operations."""
        print("  🔍 String Operations Demo")
        print("  " + "-" * 40)

        # Demo 1: Contains
        print("  📝 Demo 1: Find users with email containing 'example'")
        condition = ConditionLeaf(
            field_address="fidesuser.email_address",
            operator=Operator.contains,
            value="example"
        )

        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

        # Demo 2: Starts with
        print("  📝 Demo 2: Find users with email starting with 'admin'")
        condition = ConditionLeaf(
            field_address="fidesuser.email_address",
            operator=Operator.starts_with,
            value="admin"
        )

        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

        # Demo 3: Ends with
        print("  📝 Demo 3: Find users with email ending with '.com'")
        condition = ConditionLeaf(
            field_address="fidesuser.email_address",
            operator=Operator.ends_with,
            value=".com"
        )

        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

    def _demo_complex_conditions(self):
        """Demonstrate complex grouped conditions."""
        print("  🔍 Complex Conditions Demo")
        print("  " + "-" * 40)

        # Demo 1: AND condition
        print("  📝 Demo 1: Find users with email containing 'example' AND username starting with 'admin'")
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="fidesuser.email_address",
                    operator=Operator.contains,
                    value="example"
                ),
                ConditionLeaf(
                    field_address="fidesuser.username",
                    operator=Operator.starts_with,
                    value="admin"
                )
            ]
        )

        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

        # Demo 2: OR condition
        print("  📝 Demo 2: Find privacy requests with status 'approved' OR 'complete'")
        condition = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="privacyrequest.status",
                    operator=Operator.eq,
                    value="approved"
                ),
                ConditionLeaf(
                    field_address="privacyrequest.status",
                    operator=Operator.eq,
                    value="complete"
                )
            ]
        )

        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

        # Demo 3: Nested conditions
        print("  📝 Demo 3: Complex nested condition")
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="fidesuser.email_address",
                    operator=Operator.contains,
                    value="example"
                ),
                ConditionGroup(
                    logical_operator=GroupOperator.or_,
                    conditions=[
                        ConditionLeaf(
                            field_address="fidesuser.username",
                            operator=Operator.starts_with,
                            value="admin"
                        ),
                        ConditionLeaf(
                            field_address="fidesuser.username",
                            operator=Operator.starts_with,
                            value="user"
                        )
                    ]
                )
            ]
        )

        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)

        print(f"  Condition: {condition}")
        print(f"  SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

    def _demo_relationship_queries(self):
        """Demonstrate queries involving table relationships and JOINs."""
        print("  🔗 Relationship Queries Demo")
        print("  " + "-" * 40)

        # Demo 1: Manual Tasks assigned to specific users
        print("  📝 Demo 1: Find Manual Task Instances assigned to a specific user")

        db = self._get_db_session()

        # Use the same user that we assigned the manual task to
        if hasattr(self, 'first_test_user_id') and self.first_test_user_id:
            user_id = self.first_test_user_id
            print(f"  Using test user ID: {user_id} (same user assigned to manual task)")
        else:
            # Fallback to first user from database
            first_user = db.query(FidesUser).first()
            if not first_user:
                print("  ⚠️  No users found in database - skipping Manual Task demo")
                print()
                return
            user_id = first_user.id
            print(f"  Using database user ID: {user_id}")

        # ✅ First condition determines primary table
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                # First condition determines the primary table - manual_task_instance
                ConditionLeaf(
                    field_address="manual_task_instance.status",
                    operator=Operator.eq,
                    value="pending"
                ),
                # Related condition: the associated manual task is assigned to the user
                ConditionLeaf(
                    field_address="manual_task.assigned_users",
                    operator=Operator.list_contains,
                    value=user_id
                ),
            ]
        )

        translator = SQLConditionTranslator(db)
        # Check if the user assignment actually exists
        try:
            assignment_check = db.query(ManualTaskReference).filter_by(
                reference_id=user_id,
                reference_type=ManualTaskReferenceType.assigned_user
            ).first()
            if assignment_check:
                print(f"    ✅ Found user assignment: task_id={assignment_check.task_id}, user_id={assignment_check.reference_id}")
            else:
                print(f"    ❌ No user assignment found for user {user_id}")

            # Check if there are any ManualTaskInstance records
            instance_count = db.query(ManualTaskInstance).count()
            print(f"    📊 Total ManualTaskInstance records in database: {instance_count}")

            # If no instances exist and we have a task assignment, create a test instance
            if instance_count == 0 and assignment_check:
                print(f"    🔧 Creating test ManualTaskInstance for task {assignment_check.task_id}")
                try:
                    # Create a minimal ManualTaskInstance for testing
                    test_instance = ManualTaskInstance(
                        task_id=assignment_check.task_id,
                        config_id=None,  # We'll set this to None since no config exists
                        entity_id="test_entity_for_demo",
                        entity_type="privacy_request",
                        status="pending"
                    )
                    db.add(test_instance)
                    db.commit()
                    print(f"    ✅ Created test instance {test_instance.id}")
                    instance_count = 1
                except Exception as e:
                    print(f"    ❌ Failed to create test instance: {e}")
                    db.rollback()

            if instance_count > 0:
                instances = db.query(ManualTaskInstance).limit(3).all()
                for inst in instances:
                    print(f"      - Instance {inst.id}: task_id={inst.task_id}, status={inst.status}")

        except ImportError:
            print("    ⚠️  Cannot import manual task models for debugging")
        except Exception as e:
            print(f"    ⚠️  Debug error: {e}")

        try:
            query = translator.generate_query_from_condition(condition)
            print(f"  Condition: {condition}")
            print(f"  SQL: {query}")

            # Execute the query - it likely won't return results since we don't have manual task test data
            # but it demonstrates the relationship handling and query generation
            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Query executed successfully - {len(rows)} Manual Task Instance records returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
                print(f"  🎉 SUCCESS: Found Manual Task Instances assigned to user {user_id}!")
            else:
                # Check if we created manual task test data
                if hasattr(self, 'test_manual_tasks') and self.test_manual_tasks:
                    print(f"  📊 No Manual Tasks found assigned to user {user_id}")
                    print(f"  ℹ️  Note: Created {len(self.test_manual_tasks)} test manual tasks, but none assigned to this user")
                else:
                    print(f"  📊 No Manual Tasks found - no test manual task data was created")
        except Exception as e:
            print(f"  ⚠️  Query execution failed: {e}")
            print(f"  📝 Note: This may be expected if Manual Task models aren't available in this environment")
        print()

        # Demo 2: Find Privacy Requests with status in_progress, pending, approved, or awaiting_input and Manual Tasks assigned to user
        print("  📝 Demo 2: Find Privacy Request-related Manual Tasks assigned to a specific user")

        # Debug: Check what's in the database
        print("  🔍 Debug: Checking database state...")

        # Check Privacy Requests
        privacy_requests = db.query(PrivacyRequest).all()
        print(f"    📊 Total PrivacyRequest records: {len(privacy_requests)}")
        for pr in privacy_requests[:3]:
            print(f"      - PR {pr.id}: status={pr.status}")

        # Check Manual Task Instances and their links to Privacy Requests
        manual_task_instances = db.query(ManualTaskInstance).all()
        print(f"    📊 Total ManualTaskInstance records: {len(manual_task_instances)}")
        for instance in manual_task_instances:
            print(f"      - Instance {instance.id}: task_id={instance.task_id}, entity_id={instance.entity_id}, entity_type={instance.entity_type}")

        # Check if any Privacy Requests are linked to Manual Task Instances
        linked_instances = db.query(ManualTaskInstance).filter_by(entity_type="privacy_request").all()
        print(f"    📊 ManualTaskInstance records linked to Privacy Requests: {len(linked_instances)}")
        for instance in linked_instances:
            pr = db.query(PrivacyRequest).filter_by(id=instance.entity_id).first()
            if pr:
                print(f"      - Instance {instance.id} → PR {pr.id} (status: {pr.status})")
            else:
                print(f"      - Instance {instance.id} → PR {instance.entity_id} (NOT FOUND!)")
        print()
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="privacyrequest.status",
                    operator=Operator.list_contains,
                    value=[PrivacyRequestStatus.in_processing, PrivacyRequestStatus.pending, PrivacyRequestStatus.approved, PrivacyRequestStatus.requires_input, PrivacyRequestStatus.pending]
                ),
                ConditionLeaf(
                    field_address="manual_task.assigned_users",
                    operator=Operator.list_contains,
                    value=user_id
                )
            ]
        )

        try:
            query = translator.generate_query_from_condition(condition)
            print(f"  Condition: {condition}")
            print(f"  SQL: {query}")

            result = db.execute(query)
            rows = result.fetchall()
            print(f"  ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"  📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"  ❌ Query execution failed: {e}")
        print()

    def _demo_all_operators(self):
        """Demonstrate all available operators."""
        print("  🔍 All Operators Demo")
        print("  " + "-" * 40)

        print("  📝 Available operators and their SQL generation:")
        print()

        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        test_column = "fidesuser.email_address"
        test_value = "test@example.com"

        for operator in Operator:
            if operator in OPERATOR_MAP:
                try:
                    # Create a simple condition
                    condition = ConditionLeaf(
                        field_address=test_column,
                        operator=operator,
                        value=test_value if operator not in [Operator.exists, Operator.not_exists] else None
                    )

                    query = translator.generate_query_from_condition(condition)

                    print(f"  • {operator.name:15} → {query}")
                    print(f"    Condition: {condition}")

                    # Execute the query to verify it works
                    try:
                        result = db.execute(query)
                        rows = result.fetchall()
                        print(f"    ✅ Executed - {len(rows)} rows")
                    except Exception as exec_error:
                        print(f"    ❌ Execution failed: {exec_error}")

                except Exception as e:
                    print(f"  • {operator.name:15} → Error: {e}")

        print()

    def _demo_real_world_examples(self):
        """Demonstrate real-world use cases."""
        print("  🔍 Real-World Examples Demo")
        print("  " + "-" * 40)

        # Example 1: User management queries
        print("  📝 Example 1: User Management Queries")
        print("  " + "-" * 30)

        # Find active users
        print("  • Find active users (not disabled):")
        condition = ConditionLeaf(
            field_address="fidesuser.disabled",
            operator=Operator.eq,
            value=False
        )
        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)
        print(f"    Condition: {condition}")
        print(f"    SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"    ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"    📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"    ❌ Query execution failed: {e}")
        print()

        # Find users by role
        print("  • Find users with specific role:")
        condition = ConditionLeaf(
            field_address="fidesuser.roles",
            operator=Operator.contains,
            value="admin"
        )
        query = translator.generate_query_from_condition(condition)
        print(f"    Condition: {condition}")
        print(f"    SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"    ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"    📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"    ❌ Query execution failed: {e}")
        print()

        # Example 2: Privacy request queries
        print("  📝 Example 2: Privacy Request Queries")
        print("  " + "-" * 30)

        # Find requests from last week
        print("  • Find requests from last week:")
        condition = ConditionLeaf(
            field_address="privacyrequest.requested_at",
            operator=Operator.gte,
            value="2024-01-01T00:00:00Z"
        )
        db = self._get_db_session()
        translator = SQLConditionTranslator(db)
        query = translator.generate_query_from_condition(condition)
        print(f"    Condition: {condition}")
        print(f"    SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"    ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"    📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"    ❌ Query execution failed: {e}")
        print()

        # Find requests by specific user
        print("  • Find requests by specific user:")
        condition = ConditionLeaf(
            field_address="privacyrequest.submitted_by",
            operator=Operator.eq,
            value="user-123"
        )
        query = translator.generate_query_from_condition(condition)
        print(f"    Condition: {condition}")
        print(f"    SQL: {query}")

        # Execute the query to verify it works
        try:
            result = db.execute(query)
            rows = result.fetchall()
            print(f"    ✅ Executed successfully - {len(rows)} rows returned")
            if rows:
                print(f"    📊 Sample results: {[dict(row._mapping) for row in rows[:3]]}")
        except Exception as e:
            print(f"    ❌ Query execution failed: {e}")
        print()


def main():
    """Main entry point for the scenario."""
    parser = argparse.ArgumentParser(description="SQLConditionTranslator Demo QA Scenario")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Base URL for the Fides API")

    args = parser.parse_args()

    scenario = SQLTranslatorDemo(base_url=args.base_url)

    try:
        success = scenario.setup()
        if success:
            print("\n🎉 Demo completed successfully!")
        else:
            print("\n❌ Demo failed!")
            return 1
    finally:
        scenario.teardown()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

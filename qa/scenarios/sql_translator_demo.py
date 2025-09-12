#!/usr/bin/env python3
"""
QA scenario for demonstrating SQLConditionTranslator functionality.
This scenario demonstrates various SQL query generation capabilities without creating complex model instances.
"""

import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

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
from fides.api.models.sql_models import FidesUser, ClientDetail
from fides.api.models.policy import Policy
from fides.api.models.privacy_request.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.task.conditional_dependencies.sql_translator import SQLConditionTranslator
from fides.api.task.conditional_dependencies.schemas import ConditionLeaf, Operator, ConditionGroup, GroupOperator
from fides.config import get_config


class SQLTranslatorDemo(QATestScenario):
    """QA scenario for demonstrating SQLConditionTranslator functionality."""

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)

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

            # Demo 4: All operators
            print("Step 5: Demonstrating all available operators")
            self._demo_all_operators()

            # Demo 5: Real-world examples
            print("Step 6: Real-world examples")
            self._demo_real_world_examples()

            print("✅ SQLConditionTranslator demo completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error during setup: {e}")
            import traceback
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
        import time
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

        print("  Creating test policy...")
        self.test_policy = Policy.create(
            db=db,
            data={
                "name": f"demo_policy_{timestamp}",
                "key": f"demo_policy_key_{timestamp}",
            },
        )

        print("  Creating test privacy requests...")
        from datetime import datetime, timezone, timedelta
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

    def _demo_all_operators(self):
        """Demonstrate all available operators."""
        print("  🔍 All Operators Demo")
        print("  " + "-" * 40)

        from fides.api.task.conditional_dependencies.sql_schemas import OPERATOR_MAP
        from fides.api.task.conditional_dependencies.schemas import Operator

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

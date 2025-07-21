import uuid
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

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
    ManualTaskInstance,
    ManualTaskType,
)
from fides.api.models.policy import Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask
from fides.api.task.manual.manual_task_utils import (
    create_manual_task_artificial_graphs,
    create_manual_task_instances_for_privacy_request,
)


class TestManualTaskInstanceFiltering:
    @pytest.fixture()
    def manual_setup(self, db: Session, policy):
        """Create a connection config, manual task and two configs (access & erasure)."""
        # ConnectionConfig for manual task
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "Manual Task Connection",
                "key": f"manual_{uuid.uuid4()}",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
            },
        )

        # ManualTask attached to this connection
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request.value,
                "parent_entity_id": connection_config.id,
                "parent_entity_type": "connection_config",
            },
        )

        # Create access and erasure configs with fields
        configs = {}
        for config_type, field_key in [
            (ManualTaskConfigurationType.access_privacy_request, "access_field"),
            (ManualTaskConfigurationType.erasure_privacy_request, "erasure_field"),
        ]:
            config = ManualTaskConfig.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_type": config_type.value,
                    "is_current": True,
                },
            )

            ManualTaskConfigField.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": config.id,
                    "field_key": field_key,
                    "field_type": ManualTaskFieldType.text,
                    "field_metadata": {
                        "label": f"{config_type.value.title()} Field",
                        "required": True,
                        "data_categories": ["user.contact.email"],
                    },
                },
            )
            configs[config_type.value] = config

        yield {
            "connection_config": connection_config,
            "manual_task": manual_task,
            "access_config": configs["access_privacy_request"],
            "erasure_config": configs["erasure_privacy_request"],
        }

        # Cleanup
        try:
            for config in configs.values():
                config.delete(db)
            manual_task.delete(db)
            connection_config.delete(db)
        except Exception as e:
            print(f"Error deleting manual task: {e}")

    @pytest.fixture()
    def mixed_policy(self, db: Session):
        """Create a policy with both access and erasure rules."""
        policy = Policy.create(
            db=db,
            data={
                "name": "Mixed Policy",
                "key": "mixed_policy",
            },
        )

        # Add access rule
        Rule.create(
            db=db,
            data={
                "name": "Access Rule",
                "key": "access_rule",
                "policy_id": policy.id,
                "action_type": ActionType.access,
            },
        )

        # Add erasure rule
        Rule.create(
            db=db,
            data={
                "name": "Erasure Rule",
                "key": "erasure_rule",
                "policy_id": policy.id,
                "action_type": ActionType.erasure,
                "masking_strategy": {
                    "strategy": "null_rewrite",
                    "configuration": {},
                },
            },
        )

        yield policy
        try:
            policy.delete(db)
        except Exception as e:
            print(f"Error deleting policy: {e}")

    @pytest.fixture()
    def privacy_request(self, db: Session, mixed_policy):
        """Minimal PrivacyRequest for testing with mixed policy."""
        pr = PrivacyRequest.create(
            db=db,
            data={
                "requested_at": datetime.utcnow(),
                "policy_id": mixed_policy.id,
                "status": PrivacyRequestStatus.pending,
            },
        )
        yield pr
        pr.delete(db)

    @pytest.fixture()
    def access_only_policy(self, db: Session):
        """Create a policy with only access rules."""
        policy = Policy.create(
            db=db,
            data={
                "name": "Access Only Policy",
                "key": "access_only_policy",
            },
        )

        # Add access rule
        Rule.create(
            db=db,
            data={
                "name": "Access Rule",
                "key": "access_rule",
                "policy_id": policy.id,
                "action_type": ActionType.access,
            },
        )

        yield policy
        try:
            policy.delete(db)
        except Exception as e:
            print(f"Error deleting policy: {e}")

    @pytest.fixture()
    def erasure_only_policy(self, db: Session):
        """Create a policy with only erasure rules."""
        policy = Policy.create(
            db=db,
            data={
                "name": "Erasure Only Policy",
                "key": "erasure_only_policy",
            },
        )

        # Add erasure rule
        Rule.create(
            db=db,
            data={
                "name": "Erasure Rule",
                "key": "erasure_rule",
                "policy_id": policy.id,
                "action_type": ActionType.erasure,
                "masking_strategy": {
                    "strategy": "null_rewrite",
                    "configuration": {},
                },
            },
        )

        yield policy
        try:
            policy.delete(db)
        except Exception as e:
            print(f"Error deleting policy: {e}")

    @pytest.fixture()
    def access_privacy_request(self, db: Session, access_only_policy):
        """Privacy request with access-only policy."""
        pr = PrivacyRequest.create(
            db=db,
            data={
                "requested_at": datetime.utcnow(),
                "policy_id": access_only_policy.id,
                "status": PrivacyRequestStatus.pending,
            },
        )
        yield pr
        pr.delete(db)

    @pytest.fixture()
    def erasure_privacy_request(self, db: Session, erasure_only_policy):
        """Privacy request with erasure-only policy."""
        pr = PrivacyRequest.create(
            db=db,
            data={
                "requested_at": datetime.utcnow(),
                "policy_id": erasure_only_policy.id,
                "status": PrivacyRequestStatus.pending,
            },
        )
        yield pr
        pr.delete(db)

    def test_access_only_creates_access_instances(
        self, db: Session, manual_setup, privacy_request
    ):
        manual_task = manual_setup["manual_task"]
        access_config = manual_setup["access_config"]
        erasure_config = manual_setup["erasure_config"]

        # Instantiate dummy ManualTaskGraphTask and execute _ensure method directly
        graph_task = object.__new__(ManualTaskGraphTask)
        graph_task._ensure_manual_task_instances(
            db,
            [manual_task],
            privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Fetch instances
        instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.task_id == manual_task.id)
            .all()
        )
        assert len(instances) == 1
        assert instances[0].config_id == access_config.id
        # Ensure erasure config has no instance
        erasure_instance = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.config_id == erasure_config.id)
            .first()
        )
        assert erasure_instance is None

    def test_erasure_only_creates_erasure_instances(
        self, db: Session, manual_setup, privacy_request
    ):
        manual_task = manual_setup["manual_task"]
        access_config = manual_setup["access_config"]
        erasure_config = manual_setup["erasure_config"]

        # Instantiate dummy ManualTaskGraphTask and execute _ensure method directly
        graph_task = object.__new__(ManualTaskGraphTask)
        graph_task._ensure_manual_task_instances(
            db,
            [manual_task],
            privacy_request,
            ManualTaskConfigurationType.erasure_privacy_request,
        )

        instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.task_id == manual_task.id)
            .all()
        )
        assert len(instances) == 1
        assert instances[0].config_id == erasure_config.id
        access_instance = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.config_id == access_config.id)
            .first()
        )
        assert access_instance is None

    def test_create_manual_task_instances_filters_by_access_policy(
        self, db: Session, manual_setup, access_privacy_request
    ):
        """Test that create_manual_task_instances_for_privacy_request only creates access instances for access-only policies."""
        access_config = manual_setup["access_config"]
        erasure_config = manual_setup["erasure_config"]

        # Create instances using the utility function
        created_instances = create_manual_task_instances_for_privacy_request(
            db, access_privacy_request
        )

        # Should only create access instances
        assert len(created_instances) == 1
        assert created_instances[0].config_id == access_config.id

        # Verify no erasure instances were created
        erasure_instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.config_id == erasure_config.id)
            .all()
        )
        assert len(erasure_instances) == 0

    def test_create_manual_task_instances_filters_by_erasure_policy(
        self, db: Session, manual_setup, erasure_privacy_request
    ):
        """Test that create_manual_task_instances_for_privacy_request only creates erasure instances for erasure-only policies."""
        access_config = manual_setup["access_config"]
        erasure_config = manual_setup["erasure_config"]

        # Create instances using the utility function
        created_instances = create_manual_task_instances_for_privacy_request(
            db, erasure_privacy_request
        )

        # Should only create erasure instances
        assert len(created_instances) == 1
        assert created_instances[0].config_id == erasure_config.id

        # Verify no access instances were created
        access_instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.config_id == access_config.id)
            .all()
        )
        assert len(access_instances) == 0

    @pytest.mark.parametrize(
        "policy_fixture,expected_fields,excluded_fields",
        [
            (
                "access_privacy_request",
                ["access_field"],
                ["erasure_field"],
            ),
            (
                "erasure_privacy_request",
                ["erasure_field"],
                ["access_field"],
            ),
            (
                "privacy_request",
                ["access_field", "erasure_field"],
                [],
            ),
        ],
    )
    def test_artificial_graphs_filter_by_policy_type(
        self,
        db: Session,
        manual_setup,
        policy_fixture,
        expected_fields,
        excluded_fields,
        request,
    ):
        """Test that create_manual_task_artificial_graphs correctly filters fields based on policy type."""
        # Get the privacy request from the fixture
        privacy_request = request.getfixturevalue(policy_fixture)

        # Create artificial graphs using the utility function
        graphs = create_manual_task_artificial_graphs(db)

        # Should include exactly one graph
        assert len(graphs) == 1
        graph = graphs[0]

        # Get field names from the graph
        field_names = [field.name for field in graph.collections[0].fields]

        # Verify expected fields are included
        for field_name in expected_fields:
            assert (
                field_name in field_names
            ), f"Expected field {field_name} not found in graph"

        # Verify excluded fields are not included
        for field_name in excluded_fields:
            assert (
                field_name not in field_names
            ), f"Unexpected field {field_name} found in graph"

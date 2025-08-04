from datetime import datetime, timezone
from uuid import uuid4

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
    ManualTaskEntityType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskType,
)
from fides.api.models.policy import ActionType, Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus


class TestPrivacyRequestManualTaskInstances:
    """Test the manual_task_instances relationship and create_manual_task_instances method."""

    @pytest.fixture()
    @pytest.mark.usefixtures("policy")
    def manual_setup(self, db: Session):
        """Create a connection config, manual task and two configs (access & erasure)."""
        # ConnectionConfig for manual task
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "Manual Task Connection",
                "key": f"manual_{uuid4()}",
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
                "requested_at": datetime.now(timezone.utc),
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
                "requested_at": datetime.now(timezone.utc),
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
                "requested_at": datetime.now(timezone.utc),
                "policy_id": erasure_only_policy.id,
                "status": PrivacyRequestStatus.pending,
            },
        )
        yield pr
        pr.delete(db)

    def test_manual_task_instances_relationship(
        self, db, privacy_request, manual_setup
    ):
        """Test that the manual_task_instances relationship works correctly."""
        manual_task = manual_setup["manual_task"]
        access_config = manual_setup["access_config"]

        # Create a manual task instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": privacy_request.id,
                "entity_type": ManualTaskEntityType.privacy_request,
                "task_id": manual_task.id,
                "config_id": access_config.id,
            },
        )

        # Test the relationship
        assert len(privacy_request.manual_task_instances) == 1
        assert privacy_request.manual_task_instances[0].id == instance.id
        assert privacy_request.manual_task_instances[0].task_id == manual_task.id
        assert privacy_request.manual_task_instances[0].config_id == access_config.id

        # Cleanup
        instance.delete(db)

    def test_create_manual_task_instances_no_policy_rules(
        self, db, privacy_request, policy, connection_config
    ):
        """Test that no instances are created when policy has no relevant rules."""
        # Update privacy request to use policy with no rules
        privacy_request.policy_id = policy.id
        privacy_request.save(db)

        # Test that no instances are created
        instances = privacy_request.create_manual_task_instances(
            db, [connection_config]
        )
        assert len(instances) == 0

    def test_create_manual_task_instances_access_only(
        self, db, access_privacy_request, manual_setup
    ):
        """Test creating instances for access-only policy."""
        connection_config = manual_setup["connection_config"]
        access_config = manual_setup["access_config"]

        # Test that only access instances are created
        instances = access_privacy_request.create_manual_task_instances(
            db, [connection_config]
        )
        assert len(instances) == 1
        assert instances[0].config_id == access_config.id

        # Cleanup
        for instance in instances:
            instance.delete(db)

    def test_create_manual_task_instances_erasure_only(
        self, db, erasure_privacy_request, manual_setup
    ):
        """Test creating instances for erasure-only policy."""
        connection_config = manual_setup["connection_config"]
        erasure_config = manual_setup["erasure_config"]

        # Test that only erasure instances are created
        instances = erasure_privacy_request.create_manual_task_instances(
            db, [connection_config]
        )
        assert len(instances) == 1
        assert instances[0].config_id == erasure_config.id

        # Cleanup
        for instance in instances:
            instance.delete(db)

    def test_create_manual_task_instances_mixed_policy(
        self, db, privacy_request, manual_setup
    ):
        """Test creating instances for policy with both access and erasure rules."""
        connection_config = manual_setup["connection_config"]
        access_config = manual_setup["access_config"]
        erasure_config = manual_setup["erasure_config"]

        # Test that both access and erasure instances are created
        instances = privacy_request.create_manual_task_instances(
            db, [connection_config]
        )
        assert len(instances) == 2

        config_ids = {instance.config_id for instance in instances}
        assert config_ids == {access_config.id, erasure_config.id}

        # Cleanup
        for instance in instances:
            instance.delete(db)

    def test_create_manual_task_instances_duplicate_prevention(
        self, db, access_privacy_request, manual_setup
    ):
        """Test that duplicate instances are not created."""
        connection_config = manual_setup["connection_config"]
        manual_task = manual_setup["manual_task"]
        access_config = manual_setup["access_config"]

        # Create an existing instance manually
        existing_instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": access_privacy_request.id,
                "entity_type": ManualTaskEntityType.privacy_request,
                "task_id": manual_task.id,
                "config_id": access_config.id,
            },
        )

        # Test that no new instances are created (duplicate prevention)
        instances = access_privacy_request.create_manual_task_instances(
            db, [connection_config]
        )
        assert len(instances) == 0

        # Verify the existing instance is still there
        assert len(access_privacy_request.manual_task_instances) == 1
        assert (
            access_privacy_request.manual_task_instances[0].id == existing_instance.id
        )

        # Cleanup
        existing_instance.delete(db)

    def test_create_manual_task_instances_multiple_connections(
        self, db, access_privacy_request
    ):
        """Test creating instances for multiple connection configs."""
        # Create two connection configs
        connection_config_1 = ConnectionConfig.create(
            db=db,
            data={
                "name": "test_connection_1",
                "key": "test_connection_1",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
            },
        )

        connection_config_2 = ConnectionConfig.create(
            db=db,
            data={
                "name": "test_connection_2",
                "key": "test_connection_2",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
            },
        )

        # Create manual tasks and configs for both connections
        manual_task_1 = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request.value,
                "parent_entity_id": connection_config_1.id,
                "parent_entity_type": "connection_config",
            },
        )

        manual_task_2 = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request.value,
                "parent_entity_id": connection_config_2.id,
                "parent_entity_type": "connection_config",
            },
        )

        config_1 = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task_1.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request.value,
                "is_current": True,
            },
        )

        config_2 = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task_2.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request.value,
                "is_current": True,
            },
        )

        # Test that instances are created for both connections
        instances = access_privacy_request.create_manual_task_instances(
            db, [connection_config_1, connection_config_2]
        )
        assert len(instances) == 2

        config_ids = {instance.config_id for instance in instances}
        assert config_ids == {config_1.id, config_2.id}

        # Cleanup
        for instance in instances:
            instance.delete(db)
        config_1.delete(db)
        config_2.delete(db)
        manual_task_1.delete(db)
        manual_task_2.delete(db)
        connection_config_1.delete(db)
        connection_config_2.delete(db)

    def test_create_manual_task_instances_inactive_configs_filtered(
        self, db, access_privacy_request
    ):
        """Test that inactive configs are filtered out."""
        # Create a connection config
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "test_connection",
                "key": "test_connection",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
            },
        )

        # Create manual task
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request.value,
                "parent_entity_id": connection_config.id,
                "parent_entity_type": "connection_config",
            },
        )

        # Create active config
        active_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request.value,
                "is_current": True,
            },
        )

        # Create inactive config
        inactive_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request.value,
                "is_current": False,
            },
        )

        # Test that only active configs are used
        instances = access_privacy_request.create_manual_task_instances(
            db, [connection_config]
        )
        assert len(instances) == 1
        assert instances[0].config_id == active_config.id

        # Cleanup
        for instance in instances:
            instance.delete(db)
        active_config.delete(db)
        inactive_config.delete(db)
        manual_task.delete(db)
        connection_config.delete(db)

    def test_manual_task_instances_relationship_foreign_key_annotation(
        self, db, privacy_request, manual_setup
    ):
        """Test that the relationship works with the foreign() annotation."""
        manual_task = manual_setup["manual_task"]
        access_config = manual_setup["access_config"]

        # Create multiple instances
        instance_1 = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": privacy_request.id,
                "entity_type": ManualTaskEntityType.privacy_request,
                "task_id": manual_task.id,
                "config_id": access_config.id,
            },
        )

        instance_2 = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": privacy_request.id,
                "entity_type": ManualTaskEntityType.privacy_request,
                "task_id": manual_task.id,
                "config_id": access_config.id,
            },
        )

        # Test that the relationship loads correctly with foreign() annotation
        assert len(privacy_request.manual_task_instances) == 2

        instance_ids = {
            instance.id for instance in privacy_request.manual_task_instances
        }
        assert instance_ids == {instance_1.id, instance_2.id}

        # Test that the relationship can be queried
        session = Session.object_session(privacy_request)
        session.refresh(privacy_request)

        # This should work without SQLAlchemy errors
        instances = privacy_request.manual_task_instances
        assert len(instances) == 2

        # Cleanup
        instance_1.delete(db)
        instance_2.delete(db)

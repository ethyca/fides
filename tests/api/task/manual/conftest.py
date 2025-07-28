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
    ManualTaskParentEntityType,
    ManualTaskType,
)
from fides.api.models.policy import Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.task_resources import TaskResources

# =============================================================================
# Policy Fixtures
# =============================================================================


def _create_rule(db: Session, policy: Policy, action_type: ActionType, rule_name: str):
    """Create a rule for a policy"""
    key = "_".join(rule_name.lower().split(" "))
    data = {
        "name": rule_name,
        "key": key,
        "policy_id": policy.id,
        "action_type": action_type,
    }
    if action_type == ActionType.erasure:
        data["masking_strategy"] = {
            "strategy": "null_rewrite",
            "configuration": {},
        }
    return Rule.create(db=db, data=data)


def _create_manual_task_config_field(
    db: Session,
    manual_task: ManualTask,
    manual_config: ManualTaskConfig,
    field_data: dict,
):
    data = field_data.copy()
    data.update({"task_id": manual_task.id, "config_id": manual_config.id})
    return ManualTaskConfigField.create(
        db=db,
        data=data,
    )


@pytest.fixture()
def erasure_policy(db: Session):
    """Create a policy with only erasure rules."""
    policy = Policy.create(
        db=db,
        data={
            "name": "Erasure Policy",
            "key": "erasure_policy",
        },
    )

    # Add erasure rule
    _create_rule(db, policy, ActionType.erasure, "Erasure Rule")

    yield policy
    try:
        policy.delete(db)
    except Exception as e:
        print(f"Error deleting policy: {e}")


@pytest.fixture()
def access_policy(db: Session):
    """Create a policy with only access rules."""
    policy = Policy.create(
        db=db,
        data={
            "name": "Access Policy",
            "key": "access_policy",
        },
    )

    # Add access rule
    _create_rule(db, policy, ActionType.access, "Access Rule")

    yield policy
    try:
        policy.delete(db)
    except Exception as e:
        print(f"Error deleting policy: {e}")


@pytest.fixture()
def mixed_policy(db: Session):
    """Create a policy with both access and erasure rules."""
    policy = Policy.create(
        db=db,
        data={
            "name": "Mixed Policy",
            "key": "mixed_policy",
        },
    )

    # Add access  and erasure rules
    _create_rule(db, policy, ActionType.access, "Access Rule")
    _create_rule(db, policy, ActionType.erasure, "Erasure Rule")

    yield policy
    try:
        policy.delete(db)
    except Exception as e:
        print(f"Error deleting policy: {e}")


# =============================================================================
# Connection Config Fixtures
# =============================================================================


@pytest.fixture()
def connection_config(db: Session):
    """Create a connection config"""
    return ConnectionConfig.create(
        db=db,
        data={
            "name": "Manual Task Connection",
            "key": f"manual_{uuid.uuid4()}",
            "connection_type": ConnectionType.manual_task,
            "access": AccessLevel.write,
        },
    )


# =============================================================================
# Manual Task Fixtures
# =============================================================================


@pytest.fixture()
def manual_task(db: Session, connection_config):
    """Create a manual task"""
    return ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": connection_config.id,
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )


# =============================================================================
# Manual Task Config Fixtures
# =============================================================================


@pytest.fixture()
def manual_task_erasure_config(db: Session, manual_task):
    """Create a manual task config"""
    return ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.erasure_privacy_request,
            "version": 1,
            "is_current": True,
        },
    )


@pytest.fixture()
def manual_task_access_config(db: Session, manual_task):
    """Create a manual task config"""
    return ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.access_privacy_request,
            "version": 1,
            "is_current": True,
        },
    )


@pytest.fixture
def connection_with_manual_erasure_task(
    db, connection_config, manual_task, manual_task_erasure_config
):
    """Create a connection config with an erasure manual task and one text field"""

    field_data = {
        "field_key": "confirm_erasure",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Confirmation",
            "required": True,
            "data_categories": ["user.contact.email"],
        },
    }

    field = _create_manual_task_config_field(
        db, manual_task, manual_task_erasure_config, field_data
    )
    yield connection_config, manual_task, manual_task_erasure_config, field


@pytest.fixture()
def connection_with_manual_access_task(
    db, connection_config, manual_task, manual_task_access_config
):
    """Create a connection config with an access manual task and one text field"""

    field_data = {
        "field_key": "user_email",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Confirmation",
            "required": True,
            "data_categories": ["user.contact.email"],
        },
    }
    field = _create_manual_task_config_field(
        db, manual_task, manual_task_access_config, field_data
    )
    yield connection_config, manual_task, manual_task_access_config, field


@pytest.fixture()
def manual_setup(
    db: Session,
    connection_config,
    manual_task,
    manual_task_access_config,
    manual_task_erasure_config,
):
    """Create a connection config, manual task and two configs (access & erasure)."""
    # Create access config field
    access_field_data = {
        "field_key": "user_email",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Access Confirmation",
            "required": True,
            "data_categories": ["user.contact.email"],
        },
    }
    _create_manual_task_config_field(
        db, manual_task, manual_task_access_config, access_field_data
    )

    # Create erasure config field
    erasure_field_data = {
        "field_key": "confirm_erasure",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Erasure Confirmation",
            "required": True,
            "data_categories": ["user.contact.email"],
        },
    }
    _create_manual_task_config_field(
        db, manual_task, manual_task_erasure_config, erasure_field_data
    )

    yield {
        "connection_config": connection_config,
        "manual_task": manual_task,
        "access_config": manual_task_access_config,
        "erasure_config": manual_task_erasure_config,
    }

    # Cleanup
    try:
        for config in [manual_task_access_config, manual_task_erasure_config]:
            config.delete(db)
        manual_task.delete(db)
        connection_config.delete(db)
    except Exception as e:
        print(f"Error deleting manual task: {e}")


# =============================================================================
# Privacy Request Fixtures
# =============================================================================


@pytest.fixture()
def mixed_privacy_request(db: Session, mixed_policy):
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
def access_privacy_request(db: Session, access_policy):
    """Privacy request with access-only policy."""
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": datetime.utcnow(),
            "policy_id": access_policy.id,
            "status": PrivacyRequestStatus.pending,
        },
    )
    yield pr
    pr.delete(db)


@pytest.fixture()
def erasure_privacy_request(db: Session, erasure_policy):
    """Privacy request with erasure-only policy."""
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": datetime.utcnow(),
            "policy_id": erasure_policy.id,
            "status": PrivacyRequestStatus.pending,
        },
    )
    yield pr
    pr.delete(db)


# =============================================================================
# Test Helper Fixtures
# =============================================================================


@pytest.fixture()
def build_request_task():
    """Helper fixture to create a minimal RequestTask for manual_data collection"""

    def _build_request_task(
        db,
        privacy_request,
        connection_config,
        action_type=ActionType.access,
        manual_task=None,
    ):
        """Helper to create a minimal RequestTask for the manual_data collection"""
        # Use the standard manual data collection address
        collection_address = f"{connection_config.key}:manual_data"

        return RequestTask.create(
            db=db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": collection_address,
                "dataset_name": connection_config.key,
                "collection_name": "manual_data",
                "action_type": action_type.value,
                "status": ExecutionLogStatus.pending.value,
                "upstream_tasks": [],
                "downstream_tasks": [],
                "all_descendant_tasks": [],
                "collection": {
                    "name": "manual_data",
                    "fields": [],
                    "after": [],
                    "erase_after": [],
                    "grouped_inputs": [],
                    "data_categories": [],
                },
                "traversal_details": {
                    "dataset_connection_key": connection_config.key,
                    "incoming_edges": [],
                    "outgoing_edges": [],
                    "input_keys": [],
                },
            },
        )

    return _build_request_task


@pytest.fixture()
def build_task_resources():
    """Helper fixture to build TaskResources object"""

    def _build_task_resources(
        db, privacy_request, policy, connection_config, request_task
    ):
        """Helper to build TaskResources object"""
        return TaskResources(
            request=privacy_request,
            policy=policy,
            connection_configs=[connection_config],
            privacy_request_task=request_task,
            session=db,
        )

    return _build_task_resources

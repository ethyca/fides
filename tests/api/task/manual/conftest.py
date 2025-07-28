import uuid
from datetime import datetime
from io import BytesIO

import pytest
from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
)
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
    ManualTaskParentEntityType,
    ManualTaskSubmission,
    ManualTaskType,
    StatusType,
)
from fides.api.models.policy import Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask
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


def _build_request_task(
    db,
    privacy_request,
    connection_config,
    action_type=ActionType.access,
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


def _build_task_resources(db, privacy_request, policy, connection_config, request_task):
    """Helper to build TaskResources object"""
    return TaskResources(
        request=privacy_request,
        policy=policy,
        connection_configs=[connection_config],
        privacy_request_task=request_task,
        session=db,
    )


@pytest.fixture()
@pytest.mark.usefixtures("manual_task")
def request_task(db, privacy_request, connection_config):
    """Helper fixture to create a minimal RequestTask for manual_data collection"""
    return _build_request_task(
        db, privacy_request, connection_config, action_type=ActionType.access
    )


@pytest.fixture()
def task_resources(db, privacy_request, policy, connection_config, request_task):
    """Helper fixture to build TaskResources object"""
    return _build_task_resources(
        db, privacy_request, policy, connection_config, request_task
    )


# =============================================================================
# Manual Task Instance Fixtures
# =============================================================================


@pytest.fixture()
def manual_task_instance(
    db: Session, manual_task_access_config, access_privacy_request
):
    """Create a manual task instance for testing."""
    return ManualTaskInstance.create(
        db=db,
        data={
            "task_id": manual_task_access_config.task_id,
            "config_id": manual_task_access_config.id,
            "entity_id": access_privacy_request.id,
            "entity_type": ManualTaskEntityType.privacy_request.value,
            "status": StatusType.pending.value,
        },
    )


# =============================================================================
# Manual Task Submission Fixtures
# =============================================================================


@pytest.fixture()
def manual_task_submission_text(
    db: Session, manual_task_instance, connection_with_manual_access_task
):
    """Create a manual task submission with text field data."""
    # Get the field from the connection setup
    _, _, _, field = connection_with_manual_access_task

    return ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": field.task_id,
            "config_id": field.config_id,
            "field_id": field.id,
            "instance_id": manual_task_instance.id,
            "submitted_by": None,  # System submission
            "data": {
                "field_type": ManualTaskFieldType.text.value,
                "value": "user@example.com",
            },
        },
    )


@pytest.fixture()
def manual_task_submission_checkbox(
    db: Session, manual_task_instance, connection_with_manual_access_task
):
    """Create a manual task submission with checkbox field data."""
    # Get the field from the connection setup
    _, _, _, field = connection_with_manual_access_task

    return ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": field.task_id,
            "config_id": field.config_id,
            "field_id": field.id,
            "instance_id": manual_task_instance.id,
            "submitted_by": None,  # System submission
            "data": {"field_type": ManualTaskFieldType.checkbox.value, "value": True},
        },
    )


@pytest.fixture()
def manual_task_submission_attachment(
    db: Session, manual_task_instance, connection_with_manual_access_task
):
    """Create a manual task submission with attachment field data."""
    # Get the field from the connection setup
    _, _, _, field = connection_with_manual_access_task

    return ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": field.task_id,
            "config_id": field.config_id,
            "field_id": field.id,
            "instance_id": manual_task_instance.id,
            "submitted_by": None,  # System submission
            "data": {
                "field_type": ManualTaskFieldType.attachment.value,
                "value": None,  # Attachments are handled separately
            },
        },
    )


# =============================================================================
# Attachment Fixtures
# =============================================================================


@pytest.fixture()
def attachment_for_access_package(
    db: Session, manual_task_submission_attachment, storage_config, mock_s3_client
):
    """Create an attachment for access package inclusion."""

    # Create attachment with proper upload
    attachment = Attachment.create_and_upload(
        db=db,
        data={
            "file_name": "test_document.pdf",
            "attachment_type": "include_with_access_package",
            "storage_key": storage_config.key,
        },
        attachment_file=BytesIO(b"test document content"),
    )

    # Create attachment reference
    AttachmentReference.create(
        db=db,
        data={
            "attachment_id": attachment.id,
            "reference_id": manual_task_submission_attachment.id,
            "reference_type": AttachmentReferenceType.manual_task_submission.value,
        },
    )

    yield attachment

    # Cleanup
    try:
        attachment.delete(db)
    except Exception as e:
        print(f"Error deleting attachment: {e}")


@pytest.fixture()
def attachment_for_erasure_package(
    db: Session, manual_task_submission_attachment, storage_config, mock_s3_client
):
    """Create an attachment for erasure package inclusion."""

    # Create attachment with proper upload
    attachment = Attachment.create_and_upload(
        db=db,
        data={
            "file_name": "erasure_document.pdf",
            "attachment_type": "internal_use_only",  # Use valid enum value
            "storage_key": storage_config.key,
        },
        attachment_file=BytesIO(b"erasure document content"),
    )

    # Create attachment reference
    AttachmentReference.create(
        db=db,
        data={
            "attachment_id": attachment.id,
            "reference_id": manual_task_submission_attachment.id,
            "reference_type": AttachmentReferenceType.manual_task_submission.value,
        },
    )

    yield attachment

    # Cleanup
    try:
        attachment.delete(db)
    except Exception as e:
        print(f"Error deleting attachment: {e}")


@pytest.fixture()
def multiple_attachments_for_access(
    db: Session, manual_task_submission_attachment, storage_config, mock_s3_client
):
    """Create multiple attachments for access package inclusion."""

    attachments = []

    # Create first attachment
    attachment1 = Attachment.create_and_upload(
        db=db,
        data={
            "file_name": "document1.pdf",
            "attachment_type": "include_with_access_package",
            "storage_key": storage_config.key,
        },
        attachment_file=BytesIO(b"document 1 content"),
    )

    # Create second attachment
    attachment2 = Attachment.create_and_upload(
        db=db,
        data={
            "file_name": "document2.pdf",
            "attachment_type": "include_with_access_package",
            "storage_key": storage_config.key,
        },
        attachment_file=BytesIO(b"document 2 content"),
    )

    # Create attachment references
    for attachment in [attachment1, attachment2]:
        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment.id,
                "reference_id": manual_task_submission_attachment.id,
                "reference_type": AttachmentReferenceType.manual_task_submission.value,
            },
        )
        attachments.append(attachment)

    yield attachments

    # Cleanup
    for attachment in attachments:
        try:
            attachment.delete(db)
        except Exception as e:
            print(f"Error deleting attachment: {e}")


@pytest.fixture()
def attachment_with_retrieval_error(
    db: Session, manual_task_submission_attachment, storage_config, mock_s3_client
):
    """Create an attachment that will fail retrieval for testing error handling."""

    # Create attachment with proper upload
    attachment = Attachment.create_and_upload(
        db=db,
        data={
            "file_name": "error_document.pdf",
            "attachment_type": "include_with_access_package",
            "storage_key": storage_config.key,
        },
        attachment_file=BytesIO(b"error document content"),
    )

    # Create attachment reference
    AttachmentReference.create(
        db=db,
        data={
            "attachment_id": attachment.id,
            "reference_id": manual_task_submission_attachment.id,
            "reference_type": AttachmentReferenceType.manual_task_submission.value,
        },
    )

    yield attachment

    # Cleanup
    try:
        attachment.delete(db)
    except Exception as e:
        print(f"Error deleting attachment: {e}")


# =============================================================================
# Complete Setup Fixtures
# =============================================================================


@pytest.fixture()
def manual_task_graph_task(task_resources):
    """Helper fixture to create a ManualTaskGraphTask instance for testing"""
    # Create ManualTaskGraphTask with proper resources
    return ManualTaskGraphTask(task_resources)


@pytest.fixture()
def complete_manual_task_setup(
    db: Session,
    connection_with_manual_access_task,
    manual_task_instance,
    manual_task_submission_text,
):
    """Create a complete manual task setup with instance and submission."""
    connection_config, manual_task, config, field = connection_with_manual_access_task

    return {
        "connection_config": connection_config,
        "manual_task": manual_task,
        "config": config,
        "field": field,
        "instance": manual_task_instance,
        "submission": manual_task_submission_text,
    }


@pytest.fixture()
def complete_manual_task_setup_with_attachment(
    db: Session,
    connection_with_manual_access_task,
    manual_task_instance,
    manual_task_submission_attachment,
    attachment_for_access_package,
):
    """Create a complete manual task setup with instance, submission, and attachment."""
    connection_config, manual_task, config, field = connection_with_manual_access_task

    return {
        "connection_config": connection_config,
        "manual_task": manual_task,
        "config": config,
        "field": field,
        "instance": manual_task_instance,
        "submission": manual_task_submission_attachment,
        "attachment": attachment_for_access_package,
    }


# =============================================================================
# Manual Task Conditional Dependency Fixtures
# =============================================================================


@pytest.fixture
def mock_dataset_graph():
    """Create a mock dataset graph with collections and fields that match conditional dependencies"""
    from fides.api.graph.config import Collection, GraphDataset, ScalarField
    from fides.api.graph.graph import DatasetGraph

    # Create collections with fields that match the conditional dependencies
    customer_collection = Collection(
        name="customer",
        fields=[
            ScalarField(name="profile.age"),  # matches "user.profile.age"
            ScalarField(name="age"),  # also matches "user.profile.age"
            ScalarField(name="role"),  # matches "user.role"
        ],
    )

    payment_card_collection = Collection(
        name="payment_card",
        fields=[
            ScalarField(
                name="subscription.status"
            ),  # matches "billing.subscription.status"
            ScalarField(name="status"),  # also matches "billing.subscription.status"
        ],
    )

    # Create dataset graphs
    postgres_dataset = GraphDataset(
        name="postgres_example",
        collections=[customer_collection, payment_card_collection],
        connection_key="postgres_example",
    )

    # Create the mock dataset graph
    return DatasetGraph(postgres_dataset)


def create_condition_gt_18(
    db: Session, manual_task: ManualTask, parent_id: int = None, sort_order: int = 1
):
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "parent_id": parent_id,
            "field_address": "user.profile.age",
            "operator": "gte",
            "value": 18,
            "sort_order": sort_order,
        },
    )


def create_condition_age_lt_65(
    db: Session, manual_task: ManualTask, parent_id: int = None, sort_order: int = 2
):
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "parent_id": parent_id,
            "field_address": "user.profile.age",
            "operator": "lt",
            "value": 65,
            "sort_order": sort_order,
        },
    )


def create_condition_eq_active(
    db: Session, manual_task: ManualTask, parent_id: int = None, sort_order: int = 1
):
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "parent_id": parent_id,
            "field_address": "billing.subscription.status",
            "operator": "eq",
            "value": "active",
            "sort_order": sort_order,
        },
    )


def create_condition_eq_admin(
    db: Session, manual_task: ManualTask, parent_id: int = None, sort_order: int = 1
):
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "field_address": "user.role",
            "operator": "eq",
            "value": "admin",
            "sort_order": sort_order,
            "parent_id": parent_id,
        },
    )


@pytest.fixture()
def condition_gt_18(db: Session, manual_task: ManualTask):
    """Create a conditional dependency with field_address 'user.age' and operator 'gte' and value 18"""
    condition = create_condition_gt_18(db, manual_task, None)
    yield condition
    condition.delete(db)


@pytest.fixture()
def condition_age_lt_65(db: Session, manual_task: ManualTask):
    """Create a conditional dependency with field_address 'user.age' and operator 'lt' and value 65"""
    condition = create_condition_age_lt_65(db, manual_task, None)
    yield condition
    condition.delete(db)


@pytest.fixture()
def condition_eq_active(db: Session, manual_task: ManualTask):
    """Create a conditional dependency with field_address 'billing.subscription.status' and operator 'eq' and value 'active'"""
    condition = create_condition_eq_active(db, manual_task, None)
    yield condition
    condition.delete(db)


@pytest.fixture()
def condition_eq_admin(db: Session, manual_task: ManualTask):
    """Create a conditional dependency with field_address 'user.role' and operator 'eq' and value 'admin'"""
    condition = create_condition_eq_admin(db, manual_task, None)
    yield condition
    condition.delete(db)


@pytest.fixture()
def group_condition(db: Session, manual_task: ManualTask):
    """Create a group conditional dependency with logical_operator 'and'"""
    root_condition = ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.group,
            "logical_operator": "and",
            "sort_order": 1,
        },
    )
    create_condition_gt_18(db, manual_task, root_condition.id, 2)
    create_condition_eq_active(db, manual_task, root_condition.id, 3)
    yield root_condition
    root_condition.delete(db)


@pytest.fixture()
def nested_group_condition(db: Session, manual_task: ManualTask):
    """Create a nested group conditional dependency with logical_operator 'or'"""
    root_condition = ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.group,
            "logical_operator": "and",
            "sort_order": 1,
        },
    )
    nested_group = ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.group,
            "parent_id": root_condition.id,
            "logical_operator": "or",
            "sort_order": 2,
        },
    )
    create_condition_gt_18(db, manual_task, nested_group.id, 3)
    create_condition_eq_active(db, manual_task, nested_group.id, 4)
    create_condition_eq_admin(db, manual_task, nested_group.id, 5)
    yield root_condition
    root_condition.delete(db)

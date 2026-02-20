"""Tests for JiraTicketTask model, pending_external status, and polling task skeleton."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.jira_ticket_task import JiraTicketTask
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskInstance,
    ManualTaskParentEntityType,
    ManualTaskType,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.config import CONFIG
from fides.service.jira import polling_task
from fides.service.jira.polling_task import (
    poll_jira_tickets,
    register_poll_service,
)

# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def jira_connection_config(db: Session) -> ConnectionConfig:
    config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Jira Test Connection",
            "key": f"jira_test_{uuid.uuid4().hex[:8]}",
            "connection_type": ConnectionType.manual_task,
            "access": AccessLevel.write,
        },
    )
    yield config


@pytest.fixture
def manual_task(db: Session, jira_connection_config: ConnectionConfig) -> ManualTask:
    return ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": jira_connection_config.id,
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )


@pytest.fixture
def manual_task_config(db: Session, manual_task: ManualTask) -> ManualTaskConfig:
    return ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ActionType.access,
            "version": 1,
            "is_current": True,
        },
    )


@pytest.fixture
def manual_task_instance(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    privacy_request: PrivacyRequest,
) -> ManualTaskInstance:
    return ManualTaskInstance.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "entity_id": privacy_request.id,
            "entity_type": "privacy_request",
        },
    )


@pytest.fixture
def jira_ticket_task(
    db: Session,
    manual_task_instance: ManualTaskInstance,
    jira_connection_config: ConnectionConfig,
) -> JiraTicketTask:
    return JiraTicketTask.create(
        db=db,
        data={
            "manual_task_instance_id": manual_task_instance.id,
            "connection_config_id": jira_connection_config.id,
            "ticket_key": "PRIV-100",
            "ticket_url": "https://example.atlassian.net/browse/PRIV-100",
            "external_status": "To Do",
            "external_status_category": "new",
        },
    )


# ── PrivacyRequestStatus Tests ──────────────────────────────────────


class TestPendingExternalStatus:
    def test_pending_external_exists(self):
        assert PrivacyRequestStatus.pending_external == "pending_external"

    def test_pending_external_is_valid_enum_member(self):
        assert "pending_external" in [s.value for s in PrivacyRequestStatus]

    def test_pending_external_round_trips(self):
        status = PrivacyRequestStatus("pending_external")
        assert status == PrivacyRequestStatus.pending_external


# ── JiraTicketTask Model Tests ───────────────────────────────────────


class TestJiraTicketTaskModel:
    def test_create_jira_ticket_task(
        self, db: Session, jira_ticket_task: JiraTicketTask
    ):
        assert jira_ticket_task.id is not None
        assert jira_ticket_task.ticket_key == "PRIV-100"
        assert (
            jira_ticket_task.ticket_url
            == "https://example.atlassian.net/browse/PRIV-100"
        )
        assert jira_ticket_task.external_status == "To Do"
        assert jira_ticket_task.external_status_category == "new"
        assert jira_ticket_task.created_at is not None
        assert jira_ticket_task.updated_at is not None
        assert jira_ticket_task.last_polled_at is None

    def test_create_with_minimal_fields(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        jira_connection_config: ConnectionConfig,
    ):
        task = JiraTicketTask.create(
            db=db,
            data={
                "manual_task_instance_id": manual_task_instance.id,
                "connection_config_id": jira_connection_config.id,
            },
        )
        assert task.id is not None
        assert task.ticket_key is None
        assert task.ticket_url is None
        assert task.external_status is None
        assert task.external_status_category is None
        task.delete(db)

    def test_unique_constraint_on_instance_id(
        self,
        db: Session,
        jira_ticket_task: JiraTicketTask,
        jira_connection_config: ConnectionConfig,
    ):
        with pytest.raises(IntegrityError):
            JiraTicketTask.create(
                db=db,
                data={
                    "manual_task_instance_id": jira_ticket_task.manual_task_instance_id,
                    "connection_config_id": jira_connection_config.id,
                },
            )
        db.rollback()

    def test_relationship_to_manual_task_instance(
        self,
        db: Session,
        jira_ticket_task: JiraTicketTask,
        manual_task_instance: ManualTaskInstance,
    ):
        assert jira_ticket_task.manual_task_instance.id == manual_task_instance.id

    def test_relationship_to_connection_config(
        self,
        db: Session,
        jira_ticket_task: JiraTicketTask,
        jira_connection_config: ConnectionConfig,
    ):
        assert jira_ticket_task.connection_config.id == jira_connection_config.id

    def test_get_open_tasks(self, db: Session, jira_ticket_task: JiraTicketTask):
        open_tasks = JiraTicketTask.get_open_tasks(db)
        assert jira_ticket_task.id in [t.id for t in open_tasks]

    def test_get_open_tasks_excludes_done(
        self,
        db: Session,
        jira_ticket_task: JiraTicketTask,
    ):
        jira_ticket_task.external_status_category = "done"
        db.add(jira_ticket_task)
        db.commit()

        open_tasks = JiraTicketTask.get_open_tasks(db)
        assert jira_ticket_task.id not in [t.id for t in open_tasks]

    def test_get_by_instance_id(
        self,
        db: Session,
        jira_ticket_task: JiraTicketTask,
        manual_task_instance: ManualTaskInstance,
    ):
        found = JiraTicketTask.get_by_instance_id(db, manual_task_instance.id)
        assert found is not None
        assert found.id == jira_ticket_task.id

    def test_get_by_instance_id_not_found(self, db: Session):
        found = JiraTicketTask.get_by_instance_id(db, "nonexistent")
        assert found is None

    def test_cascade_delete_on_instance(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        jira_connection_config: ConnectionConfig,
    ):
        task = JiraTicketTask.create(
            db=db,
            data={
                "manual_task_instance_id": manual_task_instance.id,
                "connection_config_id": jira_connection_config.id,
            },
        )
        task_id = task.id
        db.delete(manual_task_instance)
        db.commit()

        assert db.query(JiraTicketTask).filter_by(id=task_id).first() is None


# ── Polling Task Tests ───────────────────────────────────────────────


class TestPollJiraTicketsTask:
    def test_poll_task_no_op_without_service(self):
        assert poll_jira_tickets is not None

    def test_register_poll_service(self):
        mock_fn = MagicMock()
        register_poll_service(mock_fn)

        assert polling_task._poll_service_fn is mock_fn

        # Clean up
        polling_task._poll_service_fn = None


# ── Configuration Tests ──────────────────────────────────────────────


class TestJiraPollingConfig:
    def test_default_polling_interval(self):
        assert CONFIG.execution.jira_polling_interval_minutes == 10

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
    ManualTaskConfigurationType,
    ManualTaskInstance,
    ManualTaskType,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask


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

        # Access config (current)
        access_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request.value,
                "is_current": True,
            },
        )

        # Erasure config (current)
        erasure_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.erasure_privacy_request.value,
                "is_current": True,
            },
        )

        yield {
            "connection_config": connection_config,
            "manual_task": manual_task,
            "access_config": access_config,
            "erasure_config": erasure_config,
        }

        # Cleanup
        erasure_config.delete(db)
        access_config.delete(db)
        manual_task.delete(db)
        connection_config.delete(db)

    @pytest.fixture()
    def privacy_request(self, db: Session, policy):
        """Minimal PrivacyRequest for testing."""
        pr = PrivacyRequest.create(
            db=db,
            data={
                "requested_at": datetime.utcnow(),
                "policy_id": policy.id,
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

from datetime import datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.common_exceptions import FidesopsException
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.manual_tasks.manual_task_instance import ManualTaskInstance
from fides.api.models.policy import Policy
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_request import ExecutionLog
from fides.api.models.property import Property
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.oauth.roles import APPROVER
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigurationType,
    ManualTaskFieldType,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
)
from fides.api.schemas.manual_tasks.manual_task_status import StatusType
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import (
    PrivacyRequestCreate,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import Identity
from fides.config.config_proxy import ConfigProxy
from fides.service.manual_tasks.manual_task_service import ManualTaskService
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService
from tests.conftest import wait_for_tasks_to_complete


@pytest.fixture
def mock_messaging_service() -> MessagingService:
    mock_service = create_autospec(MessagingService)
    mock_service.dispatch_message = MagicMock()
    return mock_service


@pytest.fixture
def privacy_request_service(
    db: Session, mock_messaging_service
) -> PrivacyRequestService:
    return PrivacyRequestService(db, ConfigProxy(db), mock_messaging_service)


@pytest.mark.integration
@pytest.mark.integration_postgres
class TestPrivacyRequestService:
    """
    Since these tests actually run the privacy request using the posgres database, we need to
    mark them all as integration tests.
    """

    @pytest.fixture
    def reviewing_user(self, db):
        user = FidesUser.create(
            db=db,
            data={
                "username": "reviewing_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
                "email_address": "fides.user@ethyca.com",
            },
        )
        client = ClientDetail(
            hashed_secret="thisisatest",
            salt="thisisstillatest",
            roles=[APPROVER],
            scopes=[],
            user_id=user.id,
        )

        FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "roles": [APPROVER]}
        )

        db.add(client)
        db.commit()
        db.refresh(client)
        yield user
        try:
            client.delete(db)
            user.delete(db)
        except ObjectDeletedError:
            pass

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures(
        "use_dsr_3_0",
        "postgres_integration_db",
        "automatically_approved",
        "postgres_example_test_dataset_config",
        "allow_custom_privacy_request_field_collection_enabled",
    )
    def test_resubmit_complete_privacy_request(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        mock_messaging_service: MessagingService,
        policy: Policy,
        connection_config: ConnectionConfig,
        property_a: Property,
        reviewing_user: FidesUser,
    ):
        # remove the host from the Postgres example connection
        # to force the privacy request to error
        secrets = connection_config.secrets
        host = secrets.pop("host")
        db.commit()

        external_id = "ext-123"
        requested_at = datetime.now(timezone.utc)
        identity = Identity(email="jane@example.com")
        custom_privacy_request_fields = {
            "first_name": {"label": "First name", "value": "John"}
        }
        policy_key = policy.key
        encryption_key = (
            "fake-key-1234567"  # this is not a real key, but it has to be 16 bytes
        )
        property_id = property_a.id
        source = PrivacyRequestSource.request_manager
        submitted_by = reviewing_user.id

        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                external_id=external_id,
                requested_at=requested_at,
                identity=identity,
                custom_privacy_request_fields=custom_privacy_request_fields,
                policy_key=policy_key,
                encryption_key=encryption_key,
                property_id=property_id,
                source=source,
            ),
            authenticated=True,
            submitted_by=submitted_by,
        )
        privacy_request_id = privacy_request.id

        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() > 0

        # re-add the host to fix the Postgres connection
        connection_config.secrets["host"] = host
        db.commit()

        # resubmit the request and wait for it to complete
        privacy_request = privacy_request_service.resubmit_privacy_request(
            privacy_request.id
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        db.refresh(privacy_request)

        # verify the fields from the original privacy request were copied
        # successfully to the resubmitted privacy request
        assert privacy_request.id == privacy_request_id
        assert privacy_request.status == PrivacyRequestStatus.complete
        assert privacy_request.external_id == external_id
        assert privacy_request.requested_at == requested_at
        assert privacy_request.get_persisted_identity() == identity
        assert (
            privacy_request.get_persisted_custom_privacy_request_fields()
            == custom_privacy_request_fields
        )
        assert privacy_request.policy.key == policy_key
        assert privacy_request.get_cached_encryption_key() == encryption_key
        assert privacy_request.property_id == property_id
        assert privacy_request.source == source
        assert privacy_request.submitted_by == submitted_by

        # verify the approval email was not sent out
        mock_messaging_service.send_request_approved.assert_not_called()

        # verify that the error logs from the original attempt
        # were deleted as part of the re-submission
        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() == 0

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures("automatically_approved")
    def test_cannot_resubmit_complete_privacy_request(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                identity=Identity(email="user@example.com"),
                policy_key=policy.key,
            ),
            authenticated=True,
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)

        with pytest.raises(FidesopsException) as exc:
            privacy_request_service.resubmit_privacy_request(privacy_request.id)
        assert "Cannot resubmit a complete privacy request" in str(exc)

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures("require_manual_request_approval")
    def test_cannot_resubmit_pending_privacy_request(
        self,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                identity=Identity(email="user@example.com"),
                policy_key=policy.key,
            ),
            authenticated=True,
        )

        with pytest.raises(FidesopsException) as exc:
            privacy_request_service.resubmit_privacy_request(privacy_request.id)
        assert "Cannot resubmit a pending privacy request" in str(exc)

    def test_cannot_resubmit_non_existent_privacy_request(
        self,
        privacy_request_service: PrivacyRequestService,
    ):
        assert privacy_request_service.resubmit_privacy_request("123") is None

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures(
        "use_dsr_3_0",
        "postgres_integration_db",
        "require_manual_request_approval",
        "postgres_example_test_dataset_config",
    )
    def test_resubmit_does_not_approve_request_if_webhooks(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        mock_messaging_service: MessagingService,
        policy: Policy,
        connection_config: ConnectionConfig,
        property_a: Property,
        reviewing_user: FidesUser,
        pre_approval_webhooks: list[PreApprovalWebhook],
    ):
        """
        Test that resubmit does not automatically approve the request if require_manual_request_approval
        is True and there's PreApproval webhooks created
        """
        # remove the host from the Postgres example connection
        # to force the privacy request to error
        secrets = connection_config.secrets
        host = secrets.pop("host")

        db.commit()

        external_id = "ext-123"
        requested_at = datetime.now(timezone.utc)
        identity = Identity(email="jane@example.com")
        custom_privacy_request_fields = {
            "first_name": {"label": "First name", "value": "John"}
        }
        policy_key = policy.key
        encryption_key = (
            "fake-key-1234567"  # this is not a real key, but it has to be 16 bytes
        )
        property_id = property_a.id
        source = PrivacyRequestSource.request_manager
        submitted_by = reviewing_user.id

        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                external_id=external_id,
                requested_at=requested_at,
                identity=identity,
                custom_privacy_request_fields=custom_privacy_request_fields,
                policy_key=policy_key,
                encryption_key=encryption_key,
                property_id=property_id,
                source=source,
            ),
            authenticated=True,
            submitted_by=submitted_by,
        )
        # Manually approve it
        privacy_request_service.approve_privacy_requests(
            request_ids=[privacy_request.id], suppress_notification=True
        )
        privacy_request_id = privacy_request.id

        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        db.refresh(privacy_request)

        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() > 0

        # re-add the host to fix the Postgres connection
        connection_config.secrets["host"] = host
        db.commit()

        # resubmit the request and wait for it to complete
        privacy_request = privacy_request_service.resubmit_privacy_request(
            privacy_request.id
        )
        db.refresh(privacy_request)

        # Check that privacy request is still pending
        assert privacy_request.id == privacy_request_id
        assert privacy_request.status == PrivacyRequestStatus.pending

        # verify that the error logs from the original attempt
        # were deleted as part of the re-submission
        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() == 0

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures(
        "use_dsr_3_0",
        "postgres_integration_db",
        "require_manual_request_approval",
        "postgres_example_test_dataset_config",
    )
    def test_resubmit_automatically_approves_request_if_no_webhooks(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        mock_messaging_service: MessagingService,
        policy: Policy,
        connection_config: ConnectionConfig,
        property_a: Property,
        reviewing_user: FidesUser,
    ):
        """
        Test that resubmit does not automatically approve the request if require_manual_request_approval
        is True and there's PreApproval webhooks created
        """
        # remove the host from the Postgres example connection
        # to force the privacy request to error
        secrets = connection_config.secrets
        host = secrets.pop("host")

        db.commit()

        external_id = "ext-123"
        requested_at = datetime.now(timezone.utc)
        identity = Identity(email="jane@example.com")
        custom_privacy_request_fields = {
            "first_name": {"label": "First name", "value": "John"}
        }
        policy_key = policy.key
        encryption_key = (
            "fake-key-1234567"  # this is not a real key, but it has to be 16 bytes
        )
        property_id = property_a.id
        source = PrivacyRequestSource.request_manager
        submitted_by = reviewing_user.id

        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                external_id=external_id,
                requested_at=requested_at,
                identity=identity,
                custom_privacy_request_fields=custom_privacy_request_fields,
                policy_key=policy_key,
                encryption_key=encryption_key,
                property_id=property_id,
                source=source,
            ),
            authenticated=True,
            submitted_by=submitted_by,
        )
        # Manually approve it
        privacy_request_service.approve_privacy_requests(
            request_ids=[privacy_request.id],
            suppress_notification=True,
        )
        privacy_request_id = privacy_request.id

        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        db.refresh(privacy_request)

        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() > 0

        # re-add the host to fix the Postgres connection
        connection_config.secrets["host"] = host
        db.commit()

        # resubmit the request and wait for it to complete
        privacy_request = privacy_request_service.resubmit_privacy_request(
            privacy_request.id
        )
        db.refresh(privacy_request)

        # Check that privacy request is complete and fields were copied properly
        assert privacy_request.id == privacy_request_id
        assert privacy_request.status == PrivacyRequestStatus.complete
        assert privacy_request.external_id == external_id
        assert privacy_request.requested_at == requested_at
        assert privacy_request.get_persisted_identity() == identity
        assert (
            privacy_request.get_persisted_custom_privacy_request_fields()
            == custom_privacy_request_fields
        )
        assert privacy_request.policy.key == policy_key
        assert privacy_request.get_cached_encryption_key() == encryption_key
        assert privacy_request.property_id == property_id
        assert privacy_request.source == source
        assert privacy_request.submitted_by == submitted_by

        # verify the approval email was not sent out
        mock_messaging_service.send_request_approved.assert_not_called()

        # verify that the error logs from the original attempt
        # were deleted as part of the re-submission
        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() == 0


@pytest.mark.integration
@pytest.mark.integration_postgres
class TestPrivacyRequestServiceManualTasks:
    @pytest.fixture
    def manual_task_service(self, db: Session) -> ManualTaskService:
        return ManualTaskService(db)

    @pytest.fixture
    def manual_task(
        self, db: Session, connection_config: ConnectionConfig
    ) -> Generator[ManualTask, None, None]:
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": "privacy_request",
                "parent_entity_id": connection_config.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )
        yield manual_task
        manual_task.delete(db)

    @pytest.fixture
    def manual_task_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ) -> Generator[ManualTaskConfig, None, None]:
        fields = [
            {
                "field_key": "field1",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "Field 1",
                    "required": True,
                    "help_text": "This is field 1",
                    "placeholder": "Enter text here",
                },
            },
        ]
        config = manual_task_service.create_config(
            ManualTaskConfigurationType.access_privacy_request, fields, manual_task.id
        )
        yield config
        config.delete(db)

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    def test_create_privacy_request_creates_manual_task_instance(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
        connection_config: ConnectionConfig,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ) -> None:
        """Test that creating a privacy request creates a manual task instance if a manual task exists."""

        # Create privacy request
        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                policy_key=policy.key,
                identity=Identity(email="test@example.com"),
                connection_config_id=connection_config.id,
            ),
            authenticated=True,
        )

        # Verify manual task instance was created
        manual_task_instance = ManualTaskInstance.filter(
            db=db,
            conditions=(
                (ManualTaskInstance.task_id == manual_task.id)
                & (ManualTaskInstance.config_id == manual_task_config.id)
                & (ManualTaskInstance.entity_id == privacy_request.id)
                & (ManualTaskInstance.entity_type == "privacy_request")
            ),
        ).first()

        assert manual_task_instance is not None
        assert manual_task_instance.status == StatusType.pending

        # Cleanup
        manual_task_instance.delete(db)
        privacy_request.delete(db)

    def test_create_manual_task_instances_no_tasks(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ) -> None:
        """Test creating manual task instances when no manual tasks exist."""
        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                policy_key=policy.key,
                identity=Identity(email="test@example.com"),
            ),
            authenticated=True,
        )

        # Verify no manual task instances were created
        manual_task_instances = ManualTaskInstance.filter(
            db=db,
            conditions=(ManualTaskInstance.entity_id == privacy_request.id),
        ).all()
        assert len(manual_task_instances) == 0

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures(
        "connection_config",
        "manual_task_config",
        "use_dsr_3_0",
    )
    def test_send_manual_task_notifications_with_assigned_users(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
        user: FidesUser,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ) -> None:
        """Test sending notifications when users are assigned to the task."""
        manual_task_service.assign_users_to_task(manual_task.id, [user.id])

        with (
            patch(
                "fides.service.privacy_request.privacy_request_service.get_email_messaging_config_service_type",
                return_value=MessagingServiceType.mailgun.value,
            ),
            patch(
                "fides.service.privacy_request.privacy_request_service.dispatch_message"
            ) as mock_dispatch,
        ):
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    policy_key=policy.key,
                    identity=Identity(email="test@example.com"),
                ),
                authenticated=True,
            )

            # Verify that dispatch_message was called with correct parameters
            mock_dispatch.assert_called_once_with(
                db=db,
                action_type=MessagingActionType.TEST_MESSAGE,
                to_identity=Identity(email=user.email_address),
                service_type=MessagingServiceType.mailgun.value,
                message_body_params=None,
                subject_override=f"New access manual task assigned - Privacy Request {privacy_request.id}",
            )
            privacy_request.delete(db)

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures("connection_config", "manual_task_config")
    def test_send_manual_task_notifications_no_assigned_users(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ) -> None:
        """Test sending notifications when no users are assigned to the task."""
        with (
            patch(
                "fides.service.privacy_request.privacy_request_service.get_email_messaging_config_service_type",
                return_value=MessagingServiceType.mailgun.value,
            ),
            patch(
                "fides.service.privacy_request.privacy_request_service.dispatch_message"
            ) as mock_dispatch,
        ):
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    policy_key=policy.key,
                    identity=Identity(email="requester@example.com"),
                ),
                authenticated=True,
            )

        # Verify that no messages were sent
        mock_dispatch.assert_not_called()

        privacy_request.delete(db)

    @pytest.mark.usefixtures("use_dsr_3_0", "manual_task_config")
    def test_send_manual_task_notifications_no_email_service(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
        manual_task: ManualTask,
        user: FidesUser,
        manual_task_service: ManualTaskService,
    ) -> None:
        """Test sending notifications when no email service is configured."""
        # Create a user and assign to manual task
        manual_task_service.assign_users_to_task(manual_task.id, [user.id])
        with patch(
            "fides.service.privacy_request.privacy_request_service.dispatch_message"
        ) as mock_dispatch:
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    policy_key=policy.key,
                    identity=Identity(email="requester@example.com"),
                ),
                authenticated=True,
            )

            # Verify that no messages were sent
            mock_dispatch.assert_not_called()

        # Cleanup
        privacy_request.delete(db)

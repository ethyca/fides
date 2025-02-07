from datetime import datetime, timezone
from unittest.mock import create_autospec

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.common_exceptions import FidesopsException
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.models.property import Property
from fides.api.oauth.roles import APPROVER
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestCreate
from fides.api.schemas.redis_cache import Identity
from fides.config.config_proxy import ConfigProxy
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService
from tests.conftest import wait_for_tasks_to_complete


class TestPrivacyRequestService:
    @pytest.fixture
    def mock_messaging_service(self) -> MessagingService:
        return create_autospec(MessagingService)

    @pytest.fixture
    def privacy_request_service(
        self, db: Session, mock_messaging_service
    ) -> PrivacyRequestService:
        return PrivacyRequestService(db, ConfigProxy(db), mock_messaging_service)

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
        encryption_key = "thisisnotarealkey"
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

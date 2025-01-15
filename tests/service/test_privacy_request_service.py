from unittest.mock import create_autospec

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequestStatus,
)
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
    ):
        # remove the host from the Postgres example connection
        # to force the privacy request to error
        secrets = connection_config.secrets
        host = secrets.pop("host")
        db.commit()

        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                identity=Identity(email="jane@example.com"),
                policy_key=policy.key,
            ),
            authenticated=True,
        )

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
        assert privacy_request.status == PrivacyRequestStatus.complete
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

        with pytest.raises(FidesopsException):
            privacy_request_service.resubmit_privacy_request(privacy_request.id)

    def test_cannot_resubmit_non_existent_privacy_request(
        self,
        privacy_request_service: PrivacyRequestService,
    ):
        assert privacy_request_service.resubmit_privacy_request("123") is None

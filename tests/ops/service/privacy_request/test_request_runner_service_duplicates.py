from datetime import datetime, timezone
from unittest import mock

import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from tests.ops.service.privacy_request.conftest import (
    create_duplicate_requests,
    get_detection_config,
)

PRIVACY_REQUEST_TASK_TIMEOUT = 5


@pytest.fixture
def mock_config_proxy():
    """Mock config proxy with privacy center URL"""
    with mock.patch(
        "fides.api.service.privacy_request.request_runner_service.ConfigProxy"
    ) as mock_proxy:
        mock_config = mock.MagicMock()
        mock_config.privacy_request_duplicate_detection = get_detection_config(
            match_identity_fields=["email"]
        )
        mock_proxy.return_value = mock_config
        yield mock_config


def test_request_runner_service_duplicates(
    db: Session,
    run_privacy_request_task,
    privacy_request_with_email_identity: PrivacyRequest,
    loguru_caplog,
    mock_config_proxy,
):
    """Test that the request runner service identifies and marks duplicate privacy requests."""
    with mock_config_proxy:
        run_privacy_request_task.delay(privacy_request_with_email_identity.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        assert (
            privacy_request_with_email_identity.status != PrivacyRequestStatus.duplicate
        )

        duplicate_request = create_duplicate_requests(
            db,
            privacy_request_with_email_identity.policy,
            1,
            PrivacyRequestStatus.in_processing,
        )[0]
        run_privacy_request_task.delay(duplicate_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(duplicate_request)
        assert duplicate_request.status == PrivacyRequestStatus.duplicate

        assert (
            "Terminating privacy request: request is a duplicate." in loguru_caplog.text
        )


def test_request_runner_service_verified_identity_duplicates(
    db: Session,
    run_privacy_request_task,
    privacy_request_with_email_identity: PrivacyRequest,
    loguru_caplog,
    mock_config_proxy,
):
    """Test that the request runner service identifies and marks duplicate privacy requests with verified identities."""
    privacy_request_with_email_identity.update(
        db=db, data={"identity_verified_at": None}
    )
    duplicate_request = create_duplicate_requests(
        db,
        privacy_request_with_email_identity.policy,
        1,
        PrivacyRequestStatus.in_processing,
    )[0]
    duplicate_request.update(
        db=db, data={"identity_verified_at": datetime.now(timezone.utc)}
    )
    with mock_config_proxy:
        run_privacy_request_task.delay(privacy_request_with_email_identity.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request_with_email_identity)
        assert (
            privacy_request_with_email_identity.status == PrivacyRequestStatus.duplicate
        )

        run_privacy_request_task.delay(duplicate_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(duplicate_request)
        assert duplicate_request.status != PrivacyRequestStatus.duplicate

        # Set as verified (after the other request)
        privacy_request_with_email_identity.update(
            db=db, data={"identity_verified_at": datetime.now(timezone.utc)}
        )
        run_privacy_request_task.delay(privacy_request_with_email_identity.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        assert (
            privacy_request_with_email_identity.status == PrivacyRequestStatus.duplicate
        )


def test_request_runner_service_actioned_duplicates(
    db: Session,
    run_privacy_request_task,
    privacy_request_with_email_identity: PrivacyRequest,
    loguru_caplog,
    mock_config_proxy,
):
    """Test that the request runner service identifies and marks duplicate privacy requests with actioned identities."""
    privacy_request_with_email_identity.update(
        db=db, data={"status": PrivacyRequestStatus.approved}
    )
    with mock_config_proxy:
        run_privacy_request_task.delay(privacy_request_with_email_identity.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        assert (
            privacy_request_with_email_identity.status != PrivacyRequestStatus.duplicate
        )

        duplicate_request = create_duplicate_requests(
            db,
            privacy_request_with_email_identity.policy,
            1,
            PrivacyRequestStatus.in_processing,
        )[0]
        run_privacy_request_task.delay(duplicate_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(duplicate_request)
        assert duplicate_request.status == PrivacyRequestStatus.duplicate

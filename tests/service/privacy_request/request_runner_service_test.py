from unittest import mock
from unittest.mock import Mock

from sqlalchemy.orm import Session

from fidesops.models.privacy_request import PrivacyRequest
from fidesops.service.privacy_request.request_runner_service import PrivacyRequestRunner


@mock.patch(
    "fidesops.service.privacy_request.request_runner_service.run_access_request"
)
@mock.patch("fidesops.service.privacy_request.request_runner_service.upload")
def test_policy_upload_called(
    upload_mock: Mock,
    run_access_request_mock: Mock,
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    privacy_request_runner.run()
    assert privacy_request.finished_processing_at is not None
    assert upload_mock.called
    assert run_access_request_mock.called


def test_start_processing_sets_started_processing_at(
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    privacy_request.started_processing_at = None
    privacy_request_runner.start_processing(db=db)
    assert privacy_request.started_processing_at is not None


def test_start_processing_doesnt_overwrite_started_processing_at(
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    before = privacy_request.started_processing_at
    privacy_request_runner.start_processing(db=db)
    assert privacy_request.started_processing_at == before

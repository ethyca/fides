from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest import mock

import pytest
from sqlalchemy.orm import Session

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.privacy_request import PrivacyRequestCreate, PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.service.privacy_request.duplication_detection import (
    DuplicateDetectionService,
)
from fides.api.task.conditional_dependencies.schemas import ConditionGroup
from fides.config.duplicate_detection_settings import DuplicateDetectionSettings
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService

PRIVACY_REQUEST_TASK_TIMEOUT = 5


# Helper function to get a detection config with default values
def get_detection_config(
    time_window_days: int = 30, match_identity_fields: list[str] = ["email"]
) -> DuplicateDetectionSettings:
    return DuplicateDetectionSettings(
        enabled=True,
        time_window_days=time_window_days,
        match_identity_fields=match_identity_fields,
    )


@pytest.fixture
def mock_config_proxy():
    """Mock config proxy with privacy center URL"""
    with mock.patch(
        "fides.api.service.privacy_request.duplication_detection.ConfigProxy"
    ) as mock_proxy:
        mock_config = mock.MagicMock()
        mock_config.privacy_request_duplicate_detection = get_detection_config()
        mock_proxy.return_value = mock_config
        yield mock_config


@pytest.fixture
def duplicate_detection_service(db: Session) -> DuplicateDetectionService:
    service = DuplicateDetectionService(db)
    service._config = get_detection_config()
    return service


@pytest.fixture
def privacy_request_with_multiple_identities(
    db: Session,
    privacy_request_with_email_identity: PrivacyRequest,
) -> Generator[PrivacyRequest, None, None]:
    """Privacy request with email and phone_number identities."""
    privacy_request_with_email_identity.persist_identity(
        db=db,
        identity=Identity(email="customer-1@example.com", phone_number="+15555555555"),
    )
    return privacy_request_with_email_identity


@pytest.fixture
def old_privacy_request_with_email(
    db: Session,
    policy: Policy,
) -> Generator[PrivacyRequest, None, None]:
    """Privacy request created 40 days ago with email identity."""
    old_date = datetime.now(timezone.utc) - timedelta(days=40)
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": "test_external_id_old",
            "started_processing_at": old_date,
            "requested_at": old_date,
            "status": PrivacyRequestStatus.in_processing,
            "policy_id": policy.id,
        },
    )
    # Manually update created_at since it's auto-set
    privacy_request.update(db, data={"created_at": old_date})
    privacy_request.persist_identity(
        db=db,
        identity=Identity(email="customer-1@example.com"),
    )
    return privacy_request


# Helper function to create duplicate requests
def create_duplicate_requests(
    db: Session, policy: Policy, count: int, status: PrivacyRequestStatus
) -> list[PrivacyRequest]:
    duplicate_requests = []
    for i in range(count):
        duplicate_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"test_external_id_duplicate_{i}",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.now(timezone.utc),
                "status": status,
                "policy_id": policy.id,
            },
        )
        duplicate_request.persist_identity(
            db=db,
            identity=Identity(email="customer-1@example.com"),
        )
        duplicate_requests.append(duplicate_request)
    return duplicate_requests


class TestCreateDuplicateDetectionConditions:
    """Tests for create_duplicate_detection_conditions function."""

    def test_create_conditions_single_identity_field(
        self, duplicate_detection_service, privacy_request_with_email_identity
    ):
        """Test creating conditions with single identity field returns expected structure."""
        conditions = duplicate_detection_service.create_duplicate_detection_conditions(
            privacy_request_with_email_identity
        )

        assert conditions is not None
        assert isinstance(conditions, ConditionGroup)
        assert (
            len(conditions.conditions) == 3
        )  # identity condition, policy condition & time window condition

    def test_create_conditions_multiple_identity_fields(
        self, duplicate_detection_service, privacy_request_with_multiple_identities
    ):
        """Test creating conditions with multiple identity fields returns expected structure."""
        duplicate_detection_service._config = get_detection_config(
            match_identity_fields=["email", "phone_number"]
        )
        conditions = duplicate_detection_service.create_duplicate_detection_conditions(
            privacy_request_with_multiple_identities
        )
        assert conditions is not None
        assert isinstance(conditions, ConditionGroup)
        assert (
            len(conditions.conditions) == 4
        )  # identity conditions, policy condition & time window condition

    @pytest.mark.parametrize(
        "match_identity_fields",
        [
            pytest.param(["phone_number"], id="no_matching_identity_field"),
            pytest.param([], id="empty_match_identity_fields"),
            pytest.param(
                ["email", "phone_number"], id="multiple_identity_fields_no_match"
            ),
        ],
    )
    def test_create_conditions_no_matching_identities(
        self,
        duplicate_detection_service,
        privacy_request_with_email_identity,
        match_identity_fields,
    ):
        """Test returns None when request has no identities matching configured fields."""
        duplicate_detection_service._config = get_detection_config(
            match_identity_fields=match_identity_fields
        )
        conditions = duplicate_detection_service.create_duplicate_detection_conditions(
            privacy_request_with_email_identity
        )
        assert conditions is None


class TestFindDuplicatePrivacyRequests:
    """Tests for find_duplicate_privacy_requests function."""

    @pytest.mark.parametrize("duplicate_count", [1, 3])
    def test_find_duplicates_within_time_window(
        self,
        db,
        duplicate_detection_service,
        privacy_request_with_email_identity,
        policy,
        duplicate_count,
    ):
        """Test finding duplicate request within time window with matching identity."""
        duplicate_requests = create_duplicate_requests(
            db, policy, duplicate_count, PrivacyRequestStatus.in_processing
        )
        duplicate_ids = [duplicate.id for duplicate in duplicate_requests]
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity
        )

        assert len(duplicates) == duplicate_count
        assert all(duplicate.id in duplicate_ids for duplicate in duplicates)

    @pytest.mark.usefixtures("old_privacy_request_with_email")
    def test_no_duplicates_outside_time_window(
        self,
        duplicate_detection_service,
        privacy_request_with_email_identity,
    ):
        """Test that requests outside time window are not returned as duplicates."""
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity
        )

        assert len(duplicates) == 0

    def test_find_duplicate_with_extended_time_window(
        self,
        duplicate_detection_service,
        privacy_request_with_email_identity,
        old_privacy_request_with_email,
    ):
        """Test finding duplicate when extending time window to include older requests."""
        duplicate_detection_service._config = get_detection_config(time_window_days=60)
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity
        )

        assert len(duplicates) == 1
        assert duplicates[0].id == old_privacy_request_with_email.id

    def test_no_duplicates_different_identity_value(
        self,
        db,
        duplicate_detection_service,
        privacy_request_with_email_identity,
        policy,
    ):
        """Test that requests with different identity values are not returned."""
        different_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_external_id_different",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.now(timezone.utc),
                "status": PrivacyRequestStatus.in_processing,
                "policy_id": policy.id,
            },
        )
        different_request.persist_identity(
            db=db,
            identity=Identity(email="different@example.com"),
        )

        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity
        )

        assert len(duplicates) == 0

    def test_no_duplicates_with_unmatched_identity_field(
        self, duplicate_detection_service, privacy_request_with_email_identity
    ):
        """Test returns empty list when config specifies unmatched identity fields."""
        duplicate_detection_service._config = get_detection_config(
            match_identity_fields=["phone_number"]
        )
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity
        )

        assert len(duplicates) == 0

    def test_current_request_excluded_from_results(
        self,
        duplicate_detection_service,
        privacy_request_with_email_identity,
    ):
        """Test that the current request itself is excluded from duplicate results."""
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity
        )

        for duplicate in duplicates:
            assert duplicate.id != privacy_request_with_email_identity.id

    def test_find_duplicate_with_multiple_identity_fields(
        self,
        db,
        duplicate_detection_service,
        privacy_request_with_multiple_identities,
        policy,
    ):
        """Test finding duplicates when matching on multiple identity fields."""
        duplicate_detection_service._config = get_detection_config(
            time_window_days=365, match_identity_fields=["email", "phone_number"]
        )
        duplicate_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_external_id_multi_dup",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.now(timezone.utc),
                "status": PrivacyRequestStatus.in_processing,
                "policy_id": policy.id,
            },
        )
        duplicate_request.persist_identity(
            db=db,
            identity=Identity(
                email="customer-1@example.com", phone_number="+15555555555"
            ),
        )

        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_multiple_identities
        )

        assert len(duplicates) == 1
        assert duplicates[0].id == duplicate_request.id

    def test_partial_identity_match_not_returned(
        self,
        db,
        duplicate_detection_service,
        privacy_request_with_multiple_identities,
        policy,
    ):
        """Test that request with only partial identity match is not returned as duplicate."""
        duplicate_detection_service._config = get_detection_config(
            time_window_days=365, match_identity_fields=["email", "phone_number"]
        )
        partial_match_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_external_id_partial",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.now(timezone.utc),
                "status": PrivacyRequestStatus.in_processing,
                "policy_id": policy.id,
            },
        )
        # Only matching email, different phone_number
        partial_match_request.persist_identity(
            db=db,
            identity=Identity(
                email="customer-1@example.com", phone_number="+19999999999"
            ),
        )

        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_multiple_identities
        )

        assert len(duplicates) == 0

    def test_requests_from_different_policy_id_not_returned(
        self,
        db,
        duplicate_detection_service,
        privacy_request_with_email_identity,
        erasure_policy: Policy,
    ):
        """Test that requests from different policies are not returned as duplicates."""
        erasure_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_external_id_erasure",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.now(timezone.utc),
                "status": PrivacyRequestStatus.in_processing,
                "policy_id": erasure_policy.id,
            },
        )
        erasure_request.persist_identity(
            db=db,
            identity=Identity(email="customer-1@example.com"),
        )

        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity
        )
        assert len(duplicates) == 0


class TestDuplicateRequestFunctionality:
    """Tests for is_canonical_request function."""

    def test_consent_request_is_not_duplicate(
        self, db, duplicate_detection_service, consent_policy
    ):
        """Test that a consent requests are not considered duplicates."""
        duplicate_requests = create_duplicate_requests(
            db, consent_policy, 3, PrivacyRequestStatus.pending
        )
        for duplicate_request in duplicate_requests:
            duplicate_request.persist_identity(
                db=db,
                identity=Identity(email="customer-1@example.com"),
            )
            is_duplicate = duplicate_detection_service.is_duplicate_request(
                duplicate_request
            )
            assert not is_duplicate

    def test_is_duplicate_request_single_request(
        self, duplicate_detection_service, privacy_request_with_email_identity
    ):
        """Test that a single request is the canonical request."""
        is_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_email_identity
        )
        assert not is_duplicate

    @pytest.mark.parametrize(
        "request_status, duplicate_status",
        [
            pytest.param(
                PrivacyRequestStatus.identity_unverified,
                PrivacyRequestStatus.identity_unverified,
                id="all_unverified_identity_first_request_is_canonical",
            ),
            pytest.param(
                PrivacyRequestStatus.pending,
                PrivacyRequestStatus.identity_unverified,
                id="only_verified_request_is_canonical",
            ),
            pytest.param(
                PrivacyRequestStatus.pending,
                PrivacyRequestStatus.pending,
                id="first_created_verified_identity_request_is_canonical",
            ),
            pytest.param(
                PrivacyRequestStatus.identity_unverified,
                PrivacyRequestStatus.duplicate,
                id="unverified_request_is_canonical_if_all_duplicates_status",
            ),
        ],
    )
    def test_is_duplicate_hierarchy_decisions_returns_false(
        self,
        db,
        duplicate_detection_service,
        privacy_request_with_email_identity,
        policy,
        request_status,
        duplicate_status,
    ):
        """Test that a first unverified request is the canonical request."""
        update_data = {
            "status": request_status,
        }
        if request_status != PrivacyRequestStatus.identity_unverified:
            update_data["identity_verified_at"] = datetime.now(timezone.utc)
        privacy_request_with_email_identity.update(db=db, data=update_data)

        duplicate_requests = create_duplicate_requests(db, policy, 3, duplicate_status)
        if duplicate_status != PrivacyRequestStatus.identity_unverified:
            for duplicate_request in duplicate_requests:
                duplicate_request.update(
                    db=db,
                    data={"identity_verified_at": datetime.now(timezone.utc)},
                )

        assert not duplicate_detection_service.is_duplicate_request(
            privacy_request_with_email_identity
        )
        assert (
            privacy_request_with_email_identity.duplicate_request_group_id is not None
        )
        for duplicate_request in duplicate_requests:
            assert duplicate_detection_service.is_duplicate_request(duplicate_request)
            assert (
                duplicate_request.duplicate_request_group_id
                == privacy_request_with_email_identity.duplicate_request_group_id
            )

    def test_duplicate_request_group_id_for_different_configs(
        self,
        db,
        duplicate_detection_service,
        privacy_request_with_email_identity,
        policy,
    ):
        """Test that the duplicate request group id is different for different duplicate detection configurations."""
        privacy_request_with_email_identity.update(
            db=db, data={"status": PrivacyRequestStatus.pending}
        )
        email_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_email_identity
        )
        assert not email_duplicate

        duplicate_request_with_multiple_identities = create_duplicate_requests(
            db, policy, 1, PrivacyRequestStatus.pending
        )[0]
        duplicate_request_with_multiple_identities.persist_identity(
            db=db,
            identity=Identity(
                email="customer-1@example.com", phone_number="+15555555555"
            ),
        )

        multiple_identity_duplicate = duplicate_detection_service.is_duplicate_request(
            duplicate_request_with_multiple_identities
        )
        assert multiple_identity_duplicate
        # This group should be the same for both requests since they have the same dedup key
        assert (
            privacy_request_with_email_identity.duplicate_request_group_id
            == duplicate_request_with_multiple_identities.duplicate_request_group_id
        )

        original_group_id = (
            privacy_request_with_email_identity.duplicate_request_group_id
        )
        duplicate_detection_service._config = get_detection_config(
            match_identity_fields=["email", "phone_number"]
        )
        email_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_email_identity
        )
        assert (
            not email_duplicate
        )  # This request is not a duplicate since it only has an email identity
        multiple_identity_duplicate = duplicate_detection_service.is_duplicate_request(
            duplicate_request_with_multiple_identities
        )
        assert not multiple_identity_duplicate  # This request is not a duplicate since it has both an email and phone number identity and is the first
        assert (
            privacy_request_with_email_identity.duplicate_request_group_id
            != duplicate_request_with_multiple_identities.duplicate_request_group_id
        )

        # This group should not be the same for both requests since the first request only has an email identity
        assert (
            privacy_request_with_email_identity.duplicate_request_group_id
            != duplicate_request_with_multiple_identities.duplicate_request_group_id
        )
        assert (
            privacy_request_with_email_identity.duplicate_request_group_id
            == original_group_id
        )

    def test_duplicate_request_group_returns_none_is_false(
        self,
        duplicate_detection_service,
        privacy_request_with_email_identity,
    ):
        """Test that the duplicate request group returns None if the request is not a duplicate."""
        with mock.patch(
            "fides.api.service.privacy_request.duplication_detection.DuplicateGroup.get_or_create"
        ) as mock_get_or_create:
            mock_get_or_create.return_value = None, None
            is_duplicate = duplicate_detection_service.is_duplicate_request(
                privacy_request_with_email_identity
            )
            assert not is_duplicate
            assert (
                privacy_request_with_email_identity.duplicate_request_group_id is None
            )

    def test_duplicate_request_group_updated_config(
        self, db, duplicate_detection_service, privacy_request_with_multiple_identities
    ):
        """Test that the duplicate request group is updated when the duplicate detection configuration is updated."""
        # First run with original config to set the group id
        privacy_request_with_multiple_identities.update(
            db=db, data={"status": PrivacyRequestStatus.in_processing}
        )
        is_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_multiple_identities
        )
        assert not is_duplicate
        group_id = privacy_request_with_multiple_identities.duplicate_request_group_id
        assert group_id is not None

        # Create a duplicate request with only an email identity - should be duplicates under first config
        duplicates = create_duplicate_requests(
            db,
            privacy_request_with_multiple_identities.policy,
            1,
            PrivacyRequestStatus.pending,
        )
        for duplicate in duplicates:
            duplicate.persist_identity(
                db=db,
                identity=Identity(email="customer-1@example.com"),
            )
            is_duplicate = duplicate_detection_service.is_duplicate_request(duplicate)
            assert is_duplicate
            assert duplicate.duplicate_request_group_id is not None
            assert duplicate.duplicate_request_group_id == group_id

        # Now run with updated config to ensure the group id is updated
        duplicate_detection_service._config = get_detection_config(
            match_identity_fields=["email", "phone_number"]
        )
        is_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_multiple_identities
        )
        assert not is_duplicate
        new_group_id = (
            privacy_request_with_multiple_identities.duplicate_request_group_id
        )
        assert new_group_id != group_id
        assert new_group_id != None
        # verify group is not updated for duplicates becasue they do not match under updated config
        for duplicate in duplicates:
            assert duplicate.duplicate_request_group_id is not None
            assert duplicate.duplicate_request_group_id == group_id

        # add the phone number identity to the duplicates to make them match under updated config
        for duplicate in duplicates:
            duplicate.persist_identity(
                db=db,
                identity=Identity(
                    email="customer-1@example.com", phone_number="+15555555555"
                ),
            )
        is_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_multiple_identities
        )
        assert not is_duplicate
        # group id for original request should not have changed because it matches under updated config
        assert (
            privacy_request_with_multiple_identities.duplicate_request_group_id
            == new_group_id
        )
        # group id for duplicates should have changed because they now match under updated config
        for duplicate in duplicates:
            assert duplicate.duplicate_request_group_id is not None
            assert duplicate.duplicate_request_group_id == new_group_id


class TestDuplicateRequestRunnerService:
    @pytest.mark.parametrize(
        "request_verified_at, duplicate_verified_at, expected_status",
        [
            pytest.param(
                None,
                None,
                PrivacyRequestStatus.duplicate,
                id="requests_not_verified_but_created_first",
            ),
            pytest.param(
                datetime.now(timezone.utc),
                None,
                PrivacyRequestStatus.duplicate,
                id="request_verified_but_not_duplicates",
            ),
            pytest.param(
                None,
                datetime.now(timezone.utc),
                PrivacyRequestStatus.complete,
                id="duplicate_verified_but_not_request",
            ),
            pytest.param(
                datetime.now(timezone.utc),
                datetime.now(timezone.utc) - timedelta(days=1),
                PrivacyRequestStatus.complete,
                id="both_verified_duplicate_verified_first",
            ),
            pytest.param(
                datetime.now(timezone.utc) - timedelta(days=1),
                datetime.now(timezone.utc),
                PrivacyRequestStatus.duplicate,
                id="both_verified_request_verified_first",
            ),
        ],
    )
    def test_request_runner_service_duplicates_all_verified_cases(
        self,
        db: Session,
        run_privacy_request_task,
        privacy_request_with_email_identity: PrivacyRequest,
        request_verified_at,
        duplicate_verified_at,
        expected_status,
        loguru_caplog,
        mock_config_proxy,
    ):
        """Test that the request runner service identifies and marks duplicate privacy requests."""
        with mock_config_proxy:
            privacy_request_with_email_identity.update(
                db=db,
                data={
                    "status": PrivacyRequestStatus.pending,
                    "identity_verified_at": request_verified_at,
                },
            )
            duplicate_request = create_duplicate_requests(
                db,
                privacy_request_with_email_identity.policy,
                1,
                PrivacyRequestStatus.pending,
            )[0]

            duplicate_request.update(
                db=db, data={"identity_verified_at": duplicate_verified_at}
            )
            run_privacy_request_task.delay(duplicate_request.id).get(
                timeout=PRIVACY_REQUEST_TASK_TIMEOUT
            )
            db.refresh(duplicate_request)
            assert duplicate_request.status == expected_status
            if expected_status == PrivacyRequestStatus.duplicate:
                skipped_log = duplicate_request.execution_logs.filter_by(
                    status=ExecutionLogStatus.skipped
                ).first()
                assert skipped_log is not None
                assert (
                    skipped_log.message
                    == f"Request {duplicate_request.id} is a duplicate: it is duplicating request(s) ['{privacy_request_with_email_identity.id}']."
                )

                assert (
                    "Terminating privacy request: request is a duplicate."
                    in loguru_caplog.text
                )
            run_privacy_request_task.delay(privacy_request_with_email_identity.id).get(
                timeout=PRIVACY_REQUEST_TASK_TIMEOUT
            )
            db.refresh(privacy_request_with_email_identity)
            assert privacy_request_with_email_identity.status != expected_status

    def test_request_runner_service_actioned_duplicates(
        self,
        db: Session,
        run_privacy_request_task,
        privacy_request_with_email_identity: PrivacyRequest,
        mock_config_proxy,
    ):
        """Test that the request runner service identifies and marks duplicate privacy requests with actioned identities."""
        with mock_config_proxy:
            run_privacy_request_task.delay(privacy_request_with_email_identity.id).get(
                timeout=PRIVACY_REQUEST_TASK_TIMEOUT
            )
            assert (
                privacy_request_with_email_identity.status
                != PrivacyRequestStatus.duplicate
            )

            privacy_request_with_email_identity.update(
                db=db, data={"status": PrivacyRequestStatus.approved}
            )
            db.refresh(privacy_request_with_email_identity)
            duplicate_request = create_duplicate_requests(
                db,
                privacy_request_with_email_identity.policy,
                1,
                PrivacyRequestStatus.pending,
            )[0]
            run_privacy_request_task.delay(duplicate_request.id).get(
                timeout=PRIVACY_REQUEST_TASK_TIMEOUT
            )
            db.refresh(duplicate_request)
            assert duplicate_request.status == PrivacyRequestStatus.duplicate
            # verify execution log is added
            assert duplicate_request.execution_logs is not None
            skipped_log = duplicate_request.execution_logs.filter_by(
                status=ExecutionLogStatus.skipped
            ).first()
            assert skipped_log is not None
            assert (
                skipped_log.message
                == f"Request {duplicate_request.id} is a duplicate: it is duplicating actioned request(s) ['{privacy_request_with_email_identity.id}']."
            )


class TestDuplicatePrivacyRequestService:
    @pytest.fixture
    def mock_messaging_service(self) -> MessagingService:
        return mock.create_autospec(MessagingService)

    @pytest.fixture
    def privacy_request_service(
        self, db: Session, mock_config_proxy, mock_messaging_service
    ) -> PrivacyRequestService:
        return PrivacyRequestService(db, mock_config_proxy, mock_messaging_service)

    def test_privacy_request_service_duplicate_detection(
        self,
        db: Session,
        privacy_request_with_email_identity: PrivacyRequest,
        privacy_request_service: PrivacyRequestService,
    ):
        """Test that the privacy request service identifies and marks duplicate privacy requests."""
        privacy_request_with_email_identity.update(
            db=db, data={"status": PrivacyRequestStatus.in_processing}
        )
        data = PrivacyRequestCreate(
            identity=Identity(email="customer-1@example.com"),
            policy_key=privacy_request_with_email_identity.policy.key,
        )
        with mock.patch(
            "fides.service.privacy_request.privacy_request_service._handle_notifications_and_processing"
        ) as mock_handle_notifications_and_processing:
            mock_handle_notifications_and_processing.return_value = None
            privacy_request = privacy_request_service.create_privacy_request(data)
            assert privacy_request.status == PrivacyRequestStatus.duplicate
            assert privacy_request.duplicate_request_group_id is not None
            assert (
                privacy_request.duplicate_request_group_id
                == privacy_request_with_email_identity.duplicate_request_group_id
            )

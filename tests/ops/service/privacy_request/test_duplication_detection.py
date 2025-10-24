from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.service.privacy_request.duplication_detection import (
    create_duplicate_detection_conditions,
    find_duplicate_privacy_requests,
)
from fides.api.task.conditional_dependencies.schemas import ConditionGroup
from fides.config.duplicate_detection_settings import DuplicateDetectionSettings


@pytest.fixture
def privacy_request_with_multiple_identities(
    db: Session,
    policy: Policy,
) -> Generator[PrivacyRequest, None, None]:
    """Privacy request with email and phone_number identities."""
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": "test_external_id_multi",
            "started_processing_at": datetime.now(timezone.utc),
            "requested_at": datetime.now(timezone.utc),
            "status": PrivacyRequestStatus.in_processing,
            "policy_id": policy.id,
        },
    )
    privacy_request.persist_identity(
        db=db,
        identity=Identity(email="customer-1@example.com", phone_number="+15555555555"),
    )
    return privacy_request


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
            "status": PrivacyRequestStatus.complete,
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


class TestCreateDuplicateDetectionConditions:
    """Tests for create_duplicate_detection_conditions function."""

    def _get_detection_config(
        self, match_identity_fields: list[str]
    ) -> DuplicateDetectionSettings:
        return DuplicateDetectionSettings(
            enabled=True,
            time_window_days=30,
            match_identity_fields=match_identity_fields,
        )

    def test_create_conditions_single_identity_field(
        self, privacy_request_with_email_identity
    ):
        """Test creating conditions with single identity field returns expected structure."""
        detection_config = self._get_detection_config(["email"])
        conditions = create_duplicate_detection_conditions(
            privacy_request_with_email_identity, detection_config
        )

        assert conditions is not None
        assert isinstance(conditions, ConditionGroup)
        # Should have identity condition and time window condition
        assert (
            len(conditions.conditions) == 2
        )  # Grouped identity conditions and time window condition

    def test_create_conditions_multiple_identity_fields(
        self, privacy_request_with_multiple_identities
    ):
        """Test creating conditions with multiple identity fields returns expected structure."""
        detection_config = self._get_detection_config(["email", "phone_number"])
        conditions = create_duplicate_detection_conditions(
            privacy_request_with_multiple_identities, detection_config
        )
        assert conditions is not None
        assert isinstance(conditions, ConditionGroup)
        # Should have grouped identity conditions and time window condition
        assert (
            len(conditions.conditions) == 3
        )  # 2 grouped identity conditions and 1 time window condition

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
        self, privacy_request_with_email_identity, match_identity_fields
    ):
        """Test returns None when request has no identities matching configured fields."""
        config = self._get_detection_config(match_identity_fields)
        conditions = create_duplicate_detection_conditions(
            privacy_request_with_email_identity, config
        )
        assert conditions is None


class TestFindDuplicatePrivacyRequests:
    """Tests for find_duplicate_privacy_requests function."""

    @pytest.fixture
    def duplicate_detection_config(self):
        """Basic duplicate detection configuration."""
        return DuplicateDetectionSettings(
            enabled=True,
            time_window_days=30,
            match_identity_fields=["email"],
        )

    @pytest.mark.parametrize("duplicate_count", [1, 3])
    def test_find_duplicates_within_time_window(
        self,
        db,
        privacy_request_with_email_identity,
        duplicate_detection_config,
        policy,
        duplicate_count,
    ):
        """Test finding duplicate request within time window with matching identity."""
        duplicate_ids = []
        for i in range(duplicate_count):
            duplicate_request = PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"test_external_id_duplicate_{i}",
                    "started_processing_at": datetime.now(timezone.utc),
                    "requested_at": datetime.now(timezone.utc),
                    "status": PrivacyRequestStatus.in_processing,
                    "policy_id": policy.id,
                },
            )
            duplicate_request.persist_identity(
                db=db,
                identity=Identity(email="customer-1@example.com"),
            )
            duplicate_ids.append(duplicate_request.id)

        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_email_identity, duplicate_detection_config
        )

        assert len(duplicates) == duplicate_count
        assert all(duplicate.id in duplicate_ids for duplicate in duplicates)

    @pytest.mark.usefixtures("old_privacy_request_with_email")
    def test_no_duplicates_outside_time_window(
        self,
        db,
        privacy_request_with_email_identity,
        duplicate_detection_config,
    ):
        """Test that requests outside time window are not returned as duplicates."""
        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_email_identity, duplicate_detection_config
        )

        assert len(duplicates) == 0

    def test_find_duplicate_with_extended_time_window(
        self, db, privacy_request_with_email_identity, old_privacy_request_with_email
    ):
        """Test finding duplicate when extending time window to include older requests."""
        config = DuplicateDetectionSettings(
            enabled=True,
            time_window_days=60,
            match_identity_fields=["email"],
        )

        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_email_identity, config
        )

        assert len(duplicates) == 1
        assert duplicates[0].id == old_privacy_request_with_email.id

    def test_no_duplicates_different_identity_value(
        self,
        db,
        privacy_request_with_email_identity,
        duplicate_detection_config,
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

        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_email_identity, duplicate_detection_config
        )

        assert len(duplicates) == 0

    def test_no_duplicates_with_unmatched_identity_field(
        self, db, privacy_request_with_email_identity
    ):
        """Test returns empty list when config specifies unmatched identity fields."""
        config = DuplicateDetectionSettings(
            enabled=True,
            time_window_days=30,
            match_identity_fields=["phone_number"],
        )

        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_email_identity, config
        )

        assert len(duplicates) == 0

    def test_current_request_excluded_from_results(
        self, db, privacy_request_with_email_identity, duplicate_detection_config
    ):
        """Test that the current request itself is excluded from duplicate results."""
        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_email_identity, duplicate_detection_config
        )

        for duplicate in duplicates:
            assert duplicate.id != privacy_request_with_email_identity.id

    def test_find_duplicate_with_multiple_identity_fields(
        self, db, privacy_request_with_multiple_identities, policy
    ):
        """Test finding duplicates when matching on multiple identity fields."""
        config = DuplicateDetectionSettings(
            enabled=True,
            time_window_days=365,
            match_identity_fields=["email", "phone_number"],
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

        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_multiple_identities, config
        )

        assert len(duplicates) == 1
        assert duplicates[0].id == duplicate_request.id

    def test_partial_identity_match_not_returned(
        self, db, privacy_request_with_multiple_identities, policy
    ):
        """Test that request with only partial identity match is not returned as duplicate."""
        config = DuplicateDetectionSettings(
            enabled=True,
            time_window_days=365,
            match_identity_fields=["email", "phone_number"],
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

        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_multiple_identities, config
        )

        assert len(duplicates) == 0

    def test_requests_from_different_policy_id_not_returned(
        self,
        db,
        privacy_request_with_email_identity,
        duplicate_detection_config,
        erasure_policy: Policy,
    ):
        """Test that requests from different policies are not returned as duplicates."""

        erasure_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_external_id_erasure",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.now(timezone.utc),
                "status": PrivacyRequestStatus.complete,
                "policy_id": erasure_policy.id,
            },
        )
        erasure_request.persist_identity(
            db=db,
            identity=Identity(email="customer-1@example.com"),
        )

        duplicates = find_duplicate_privacy_requests(
            db, privacy_request_with_email_identity, duplicate_detection_config
        )

        assert len(duplicates) == 0

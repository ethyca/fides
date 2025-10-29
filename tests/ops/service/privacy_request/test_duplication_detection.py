from datetime import datetime, timedelta, timezone
from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.service.privacy_request.duplication_detection import (
    DuplicateDetectionService,
)
from fides.api.task.conditional_dependencies.schemas import ConditionGroup
from tests.ops.service.privacy_request.conftest import (
    create_duplicate_requests,
    get_detection_config,
)


@pytest.fixture
def duplicate_detection_service(db: Session) -> DuplicateDetectionService:
    return DuplicateDetectionService(db)


class TestCreateDuplicateDetectionConditions:
    """Tests for create_duplicate_detection_conditions function."""

    def test_create_conditions_single_identity_field(
        self, duplicate_detection_service, privacy_request_with_email_identity
    ):
        """Test creating conditions with single identity field returns expected structure."""
        detection_config = get_detection_config(match_identity_fields=["email"])
        conditions = duplicate_detection_service.create_duplicate_detection_conditions(
            privacy_request_with_email_identity, detection_config
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
        detection_config = get_detection_config(
            match_identity_fields=["email", "phone_number"]
        )
        conditions = duplicate_detection_service.create_duplicate_detection_conditions(
            privacy_request_with_multiple_identities, detection_config
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
        config = get_detection_config(match_identity_fields=match_identity_fields)
        conditions = duplicate_detection_service.create_duplicate_detection_conditions(
            privacy_request_with_email_identity, config
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
        duplicate_detection_config = get_detection_config()
        duplicate_requests = create_duplicate_requests(
            db, policy, duplicate_count, PrivacyRequestStatus.in_processing
        )
        duplicate_ids = [duplicate.id for duplicate in duplicate_requests]
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity, duplicate_detection_config
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
        duplicate_detection_config = get_detection_config()
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity, duplicate_detection_config
        )

        assert len(duplicates) == 0

    def test_find_duplicate_with_extended_time_window(
        self,
        duplicate_detection_service,
        privacy_request_with_email_identity,
        old_privacy_request_with_email,
    ):
        """Test finding duplicate when extending time window to include older requests."""
        duplicate_detection_config = get_detection_config(time_window_days=60)
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity, duplicate_detection_config
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
        duplicate_detection_config = get_detection_config()
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
            privacy_request_with_email_identity, duplicate_detection_config
        )

        assert len(duplicates) == 0

    def test_no_duplicates_with_unmatched_identity_field(
        self, duplicate_detection_service, privacy_request_with_email_identity
    ):
        """Test returns empty list when config specifies unmatched identity fields."""
        duplicate_detection_config = get_detection_config(
            match_identity_fields=["phone_number"]
        )
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity, duplicate_detection_config
        )

        assert len(duplicates) == 0

    def test_current_request_excluded_from_results(
        self,
        duplicate_detection_service,
        privacy_request_with_email_identity,
    ):
        """Test that the current request itself is excluded from duplicate results."""
        duplicate_detection_config = get_detection_config()
        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity, duplicate_detection_config
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
        config = get_detection_config(
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
            privacy_request_with_multiple_identities, config
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
        config = get_detection_config(
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
            privacy_request_with_multiple_identities, config
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
        duplicate_detection_config = get_detection_config()
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

        duplicates = duplicate_detection_service.find_duplicate_privacy_requests(
            privacy_request_with_email_identity, duplicate_detection_config
        )
        assert len(duplicates) == 0


class TestDuplicateRequestFunctionality:
    """Tests for is_canonical_request function."""

    def test_is_duplicate_request_single_request(
        self, duplicate_detection_service, privacy_request_with_email_identity
    ):
        """Test that a single request is the canonical request."""
        duplicate_detection_config = get_detection_config()
        is_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_email_identity, duplicate_detection_config
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
        duplicate_detection_config = get_detection_config()

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
            privacy_request_with_email_identity, duplicate_detection_config
        )
        assert (
            privacy_request_with_email_identity.duplicate_request_group_id is not None
        )
        for duplicate_request in duplicate_requests:
            assert duplicate_detection_service.is_duplicate_request(
                duplicate_request, duplicate_detection_config
            )
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
        config_1 = get_detection_config(match_identity_fields=["email"])
        config_2 = get_detection_config(match_identity_fields=["email", "phone_number"])

        email_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_email_identity, config_1
        )
        assert not email_duplicate

        duplicate_request_with_multiple_identities = create_duplicate_requests(
            db, policy, 1, PrivacyRequestStatus.in_processing
        )[0]
        duplicate_request_with_multiple_identities.persist_identity(
            db=db,
            identity=Identity(
                email="customer-1@example.com", phone_number="+15555555555"
            ),
        )

        multiple_identity_duplicate = duplicate_detection_service.is_duplicate_request(
            duplicate_request_with_multiple_identities, config_1
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
        email_duplicate = duplicate_detection_service.is_duplicate_request(
            privacy_request_with_email_identity, config_2
        )
        assert (
            not email_duplicate
        )  # This request is not a duplicate since it only has an email identity
        multiple_identity_duplicate = duplicate_detection_service.is_duplicate_request(
            duplicate_request_with_multiple_identities, config_2
        )
        assert (
            not multiple_identity_duplicate
        )  # This request is not a duplicate since it has both an email and phone number identity and is the first
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

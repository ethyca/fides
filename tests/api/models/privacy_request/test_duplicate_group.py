import time
import uuid

from sqlalchemy.orm import Session

from fides.api.models.privacy_request.duplicate_group import (
    DuplicateGroup,
    generate_deterministic_uuid,
    generate_rule_version,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.config.duplicate_detection_settings import DuplicateDetectionSettings

DUPLICATE_DETECTION_SETTINGS_EMAIL = DuplicateDetectionSettings(
    enabled=True,
    time_window_days=30,
    match_identity_fields=["email"],
)


DUPLICATE_DETECTION_SETTINGS_EMAIL_PHONE = DuplicateDetectionSettings(
    enabled=True,
    time_window_days=30,
    match_identity_fields=["email", "phone_number"],
)

GROUP_ID_EMAIL = generate_deterministic_uuid(
    generate_rule_version(DUPLICATE_DETECTION_SETTINGS_EMAIL), "duplicate@example.com"
)


class TestHelperFunctions:
    def test_generate_rule_version(self):
        """Test that rule version generation is stable and unique."""
        version_a1 = generate_rule_version(DUPLICATE_DETECTION_SETTINGS_EMAIL)
        version_a2 = generate_rule_version(DUPLICATE_DETECTION_SETTINGS_EMAIL)
        version_b = generate_rule_version(DUPLICATE_DETECTION_SETTINGS_EMAIL_PHONE)

        assert version_a1 == version_a2, (
            "Rule version should be stable for the same config"
        )
        assert version_a1 != version_b, (
            "Different configs should yield different rule versions"
        )

    def test_generate_deterministic_uuid(self):
        """Test that deterministic UUID generation is stable and unique."""
        uuid_a1 = generate_deterministic_uuid(
            DUPLICATE_DETECTION_SETTINGS_EMAIL, "duplicate@example.com"
        )
        uuid_a2 = generate_deterministic_uuid(
            DUPLICATE_DETECTION_SETTINGS_EMAIL, "duplicate@example.com"
        )
        uuid_a3 = generate_deterministic_uuid(
            DUPLICATE_DETECTION_SETTINGS_EMAIL, "new_duplicate@example.com"
        )
        uuid_b = generate_deterministic_uuid(
            DUPLICATE_DETECTION_SETTINGS_EMAIL_PHONE, "duplicate@example.com|1234567890"
        )

        assert uuid_a1 == uuid_a2, "UUID should be stable for the same config"
        assert uuid_a1 != uuid_a3, "Different dedup keys should yield different UUIDs"
        assert uuid_a1 != uuid_b, "Different configs should yield different UUIDs"


class TestDuplicateGroup:
    def test_create_duplicate_group(self, db: Session):
        """Test that duplicate group creation is successful."""
        rule_version = generate_rule_version(DUPLICATE_DETECTION_SETTINGS_EMAIL)
        duplicate_group = DuplicateGroup.create(
            db=db,
            data={
                "rule_version": rule_version,
                "dedup_key": "duplicate@example.com",
            },
        )
        assert duplicate_group.id == GROUP_ID_EMAIL
        assert duplicate_group.rule_version == rule_version
        assert duplicate_group.dedup_key == "duplicate@example.com"
        assert duplicate_group.is_active is True  # default is True

    def test_create_duplicate_group_existing_active_is_false(self, db: Session):
        """Test that duplicate group creation is successful when the existing group has is_active set to False."""
        duplicate_group = DuplicateGroup.create(
            db=db,
            data={
                "rule_version": generate_rule_version(
                    DUPLICATE_DETECTION_SETTINGS_EMAIL
                ),
                "dedup_key": "duplicate@example.com",
                "is_active": False,
            },
        )
        assert duplicate_group.is_active is False
        re_created_duplicate_group = DuplicateGroup.create(
            db=db,
            data={
                "rule_version": generate_rule_version(
                    DUPLICATE_DETECTION_SETTINGS_EMAIL
                ),
                "dedup_key": "duplicate@example.com",
            },
        )
        assert re_created_duplicate_group.is_active is True
        assert re_created_duplicate_group.id == duplicate_group.id

    def test_relationship_with_privacy_request(
        self, db: Session, privacy_request_with_email_identity: PrivacyRequest
    ):
        """Test that the relationship with privacy request is successful."""
        hashed_email = [
            pi.hashed_value
            for pi in privacy_request_with_email_identity.provided_identities
            if pi.field_name == "email"
        ][0]
        duplicate_group = DuplicateGroup.create(
            db=db,
            data={
                "rule_version": generate_rule_version(
                    DUPLICATE_DETECTION_SETTINGS_EMAIL
                ),
                "dedup_key": hashed_email,
            },
        )
        privacy_request_with_email_identity.duplicate_request_group_id = (
            duplicate_group.id
        )
        db.commit()
        assert (
            privacy_request_with_email_identity.duplicate_request_group_id
            == duplicate_group.id
        )
        assert duplicate_group.privacy_requests.count() == 1
        assert (
            duplicate_group.privacy_requests.first()
            == privacy_request_with_email_identity
        )

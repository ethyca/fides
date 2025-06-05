from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import IdentityVerificationException
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_respondent_email_verification import (
    ACCESS_LINK_TTL_DAYS,
    FidesUserRespondentEmailVerification,
)


class TestFidesUserRespondentEmailVerification:

    def test_create(self, db: Session, external_respondent: FidesUser) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        assert verification.user_id == external_respondent.id
        assert verification.access_token is not None
        assert verification.access_token_expires_at is not None
        assert verification.identity_verified_at is None
        assert verification.created_at is not None

        # Verify expiration is set correctly
        expected_expiry = datetime.now(timezone.utc) + timedelta(
            days=ACCESS_LINK_TTL_DAYS
        )
        assert (
            abs(
                (verification.access_token_expires_at - expected_expiry).total_seconds()
            )
            < 1
        )

    def test_multiple_active_verifications(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        """Test that a user can have multiple active verifications."""
        # Create first verification
        verification1 = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        # Create second verification
        verification2 = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        # Verify both verifications exist and are active
        assert verification1.id != verification2.id
        assert verification1.access_token != verification2.access_token
        assert not verification1.is_access_token_expired()
        assert not verification2.is_access_token_expired()

        # Verify the relationship works
        assert len(external_respondent.email_verifications.all()) == 2
        assert verification1 in external_respondent.email_verifications
        assert verification2 in external_respondent.email_verifications

    def test_create_bad_payload(self, db: Session) -> None:
        with pytest.raises(KeyError):
            FidesUserRespondentEmailVerification.create(
                db=db,
                data={},
            )

    def test_is_access_token_expired(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        assert not verification.is_access_token_expired()

        # Manually set expiration to past
        verification.access_token_expires_at = datetime.now(timezone.utc) - timedelta(
            days=1
        )
        assert verification.is_access_token_expired()

    def test_verify_access_token(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        assert verification.verify_access_token(verification.access_token)
        assert not verification.verify_access_token("invalid_token")

        # Test expired token
        verification.access_token_expires_at = datetime.now(timezone.utc) - timedelta(
            days=1
        )
        assert not verification.verify_access_token(verification.access_token)

    def test_verify_identity(self, db: Session, external_respondent: FidesUser) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        # Cache a verification code
        verification.cache_identity_verification_code("123456")

        # Verify with correct code
        verification.verify_identity(db, provided_code="123456")
        assert verification.identity_verified_at is not None

        # Verify with incorrect code
        with pytest.raises(PermissionError) as exc:
            verification.verify_identity(db, provided_code="000000")
        assert "Incorrect identification code" in str(exc.value)

        # Verify with expired token
        verification.access_token_expires_at = datetime.now(timezone.utc) - timedelta(
            days=1
        )
        with pytest.raises(ValueError):
            verification.verify_identity(db, provided_code="123456")

    def test_verify_identity_without_code(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        """Test that verifying identity without caching a code first raises an error."""
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        with pytest.raises(IdentityVerificationException) as exc:
            verification.verify_identity(db, provided_code="123456")
        assert "Identification code expired" in str(exc.value)

    def test_verify_identity_multiple_times(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        """Test that verifying identity multiple times works correctly."""
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        # Cache a verification code
        verification.cache_identity_verification_code("123456")

        # First verification
        verification.verify_identity(db, provided_code="123456")
        first_verified_at = verification.identity_verified_at

        # Cache a new code
        verification.cache_identity_verification_code("654321")

        # Second verification
        verification.verify_identity(db, provided_code="654321")
        second_verified_at = verification.identity_verified_at

        # Verify that the timestamps are different
        assert first_verified_at != second_verified_at

    def test_get_cached_verification_code(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        """Test retrieving a cached verification code."""
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        # Initially no code should be cached
        assert verification.get_cached_verification_code() is None

        # Cache a code
        verification.cache_identity_verification_code("123456")
        assert verification.get_cached_verification_code() == "123456"

    def test_purge_verification_code(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        """Test removing a cached verification code."""
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "user_id": external_respondent.id,
            },
        )

        # Cache a code
        verification.cache_identity_verification_code("123456")
        assert verification.get_cached_verification_code() == "123456"

        # Purge the code
        verification.purge_verification_code()
        assert verification.get_cached_verification_code() is None

from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_respondent_email_verification import (
    ACCESS_LINK_TTL_DAYS,
    MAX_ATTEMPTS,
    VERIFICATION_CODE_TTL_HOURS,
    FidesUserRespondentEmailVerification,
)


class TestFidesUserRespondentEmailVerification:

    def test_create(self, db: Session, external_respondent: FidesUser) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )

        assert verification.username == external_respondent.username
        assert verification.user_id == external_respondent.id
        assert verification.access_token is not None
        assert verification.access_token_expires_at is not None
        assert verification.verification_code is None
        assert verification.verification_code_expires_at is None
        assert verification.attempts == 0
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
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )

        # Create second verification
        verification2 = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )

        # Verify both verifications exist and are active
        assert verification1.id != verification2.id
        assert verification1.access_token != verification2.access_token
        assert not verification1.is_access_token_expired()
        assert not verification2.is_access_token_expired()

        # Generate verification codes for both
        code1 = verification1.generate_verification_code(db)
        code2 = verification2.generate_verification_code(db)

        # Verify both codes are valid
        assert verification1.verify_code(code1, db)
        assert verification2.verify_code(code2, db)

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
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )

        assert not verification.is_access_token_expired()

        # Manually set expiration to past
        verification.access_token_expires_at = datetime.now(timezone.utc) - timedelta(
            days=1
        )
        assert verification.is_access_token_expired()

    def test_is_verification_code_expired(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )

        # Should be expired when no code exists
        assert verification.is_verification_code_expired()

        # Generate a code
        code = verification.generate_verification_code(db)
        assert not verification.is_verification_code_expired()

        # Manually set expiration to past
        verification.verification_code_expires_at = datetime.now(
            timezone.utc
        ) - timedelta(hours=1)
        assert verification.is_verification_code_expired()

    def test_verify_access_token(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "username": external_respondent.username,
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

    def test_generate_verification_code(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )

        code = verification.generate_verification_code(db)
        assert len(code) == 16
        assert code.isalnum()
        assert verification.verification_code == code
        assert verification.attempts == 0

        # Verify expiration is set correctly
        expected_expiry = datetime.now(timezone.utc) + timedelta(
            hours=VERIFICATION_CODE_TTL_HOURS
        )
        assert (
            abs(
                (
                    verification.verification_code_expires_at - expected_expiry
                ).total_seconds()
            )
            < 1
        )

    def test_verify_code(self, db: Session, external_respondent: FidesUser) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )

        code = verification.generate_verification_code(db)
        assert verification.verify_code(code, db)
        # Correct code should reset attempts and not increment
        assert verification.attempts == 0

        # Test invalid code
        # Incorrect code should increment attempts
        assert not verification.verify_code("000000", db)
        assert verification.attempts == 1

        # Test expired code
        # Expired code should increment attempts
        verification.verification_code_expires_at = datetime.now(
            timezone.utc
        ) - timedelta(hours=1)
        assert not verification.verify_code(code, db)
        assert verification.attempts == 2

    def test_verify_code_max_attempts(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        from loguru import logger

        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )
        verification.generate_verification_code(db)
        for _ in range(MAX_ATTEMPTS):
            assert not verification.verify_code("000000", db)
            logger.info(f"Attempt {_ + 1} of {MAX_ATTEMPTS}")

        # This attempt should raise ValueError since attempts > MAX_ATTEMPTS
        with pytest.raises(ValueError) as exc:
            verification.verify_code("000000", db)
        assert str(exc.value) == "Maximum number of attempts for verification reached."

    def test_reset_attempts(self, db: Session, external_respondent: FidesUser) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={
                "username": external_respondent.username,
                "user_id": external_respondent.id,
            },
        )
        # Should be 0 attempts
        assert verification.attempts == 0
        # Should be 1 attempt
        verification.verify_code("000000", db)
        assert verification.attempts == 1
        # Should be 0 attempts
        verification.reset_attempts(db)
        assert verification.attempts == 0

        code = verification.generate_verification_code(db)
        verification.verify_code("000000", db)
        assert verification.attempts == 1
        # Correct code should reset attempts
        verification.verify_code(code, db)
        assert verification.attempts == 0

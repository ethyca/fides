from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_respondent_email_verification import (
    ACCESS_LINK_TTL_DAYS,
    VERIFICATION_CODE_TTL_HOURS,
    FidesUserRespondentEmailVerification,
)

USER_NAME = "test_user"
EMAIL_ADDRESS = "test@example.com"


@pytest.fixture
def external_respondent(db: Session) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={
            "username": USER_NAME,
            "email_address": EMAIL_ADDRESS,
            "roles": ["external_respondent"],
        },
    )
    yield user
    user.delete(db)


class TestFidesUserRespondentEmailVerification:
    def test_create(self, db: Session, external_respondent: FidesUser) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={"username": USER_NAME},
        )

        assert verification.username == USER_NAME
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
            data={"username": USER_NAME},
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
            data={"username": USER_NAME},
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
            data={"username": USER_NAME},
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
            data={"username": USER_NAME},
        )

        code = verification.generate_verification_code(db)
        assert len(code) == 6
        assert code.isdigit()
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
            data={"username": USER_NAME},
        )

        code = verification.generate_verification_code(db)
        assert verification.verify_code(code, db)
        assert verification.attempts == 1

        # Test invalid code
        assert not verification.verify_code("000000", db)
        assert verification.attempts == 2

        # Test expired code
        verification.verification_code_expires_at = datetime.now(
            timezone.utc
        ) - timedelta(hours=1)
        assert not verification.verify_code(code, db)

    def test_generate_new_access_token(
        self, db: Session, external_respondent: FidesUser
    ) -> None:
        verification = FidesUserRespondentEmailVerification.create(
            db=db,
            data={"username": USER_NAME},
        )

        original_token = verification.access_token
        original_expiry = verification.access_token_expires_at
        verification.attempts = 5

        new_token = verification.generate_new_access_token(db)
        assert new_token != original_token
        assert verification.access_token == new_token
        assert verification.access_token_expires_at > original_expiry
        assert verification.attempts == 0

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

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from fides.api.models.fides_user_invite import INVITE_CODE_TTL_HOURS, FidesUserInvite


class TestFidesUserInvite:
    def test_create(self, db: Session):
        email = "test@example.com"
        invite_code = "test_invite"
        user_invite = FidesUserInvite.create(
            db, {"email": email, "invite_code": invite_code}
        )

        assert user_invite.email == email
        assert user_invite.hashed_invite_code is not None
        assert user_invite.salt is not None
        assert user_invite.created_at is not None
        assert user_invite.updated_at is not None

    def test_invite_code_valid(self, db: Session):
        email = "test@example.com"
        invite_code = "test_invite"
        user_invite = FidesUserInvite.create(
            db, {"email": email, "invite_code": invite_code}
        )

        assert user_invite.invite_code_valid(invite_code) is True
        assert user_invite.invite_code_valid("wrong_code") is False

    def test_is_expired(self, db: Session):
        email = "test@example.com"
        invite_code = "test_invite"
        user_invite = FidesUserInvite.create(
            db, {"email": email, "invite_code": invite_code}
        )
        assert user_invite.is_expired() is False

        # Manually set 'updated_at' to simulate an expired invite
        user_invite.updated_at = datetime.now(timezone.utc) - timedelta(
            hours=INVITE_CODE_TTL_HOURS + 1
        )
        assert user_invite.is_expired() is True

    def test_renew_invite(self, db: Session):
        email = "test@example.com"
        initial_invite_code = "initial_invite"
        new_invite_code = "new_invite"

        # Create initial invite
        user_invite = FidesUserInvite.create(
            db, {"email": email, "invite_code": initial_invite_code}
        )
        original_hashed_code = user_invite.hashed_invite_code
        original_salt = user_invite.salt
        original_updated_at = user_invite.updated_at

        # Refresh invite with new code
        user_invite.renew_invite(db, new_invite_code)
        db.refresh(user_invite)

        assert user_invite.hashed_invite_code != original_hashed_code
        assert user_invite.salt != original_salt
        assert user_invite.updated_at > original_updated_at
        assert user_invite.invite_code_valid(new_invite_code)

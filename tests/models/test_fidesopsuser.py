import pytest

from sqlalchemy.orm import Session
from fidesops.models.fidesops_user import FidesopsUser


class TestFidesopsUser:
    def test_create_user(self, db: Session) -> None:
        user = FidesopsUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        assert user.username == "user_1"
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.hashed_password != "test_password"

        assert not user.credentials_valid("bad_password")
        assert user.credentials_valid("test_password")

        user.delete(db)

    def test_create_user_bad_payload(self, db: Session) -> None:
        with pytest.raises(KeyError):
            FidesopsUser.create(
                db=db,
                data={},
            )

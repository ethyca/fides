import pytest
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions
from sqlalchemy.orm import Session

from fidesops.ops.api.v1.scope_registry import PRIVACY_REQUEST_READ


class TestFidesUserPermissions:
    def test_create_user_permissions(self, db: Session) -> None:
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions: FidesUserPermissions = FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]},
        )

        assert permissions.user_id == user.id
        assert permissions.scopes == [PRIVACY_REQUEST_READ]
        assert permissions.created_at is not None
        assert permissions.updated_at is not None

        user.delete(db)

    def test_create_user_permissions_bad_payload(self, db: Session) -> None:
        with pytest.raises(Exception):
            FidesUserPermissions.create(
                db=db,
                data={},
            )

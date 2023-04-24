import pytest
from sqlalchemy.orm import Session

from fides.api.ops.models.fides_user import FidesUser
from fides.api.ops.models.fides_user_permissions import FidesUserPermissions
from fides.lib.oauth.roles import CONTRIBUTOR, ROLES_TO_SCOPES_MAPPING, VIEWER


class TestFidesUserPermissions:
    def test_create_user_permissions(self, db: Session) -> None:
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions: FidesUserPermissions = FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [CONTRIBUTOR]},
        )

        assert permissions.user_id == user.id
        assert permissions.roles == [CONTRIBUTOR]
        assert permissions.created_at is not None
        assert permissions.updated_at is not None

        user.delete(db)

    def test_create_user_permissions_bad_payload(self, db: Session) -> None:
        with pytest.raises(Exception):
            FidesUserPermissions.create(
                db=db,
                data={},
            )

    def test_total_scopes(self, db):
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions: FidesUserPermissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "roles": [VIEWER],
            },
        )
        assert permissions.total_scopes == ROLES_TO_SCOPES_MAPPING[VIEWER]
        user.delete(db)

    def test_total_scopes_no_roles(self, db):
        user = FidesUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions: FidesUserPermissions = FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id},
        )
        assert permissions.total_scopes == []
        user.delete(db)

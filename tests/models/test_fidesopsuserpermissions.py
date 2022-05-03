import pytest

from sqlalchemy.orm import Session

import psycopg2.errors as db_errors
from fidesops.api.v1.scope_registry import PRIVACY_REQUEST_READ
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.fidesops_user_permissions import FidesopsUserPermissions


class TestFidesopsUserPermissions:
    def test_create_user_permissions(self, db: Session) -> None:
        user = FidesopsUser.create(
            db=db,
            data={"username": "user_1", "password": "test_password"},
        )

        permissions:FidesopsUserPermissions = FidesopsUserPermissions.create(
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
            FidesopsUserPermissions.create(
                db=db,
                data={},
            )

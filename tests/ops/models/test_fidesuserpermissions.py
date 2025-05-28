import pytest
from sqlalchemy.orm import Session
from typing import Generator

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.roles import (
    CONTRIBUTOR,
    EXTERNAL_RESPONDENT,
    RESPONDENT,
    ROLES_TO_SCOPES_MAPPING,
    VIEWER,
)


USER_NAME = "user_1"
PASSWORD = "test_password"

@pytest.fixture
def user(db: Session) -> Generator[FidesUser, None, None]:
    user = FidesUser.create(
        db=db,
        data={"username": USER_NAME, "password": PASSWORD},
    )
    yield user
    user.delete(db)

class TestFidesUserPermissions:
    def test_create_user_permissions(self, db: Session, user: FidesUser) -> None:
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

    def test_total_scopes(self, db: Session, user: FidesUser) -> None:
        permissions: FidesUserPermissions = FidesUserPermissions.create(
            db=db,
            data={
                "user_id": user.id,
                "roles": [VIEWER],
            },
        )
        assert permissions.total_scopes == ROLES_TO_SCOPES_MAPPING[VIEWER]
        user.delete(db)

    def test_total_scopes_no_roles(self, db: Session, user: FidesUser) -> None:
        permissions: FidesUserPermissions = FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id},
        )
        assert permissions.total_scopes == []
        user.delete(db)

    @pytest.mark.parametrize(
        "role, expected",
        [
            (RESPONDENT, True),
            (EXTERNAL_RESPONDENT, True),
            (CONTRIBUTOR, False),
            (VIEWER, False),
        ],
    )
    def test_is_respondent(self, db: Session, user: FidesUser, role: str, expected: bool) -> None:
        permissions: FidesUserPermissions = FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": [role]},
        )
        assert permissions.is_respondent() == expected
        user.delete(db)

    @pytest.mark.parametrize(
        "initial_roles, new_roles, expected_error",
        [
            ([CONTRIBUTOR], [RESPONDENT], None),
            ([CONTRIBUTOR], [VIEWER], None),
            ([CONTRIBUTOR], [CONTRIBUTOR], None),
            (
                [RESPONDENT],
                [CONTRIBUTOR],
                "Role changes are not allowed for respondents",
            ),
            (
                [EXTERNAL_RESPONDENT],
                [CONTRIBUTOR],
                "Role changes are not allowed for respondents",
            ),
        ],
    )
    def test_update_roles(self, db: Session, user: FidesUser, initial_roles: list[str], new_roles: list[str], expected_error: str) -> None:
        permissions: FidesUserPermissions = FidesUserPermissions.create(
            db=db,
            data={"user_id": user.id, "roles": initial_roles},
        )
        if expected_error:
            with pytest.raises(ValueError, match=expected_error):
                permissions.update_roles(db, new_roles)
        else:
            permissions.update_roles(db, new_roles)
            assert permissions.roles == new_roles
        user.delete(db)

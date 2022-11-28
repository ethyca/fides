# pylint: disable=missing-function-docstring

from unittest.mock import MagicMock

from fideslib.models.fides_user_permissions import FidesUserPermissions
from fideslib.oauth.scopes import (
    PRIVACY_REQUEST_READ,
    USER_CREATE,
    USER_DELETE,
    USER_READ,
)


def test_create_user_permissions():
    permissions: FidesUserPermissions = FidesUserPermissions.create(  # type: ignore
        db=MagicMock(),
        data={"user_id": "test", "scopes": [PRIVACY_REQUEST_READ]},
    )

    assert permissions.user_id == "test"
    assert permissions.scopes == [PRIVACY_REQUEST_READ]
    assert permissions.privileges == ("view_subject_requests",)


def test_associated_privileges():
    permissions: FidesUserPermissions = FidesUserPermissions.create(  # type: ignore
        db=MagicMock(),
        data={
            "user_id": "test",
            "scopes": [USER_CREATE, USER_READ, USER_DELETE, PRIVACY_REQUEST_READ],
        },
    )

    assert permissions.user_id == "test"
    assert permissions.scopes == [
        USER_CREATE,
        USER_READ,
        USER_DELETE,
        PRIVACY_REQUEST_READ,
    ]
    assert permissions.privileges == (
        "view_subject_requests",
        "view_users",
        "manage_users",
    )

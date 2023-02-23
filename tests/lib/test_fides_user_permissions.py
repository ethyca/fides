# pylint: disable=missing-function-docstring

from unittest.mock import MagicMock

# Included so that `AccessManualWebhook` can be located when
# `ConnectionConfig` is instantiated.
from fides.api.ops.models.manual_webhook import (  # pylint: disable=unused-import
    AccessManualWebhook,
)
from fides.lib.models.fides_user_permissions import FidesUserPermissions
from fides.api.ops.api.v1.scope_registry import (
    PRIVACY_REQUEST_READ,
    USER_CREATE,
    USER_DELETE,
    USER_READ,
)


def test_create_user_permissions():
    permissions: FidesUserPermissions = FidesUserPermissions.create(  # type: ignore
        # Not using the `db` here allows us to omit PK and FK data
        db=MagicMock(),
        data={"user_id": "test", "scopes": [PRIVACY_REQUEST_READ]},
    )

    assert permissions.user_id == "test"
    assert permissions.scopes == [PRIVACY_REQUEST_READ]
    assert permissions.privileges == ("view_subject_requests",)


def test_associated_privileges():
    permissions: FidesUserPermissions = FidesUserPermissions.create(  # type: ignore
        # Not using the `db` here allows us to omit PK and FK data
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

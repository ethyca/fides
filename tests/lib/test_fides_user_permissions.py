# pylint: disable=missing-function-docstring

from unittest.mock import MagicMock

# Included so that `AccessManualWebhook` can be located when
# `ConnectionConfig` is instantiated.
from fides.api.ops.models.manual_webhook import (  # pylint: disable=unused-import
    AccessManualWebhook,
)
from fides.lib.models.fides_user_permissions import FidesUserPermissions
from fides.lib.oauth.scopes import (
    PRIVACY_REQUEST_READ,
    USER_CREATE,
    USER_DELETE,
    USER_READ,
)

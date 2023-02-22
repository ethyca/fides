# pylint: disable=missing-function-docstring

from unittest.mock import MagicMock

from fides.api.ops.api.v1.scope_registry import (
    PRIVACY_REQUEST_READ,
    USER_CREATE,
    USER_DELETE,
    USER_READ,
)

# Included so that `AccessManualWebhook` can be located when
# `ConnectionConfig` is instantiated.
from fides.api.ops.models.manual_webhook import (  # pylint: disable=unused-import
    AccessManualWebhook,
)
from fides.lib.models.fides_user_permissions import FidesUserPermissions

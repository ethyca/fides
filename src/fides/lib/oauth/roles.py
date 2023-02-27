from enum import Enum
from typing import Dict, List, Optional

from fides.api.ops.api.v1.scope_registry import (
    CLI_OBJECTS_READ,
    CLIENT_READ,
    CONFIG_READ,
    CONNECTION_READ,
    CONNECTION_TYPE_READ,
    CONSENT_READ,
    CTL_DATASET_READ,
    CTL_POLICY_READ,
    DATA_CATEGORY_READ,
    DATA_QUALIFIER_READ,
    DATA_SUBJECT_READ,
    DATA_USE_READ,
    DATAMAP_READ,
    DATASET_READ,
    EVALUATION_READ,
    MESSAGING_READ,
    ORGANIZATION_READ,
    POLICY_READ,
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_NOTIFICATIONS_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
    PRIVACY_REQUEST_TRANSFER,
    PRIVACY_REQUEST_UPLOAD_DATA,
    PRIVACY_REQUEST_VIEW_DATA,
    REGISTRY_READ,
    RULE_READ,
    SAAS_CONFIG_READ,
    SCOPE_READ,
    SCOPE_REGISTRY,
    STORAGE_READ,
    SYSTEM_READ,
    USER_READ,
    WEBHOOK_READ,
)

PRIVACY_REQUEST_MANAGER = "privacy_request_manager"
VIEWER = "viewer"
VIEWER_AND_PRIVACY_REQUEST_MANAGER = "viewer_and_privacy_request_manager"
ADMIN = "admin"


class RoleRegistry(Enum):
    """Enum of available roles"""

    admin = ADMIN
    viewer_and_privacy_request_manager = VIEWER_AND_PRIVACY_REQUEST_MANAGER
    viewer = VIEWER
    privacy_request_manager = PRIVACY_REQUEST_MANAGER


privacy_request_manager_scopes = [
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_REVIEW,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_NOTIFICATIONS_READ,
    PRIVACY_REQUEST_TRANSFER,
    PRIVACY_REQUEST_UPLOAD_DATA,
    PRIVACY_REQUEST_VIEW_DATA,
]


viewer_scopes = [  # Intentionally omitted USER_PERMISSION_READ
    CLI_OBJECTS_READ,
    CLIENT_READ,
    CONFIG_READ,
    CONNECTION_READ,
    CONSENT_READ,
    CONNECTION_TYPE_READ,
    CTL_DATASET_READ,
    DATA_CATEGORY_READ,
    CTL_POLICY_READ,
    DATA_QUALIFIER_READ,
    DATAMAP_READ,
    DATASET_READ,
    DATA_SUBJECT_READ,
    DATA_USE_READ,
    EVALUATION_READ,
    ORGANIZATION_READ,
    POLICY_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_NOTIFICATIONS_READ,
    REGISTRY_READ,
    RULE_READ,
    SCOPE_READ,
    STORAGE_READ,
    SYSTEM_READ,
    MESSAGING_READ,
    WEBHOOK_READ,
    SAAS_CONFIG_READ,
    USER_READ,
]

ROLES_TO_SCOPES_MAPPING: Dict[str, List] = {
    ADMIN: sorted(SCOPE_REGISTRY),
    VIEWER_AND_PRIVACY_REQUEST_MANAGER: sorted(
        list(set(viewer_scopes + privacy_request_manager_scopes))
    ),
    VIEWER: sorted(viewer_scopes),
    PRIVACY_REQUEST_MANAGER: sorted(privacy_request_manager_scopes),
}


def get_scopes_from_roles(roles: Optional[List[str]]) -> List[str]:
    """Return a list of all the scopes the user has via their role(s)"""
    if not roles:
        return []

    scope_list: List[str] = []
    for role in roles:
        scope_list += ROLES_TO_SCOPES_MAPPING.get(role, [])
    return [*set(scope_list)]

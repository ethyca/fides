from enum import Enum
from typing import Dict, List, Optional

from fides.common.api.scope_registry import (
    CLI_OBJECTS_READ,
    CLIENT_READ,
    CONNECTION_READ,
    CONNECTION_TYPE_READ,
    CONNECTOR_TEMPLATE_REGISTER,
    CONSENT_READ,
    CONSENT_SETTINGS_READ,
    CTL_DATASET_READ,
    CTL_POLICY_READ,
    DATA_CATEGORY_READ,
    DATA_SUBJECT_READ,
    DATA_USE_READ,
    DATASET_READ,
    EVALUATION_READ,
    MASKING_EXEC,
    MASKING_READ,
    MESSAGING_CREATE_OR_UPDATE,
    MESSAGING_DELETE,
    MESSAGING_READ,
    ORGANIZATION_READ,
    POLICY_READ,
    PRIVACY_EXPERIENCE_READ,
    PRIVACY_NOTICE_READ,
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_NOTIFICATIONS_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
    PRIVACY_REQUEST_UPLOAD_DATA,
    PRIVACY_REQUEST_VIEW_DATA,
    RULE_READ,
    SAAS_CONFIG_READ,
    SCOPE_READ,
    SCOPE_REGISTRY,
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    STORAGE_READ,
    SYSTEM_MANAGER_READ,
    SYSTEM_READ,
    USER_PERMISSION_ASSIGN_OWNERS,
    USER_READ,
    WEBHOOK_READ,
)

APPROVER = "approver"
CONTRIBUTOR = "contributor"
OWNER = "owner"
VIEWER = "viewer"
VIEWER_AND_APPROVER = "viewer_and_approver"


class RoleRegistryEnum(Enum):
    """Enum of available roles

    Owner - Full admin
    Viewer - Can view everything
    Approver - Limited viewer but can approve Privacy Requests
    Viewer + Approver = Full View and can approve Privacy Requests
    Contributor - Can't configure storage and messaging
    """

    owner = OWNER
    viewer_approver = VIEWER_AND_APPROVER
    viewer = VIEWER
    approver = APPROVER
    contributor = CONTRIBUTOR


approver_scopes = [
    PRIVACY_REQUEST_REVIEW,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_UPLOAD_DATA,
    PRIVACY_REQUEST_VIEW_DATA,
]


viewer_scopes = [  # Intentionally omitted USER_PERMISSION_READ
    CLI_OBJECTS_READ,
    CLIENT_READ,
    CONNECTION_READ,
    CONSENT_READ,
    CONSENT_SETTINGS_READ,
    CONNECTION_TYPE_READ,
    CTL_DATASET_READ,
    DATA_CATEGORY_READ,
    CTL_POLICY_READ,
    DATASET_READ,
    DATA_SUBJECT_READ,
    DATA_USE_READ,
    EVALUATION_READ,
    MASKING_EXEC,
    MASKING_READ,
    ORGANIZATION_READ,
    POLICY_READ,
    PRIVACY_EXPERIENCE_READ,
    PRIVACY_NOTICE_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_NOTIFICATIONS_READ,
    RULE_READ,
    SCOPE_READ,
    STORAGE_READ,
    SYSTEM_READ,
    MESSAGING_READ,
    WEBHOOK_READ,
    SYSTEM_MANAGER_READ,
    SAAS_CONFIG_READ,
    USER_READ,
]

not_contributor_scopes = [
    CONNECTOR_TEMPLATE_REGISTER,
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    MESSAGING_CREATE_OR_UPDATE,
    MESSAGING_DELETE,
    PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE,
    USER_PERMISSION_ASSIGN_OWNERS,
]

ROLES_TO_SCOPES_MAPPING: Dict[str, List] = {
    OWNER: sorted(SCOPE_REGISTRY),
    VIEWER_AND_APPROVER: sorted(list(set(viewer_scopes + approver_scopes))),
    VIEWER: sorted(viewer_scopes),
    APPROVER: sorted(approver_scopes),
    CONTRIBUTOR: sorted(list(set(SCOPE_REGISTRY) - set(not_contributor_scopes))),
}


def get_scopes_from_roles(roles: Optional[List[str]]) -> List[str]:
    """Return a list of all the scopes the user has via their role(s)"""
    if not roles:
        return []

    scope_list: List[str] = []
    for role in roles:
        scope_list += ROLES_TO_SCOPES_MAPPING.get(role, [])
    return [*set(scope_list)]

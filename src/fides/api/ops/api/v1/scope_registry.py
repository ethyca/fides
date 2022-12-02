CLIENT_CREATE = "client:create"
CLIENT_UPDATE = "client:update"
CLIENT_READ = "client:read"
CLIENT_DELETE = "client:delete"

CONFIG_READ = "config:read"

POLICY_CREATE_OR_UPDATE = "policy:create_or_update"
POLICY_READ = "policy:read"
POLICY_DELETE = "policy:delete"

CONNECTION_TYPE_READ = "connection_type:read"

CONNECTION_CREATE_OR_UPDATE = "connection:create_or_update"
CONNECTION_READ = "connection:read"
CONNECTION_DELETE = "connection:delete"
CONNECTION_AUTHORIZE = "connection:authorize"
SAAS_CONNECTION_INSTANTIATE = "connection:instantiate"

CONSENT_READ = "consent:read"

PRIVACY_REQUEST_CREATE = "privacy-request:create"
PRIVACY_REQUEST_READ = "privacy-request:read"
PRIVACY_REQUEST_DELETE = "privacy-request:delete"
PRIVACY_REQUEST_CALLBACK_RESUME = (
    "privacy-request:resume"  # User has permission to resume a privacy request
)
PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE = (
    "privacy-request-notifications:create_or_update"
)
PRIVACY_REQUEST_NOTIFICATIONS_READ = "privacy-request-notifications:read"
PRIVACY_REQUEST_REVIEW = "privacy-request:review"
PRIVACY_REQUEST_TRANSFER = "privacy-request:transfer"
PRIVACY_REQUEST_UPLOAD_DATA = "privacy-request:upload_data"
PRIVACY_REQUEST_VIEW_DATA = "privacy-request:view_data"

WEBHOOK_CREATE_OR_UPDATE = "webhook:create_or_update"
WEBHOOK_READ = "webhook:read"
WEBHOOK_DELETE = "webhook:delete"

RULE_CREATE_OR_UPDATE = "rule:create_or_update"
RULE_READ = "rule:read"
RULE_DELETE = "rule:delete"

STORAGE_CREATE_OR_UPDATE = "storage:create_or_update"
STORAGE_READ = "storage:read"
STORAGE_DELETE = "storage:delete"

MESSAGING_CREATE_OR_UPDATE = "messaging:create_or_update"
MESSAGING_READ = "messaging:read"
MESSAGING_DELETE = "messaging:delete"

SCOPE_READ = "scope:read"

ENCRYPTION_EXEC = "encryption:exec"

DATASET_CREATE_OR_UPDATE = "dataset:create_or_update"
DATASET_READ = "dataset:read"
DATASET_DELETE = "dataset:delete"

SAAS_CONFIG_CREATE_OR_UPDATE = "saas_config:create_or_update"
SAAS_CONFIG_READ = "saas_config:read"
SAAS_CONFIG_DELETE = "saas_config:delete"

USER_CREATE = "user:create"
USER_UPDATE = "user:update"
USER_READ = "user:read"
USER_DELETE = "user:delete"
USER_PASSWORD_RESET = "user:reset-password"

USER_PERMISSION_CREATE = "user-permission:create"
USER_PERMISSION_UPDATE = "user-permission:update"
USER_PERMISSION_READ = "user-permission:read"

SCOPE_REGISTRY = [
    CLIENT_CREATE,
    CLIENT_UPDATE,
    CLIENT_READ,
    CLIENT_DELETE,
    CONFIG_READ,
    CONNECTION_READ,
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_AUTHORIZE,
    SAAS_CONNECTION_INSTANTIATE,
    CONSENT_READ,
    CONNECTION_TYPE_READ,
    DATASET_CREATE_OR_UPDATE,
    DATASET_DELETE,
    DATASET_READ,
    ENCRYPTION_EXEC,
    POLICY_CREATE_OR_UPDATE,
    POLICY_READ,
    POLICY_DELETE,
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
    RULE_CREATE_OR_UPDATE,
    RULE_READ,
    RULE_DELETE,
    SCOPE_READ,
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    STORAGE_READ,
    MESSAGING_CREATE_OR_UPDATE,
    MESSAGING_DELETE,
    MESSAGING_READ,
    WEBHOOK_CREATE_OR_UPDATE,
    WEBHOOK_READ,
    WEBHOOK_DELETE,
    SAAS_CONFIG_CREATE_OR_UPDATE,
    SAAS_CONFIG_READ,
    SAAS_CONFIG_DELETE,
    USER_CREATE,
    USER_UPDATE,
    USER_READ,
    USER_PASSWORD_RESET,
    USER_DELETE,
    USER_PERMISSION_CREATE,
    USER_PERMISSION_UPDATE,
    USER_PERMISSION_READ,
]

CLIENT_CREATE = "client:create"
CLIENT_UPDATE = "client:update"
CLIENT_READ = "client:read"
CLIENT_DELETE = "client:delete"

CONFIG_READ = "config:read"

POLICY_CREATE_OR_UPDATE = "policy:create_or_update"
POLICY_READ = "policy:read"
POLICY_DELETE = "policy:delete"

CONNECTION_CREATE_OR_UPDATE = "connection:create_or_update"
CONNECTION_READ = "connection:read"
CONNECTION_DELETE = "connection:delete"

PRIVACY_REQUEST_READ = "privacy-request:read"
PRIVACY_REQUEST_DELETE = "privacy-request:delete"
PRIVACY_REQUEST_CALLBACK_RESUME = (
    "privacy-request:resume"  # User has permission to restart a paused privacy request
)
PRIVACY_REQUEST_REVIEW = "privacy-request:review"

WEBHOOK_CREATE_OR_UPDATE = "webhook:create_or_update"
WEBHOOK_READ = "webhook:read"
WEBHOOK_DELETE = "webhook:delete"

RULE_CREATE_OR_UPDATE = "rule:create_or_update"
RULE_READ = "rule:read"
RULE_DELETE = "rule:delete"

STORAGE_CREATE_OR_UPDATE = "storage:create_or_update"
STORAGE_READ = "storage:read"
STORAGE_DELETE = "storage:delete"

SCOPE_READ = "scope:read"

ENCRYPTION_EXEC = "encryption:exec"

DATASET_CREATE_OR_UPDATE = "dataset:create_or_update"
DATASET_READ = "dataset:read"
DATASET_DELETE = "dataset:delete"

SAAS_CONFIG_CREATE_OR_UPDATE = "saas_config:create_or_update"
SAAS_CONFIG_READ = "saas_config:read"
SAAS_CONFIG_DELETE = "saas_config:delete"

USER_CREATE = "user:create"
USER_READ = "user:read"
USER_DELETE = "user:delete"

SCOPE_REGISTRY = [
    CLIENT_CREATE,
    CLIENT_UPDATE,
    CLIENT_READ,
    CLIENT_DELETE,
    CONFIG_READ,
    CONNECTION_READ,
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    DATASET_CREATE_OR_UPDATE,
    DATASET_DELETE,
    DATASET_READ,
    ENCRYPTION_EXEC,
    POLICY_CREATE_OR_UPDATE,
    POLICY_READ,
    POLICY_DELETE,
    PRIVACY_REQUEST_REVIEW,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_CALLBACK_RESUME,
    RULE_CREATE_OR_UPDATE,
    RULE_READ,
    RULE_DELETE,
    SCOPE_READ,
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    STORAGE_READ,
    WEBHOOK_CREATE_OR_UPDATE,
    WEBHOOK_READ,
    WEBHOOK_DELETE,
    SAAS_CONFIG_CREATE_OR_UPDATE,
    SAAS_CONFIG_READ,
    SAAS_CONFIG_DELETE,
    USER_CREATE,
    USER_READ,
    USER_DELETE,
]

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

PRIVACY_REQUEST_CREATE = "privacy-request:create"
PRIVACY_REQUEST_READ = "privacy-request:read"
PRIVACY_REQUEST_DELETE = "privacy-request:delete"

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
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_DELETE,
    RULE_CREATE_OR_UPDATE,
    RULE_READ,
    RULE_DELETE,
    SCOPE_READ,
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    STORAGE_READ,
]

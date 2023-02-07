"""
This module contains every scope used in the application.

The format for defining a scope is:
    <SCOPE_SECTION>_<SCOPE_NAME> = "<scope_section>:<scope_name>"
    CLIENT_CREATE = "client:create"

`SCOPE_REGISTRY` is intended as a comprehensive list of all available scopes.

There is a redundant `fides/lib/oauth/scopes.py` file that should not be used.
"""

# These permissions all endpoints used by the CLI's `push` & `evaluate` commands
CLI_OBJECTS_CREATE = "cli-objects:create"
CLI_OBJECTS_READ = "cli-objects:read"
CLI_OBJECTS_UPDATE = "cli-objects:update"
CLI_OBJECTS_DELETE = "cli-objects:delete"

CLIENT_CREATE = "client:create"
CLIENT_UPDATE = "client:update"
CLIENT_READ = "client:read"
CLIENT_DELETE = "client:delete"

CONFIG_READ = "config:read"
CONFIG_UPDATE = "config:update"

CONNECTION_TYPE_READ = "connection_type:read"

CONNECTION_CREATE_OR_UPDATE = "connection:create_or_update"
CONNECTION_READ = "connection:read"
CONNECTION_DELETE = "connection:delete"
CONNECTION_AUTHORIZE = "connection:authorize"
SAAS_CONNECTION_INSTANTIATE = "connection:instantiate"

CONSENT_READ = "consent:read"

DATABASE_RESET = "database:reset"

DATAMAP_READ = "datamap:read"

DATASET_CREATE_OR_UPDATE = "dataset:create_or_update"
DATASET_READ = "dataset:read"
DATASET_DELETE = "dataset:delete"

ENCRYPTION_EXEC = "encryption:exec"

GENERATE_EXEC = "generate:exec"

MESSAGING_CREATE_OR_UPDATE = "messaging:create_or_update"
MESSAGING_READ = "messaging:read"
MESSAGING_DELETE = "messaging:delete"

POLICY_CREATE_OR_UPDATE = "policy:create_or_update"
POLICY_READ = "policy:read"
POLICY_DELETE = "policy:delete"

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

RULE_CREATE_OR_UPDATE = "rule:create_or_update"
RULE_READ = "rule:read"
RULE_DELETE = "rule:delete"

SAAS_CONFIG_CREATE_OR_UPDATE = "saas_config:create_or_update"
SAAS_CONFIG_READ = "saas_config:read"
SAAS_CONFIG_DELETE = "saas_config:delete"

SCOPE_READ = "scope:read"

STORAGE_CREATE_OR_UPDATE = "storage:create_or_update"
STORAGE_READ = "storage:read"
STORAGE_DELETE = "storage:delete"

USER_CREATE = "user:create"
USER_UPDATE = "user:update"
USER_READ = "user:read"
USER_DELETE = "user:delete"
USER_PASSWORD_RESET = "user:password-reset"

USER_PERMISSION_CREATE = "user-permission:create"
USER_PERMISSION_UPDATE = "user-permission:update"
USER_PERMISSION_READ = "user-permission:read"

VALIDATE_EXEC = "validate:exec"

WEBHOOK_CREATE_OR_UPDATE = "webhook:create_or_update"
WEBHOOK_READ = "webhook:read"
WEBHOOK_DELETE = "webhook:delete"

# Should contain all scopes listed above.
SCOPE_REGISTRY = [
    CLI_OBJECTS_CREATE,
    CLI_OBJECTS_READ,
    CLI_OBJECTS_UPDATE,
    CLI_OBJECTS_DELETE,
    CLIENT_CREATE,
    CLIENT_UPDATE,
    CLIENT_READ,
    CLIENT_DELETE,
    CONFIG_READ,
    CONFIG_UPDATE,
    CONNECTION_READ,
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_AUTHORIZE,
    SAAS_CONNECTION_INSTANTIATE,
    CONSENT_READ,
    CONNECTION_TYPE_READ,
    DATABASE_RESET,
    DATAMAP_READ,
    DATASET_CREATE_OR_UPDATE,
    DATASET_DELETE,
    DATASET_READ,
    ENCRYPTION_EXEC,
    GENERATE_EXEC,
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
    VALIDATE_EXEC,
]

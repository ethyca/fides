AUTHORIZE = "authorize"
CONFIG = "config"
CONNECTION = "connection"
CONNECTION_TYPE = "connection_type"
CLIENT = "client"
CREATE = "create"
CREATE_OR_UPDATE = "create_or_update"
DATASET = "dataset"
DELETE = "delete"
ENCRYPTION = "encryption"
EXEC = "exec"
FIDES_TAXONOMY = "fides_taxonomy"
ORGANIZATION = "organization"
POLICY = "policy"
PRIVACY_REQUEST = "privacy-request"
READ = "read"
RESUME = "resume"
REVIEW = "review"
RESET_PASSWORD = "reset-password"
RULE = "rule"
SAAS_CONFIG = "saas_config"
SCOPE = "scope"
STORAGE = "storage"
SYSTEM = "system"
TAXONOMY = "taxonomy"
UPDATE = "update"
UPLOAD_DATA = "upload_data"
USER = "user"
USER_PERMISSION = "user-permission"
VIEW_DATA = "view_data"
WEBHOOK = "webhook"

CONFIG_READ = f"{CONFIG}:{READ}"

CLIENT_CREATE = f"{CLIENT}:{CREATE}"
CLIENT_DELETE = f"{CLIENT}:{DELETE}"
CLIENT_READ = f"{CLIENT}:{READ}"
CLIENT_UPDATE = f"{CLIENT}:{UPDATE}"

CONNECTION_CREATE_OR_UPDATE = f"{CONNECTION}:{CREATE_OR_UPDATE}"
CONNECTION_DELETE = f"{CONNECTION}:{DELETE}"
CONNECTION_READ = f"{CONNECTION}:{READ}"
CONNECTION_AUTHORIZE = f"{CONNECTION}:{AUTHORIZE}"

CONNECTION_TYPE_READ = f"{CONNECTION_TYPE}:{READ}"

DATASET_CREATE_OR_UPDATE = f"{DATASET}:{CREATE_OR_UPDATE}"
DATASET_DELETE = f"{DATASET}:{DELETE}"
DATASET_READ = f"{DATASET}:{READ}"

ENCRYPTION_EXEC = f"{ENCRYPTION}:{EXEC}"

FIDES_TAXONOMY_UPDATE = f"{FIDES_TAXONOMY}:{UPDATE}"

ORGANIZATION_CREATE = f"{ORGANIZATION}:{CREATE}"
ORGANIZATION_UPDATE = f"{ORGANIZATION}:{UPDATE}"
ORGANIZATION_DELETE = f"{ORGANIZATION}:{DELETE}"

POLICY_CREATE_OR_UPDATE = f"{POLICY}:{CREATE_OR_UPDATE}"
POLICY_DELETE = f"{POLICY}:{DELETE}"
POLICY_READ = f"{POLICY}:{READ}"

PRIVACY_REQUEST_CALLBACK_RESUME = f"{PRIVACY_REQUEST}:{RESUME}"  # User has permission to restart a paused privacy request
PRIVACY_REQUEST_DELETE = f"{PRIVACY_REQUEST}:{DELETE}"
PRIVACY_REQUEST_READ = f"{PRIVACY_REQUEST}:{READ}"
PRIVACY_REQUEST_REVIEW = f"{PRIVACY_REQUEST}:{REVIEW}"
PRIVACY_REQUEST_UPLOAD_DATA = f"{PRIVACY_REQUEST}:{UPLOAD_DATA}"
PRIVACY_REQUEST_VIEW_DATA = f"{PRIVACY_REQUEST}:{VIEW_DATA}"

RULE_CREATE_OR_UPDATE = f"{RULE}:{CREATE_OR_UPDATE}"
RULE_DELETE = f"{RULE}:{DELETE}"
RULE_READ = f"{RULE}:{READ}"

SAAS_CONFIG_CREATE_OR_UPDATE = f"{SAAS_CONFIG}:{CREATE_OR_UPDATE}"
SAAS_CONFIG_DELETE = f"{SAAS_CONFIG}:{DELETE}"
SAAS_CONFIG_READ = f"{SAAS_CONFIG}:{READ}"

SCOPE_READ = f"{SCOPE}:{READ}"

STORAGE_CREATE_OR_UPDATE = f"{STORAGE}:{CREATE_OR_UPDATE}"
STORAGE_DELETE = f"{STORAGE}:{DELETE}"
STORAGE_READ = f"{STORAGE}:{READ}"

SYSTEM_CREATE = f"{SYSTEM}:{CREATE}"
SYSTEM_UPDATE = f"{SYSTEM}:{UPDATE}"
SYSTEM_DELETE = f"{SYSTEM}:{DELETE}"

TAXONOMY_CREATE = f"{TAXONOMY}:{CREATE}"
TAXONOMY_UPDATE = f"{TAXONOMY}:{UPDATE}"
TAXONOMY_DELETE = f"{TAXONOMY}:{DELETE}"

USER_CREATE = f"{USER}:{CREATE}"
USER_DELETE = f"{USER}:{DELETE}"
USER_READ = f"{USER}:{READ}"
USER_UPDATE = f"{USER}:{UPDATE}"
USER_PASSWORD_RESET = f"{USER}:{RESET_PASSWORD}"

USER_PERMISSION_CREATE = f"{USER_PERMISSION}:{CREATE}"
USER_PERMISSION_UPDATE = f"{USER_PERMISSION}:{UPDATE}"
USER_PERMISSION_READ = f"{USER_PERMISSION}:{READ}"

WEBHOOK_CREATE_OR_UPDATE = f"{WEBHOOK}:{CREATE_OR_UPDATE}"
WEBHOOK_DELETE = f"{WEBHOOK}:{DELETE}"
WEBHOOK_READ = f"{WEBHOOK}:{READ}"

SCOPE_DOCS = {
    CONFIG_READ: "View the configuration",
    CLIENT_CREATE: "Create OAuth clients",
    CLIENT_DELETE: "Remove OAuth clients",
    CLIENT_READ: "View current scopes for OAuth clients",
    CLIENT_UPDATE: "Modify existing scopes for OAuth clients",
    CONNECTION_CREATE_OR_UPDATE: "Create or modify connections",
    CONNECTION_DELETE: "Remove connections",
    CONNECTION_READ: "View connections",
    CONNECTION_AUTHORIZE: "OAuth2 Authorization",
    CONNECTION_TYPE_READ: "View types of connections",
    DATASET_CREATE_OR_UPDATE: "Create or modify datasets",
    DATASET_DELETE: "Delete datasets",
    DATASET_READ: "View datasets",
    ENCRYPTION_EXEC: "Encrypt data",
    FIDES_TAXONOMY_UPDATE: "Update default fides taxonomy description",
    ORGANIZATION_CREATE: "Create organization",
    ORGANIZATION_DELETE: "Delete organization",
    ORGANIZATION_UPDATE: "Update organization details",
    POLICY_CREATE_OR_UPDATE: "Create or modify policies",
    POLICY_DELETE: "Remove policies",
    POLICY_READ: "View policies",
    PRIVACY_REQUEST_CALLBACK_RESUME: "Restart paused privacy requests",
    PRIVACY_REQUEST_DELETE: "Remove privacy requests",
    PRIVACY_REQUEST_READ: "View privacy requests",
    PRIVACY_REQUEST_REVIEW: "Review privacy requests",
    PRIVACY_REQUEST_UPLOAD_DATA: "Manually upload data for the privacy request",
    PRIVACY_REQUEST_VIEW_DATA: "View subject data related to the privacy request",
    RESET_PASSWORD: "Reset user password",
    RULE_CREATE_OR_UPDATE: "Create or update rules",
    RULE_DELETE: "Remove rules",
    RULE_READ: "View rules",
    SAAS_CONFIG_CREATE_OR_UPDATE: "Create or update SAAS configurations",
    SAAS_CONFIG_DELETE: "Remove SAAS configurations",
    SAAS_CONFIG_READ: "View SAAS configurations",
    SCOPE_READ: "View authorization scopes",
    STORAGE_CREATE_OR_UPDATE: "Create or update storage",
    STORAGE_DELETE: "Remove storage",
    STORAGE_READ: "View storage",
    SYSTEM_CREATE: "Create systems",
    SYSTEM_DELETE: "Delete systems",
    SYSTEM_UPDATE: "Update systems",
    TAXONOMY_CREATE: "Create local taxonomy",
    TAXONOMY_DELETE: "Delete local taxonomy",
    TAXONOMY_UPDATE: "Update local taxonomy",
    USER_CREATE: "Create users",
    USER_UPDATE: "Update users",
    USER_DELETE: "Remove users",
    USER_READ: "View users",
    USER_PASSWORD_RESET: "Update user password",
    USER_PERMISSION_CREATE: "Create user permissions",
    USER_PERMISSION_UPDATE: "Update user permissions",
    USER_PERMISSION_READ: "View user permissions",
    WEBHOOK_CREATE_OR_UPDATE: "Create or update web hooks",
    WEBHOOK_DELETE: "Remove web hooks",
    WEBHOOK_READ: "View web hooks",
}

SCOPES = list(SCOPE_DOCS.keys())

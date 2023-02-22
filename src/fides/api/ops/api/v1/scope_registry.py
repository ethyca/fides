"""
This module contains every scope used in the application.

The format for defining a scope is:
    <SCOPE_SECTION>_<SCOPE_NAME> = "<scope_section>:<scope_name>"
    CLIENT_CREATE = "client:create"

`SCOPE_REGISTRY` is intended as a comprehensive list of all available scopes.
"""

AUTHORIZE = "authorize"
CLI_OBJECTS = "cli-objects"
CLIENT = "client"
CONFIG = "config"
CONNECTION = "connection"
CONNECTION_TYPE = "connection_type"
CONSENT = "consent"
CREATE = "create"
CREATE_OR_UPDATE = "create_or_update"
DATABASE = "database"
DATAMAP = "datamap"
DATASET = "dataset"
DELETE = "delete"
ENCRYPTION = "encryption"
EXEC = "exec"
FIDES_TAXONOMY = "fides_taxonomy"
GENERATE = "generate"
INSTANTIATE = "instantiate"
MESSAGING = "messaging"
ORGANIZATION = "organization"
PASSWORD_RESET = "password-reset"
POLICY = "policy"
PRIVACY_REQUEST = "privacy-request"
PRIVACY_REQUEST_NOTIFICATIONS = "privacy-request-notifications"
READ = "read"
RESET = "reset"
RESUME = "resume"
REVIEW = "review"
RULE = "rule"
SAAS_CONFIG = "saas_config"
SCOPE = "scope"
STORAGE = "storage"
SYSTEM = "system"
TAXONOMY = "taxonomy"
TRANSFER = "transfer"
UPDATE = "update"
UPLOAD_DATA = "upload_data"
USER = "user"
USER_PERMISSION = "user-permission"
VALIDATE = "validate"
VIEW_DATA = "view_data"
WEBHOOK = "webhook"

CLIENT_CREATE = f"{CLIENT}:{CREATE}"
CLIENT_DELETE = f"{CLIENT}:{DELETE}"
CLIENT_READ = f"{CLIENT}:{READ}"
CLIENT_UPDATE = f"{CLIENT}:{UPDATE}"

CLI_OBJECTS_CREATE = f"{CLI_OBJECTS}:{CREATE}"
CLI_OBJECTS_READ = f"{CLI_OBJECTS}:{READ}"
CLI_OBJECTS_UPDATE = f"{CLI_OBJECTS}:{UPDATE}"
CLI_OBJECTS_DELETE = f"{CLI_OBJECTS}:{DELETE}"

CONFIG_READ = f"{CONFIG}:{READ}"
CONFIG_UPDATE = f"{CONFIG}:{UPDATE}"

CONNECTION_CREATE_OR_UPDATE = f"{CONNECTION}:{CREATE_OR_UPDATE}"
CONNECTION_DELETE = f"{CONNECTION}:{DELETE}"
CONNECTION_READ = f"{CONNECTION}:{READ}"
CONNECTION_AUTHORIZE = f"{CONNECTION}:{AUTHORIZE}"

CONNECTION_TYPE_READ = f"{CONNECTION_TYPE}:{READ}"

CONSENT_READ = f"{CONSENT}:{READ}"

DATABASE_RESET = f"{DATABASE}:{RESET}"

DATAMAP_READ = f"{DATAMAP}:{READ}"

DATASET_CREATE_OR_UPDATE = f"{DATASET}:{CREATE_OR_UPDATE}"
DATASET_DELETE = f"{DATASET}:{DELETE}"
DATASET_READ = f"{DATASET}:{READ}"

ENCRYPTION_EXEC = f"{ENCRYPTION}:{EXEC}"

FIDES_TAXONOMY_UPDATE = f"{FIDES_TAXONOMY}:{UPDATE}"

GENERATE_EXEC = f"{GENERATE}:{EXEC}"

MESSAGING_CREATE_OR_UPDATE = f"{MESSAGING}:{CREATE_OR_UPDATE}"
MESSAGING_DELETE = f"{MESSAGING}:{DELETE}"
MESSAGING_READ = f"{MESSAGING}:{READ}"

ORGANIZATION_CREATE = f"{ORGANIZATION}:{CREATE}"
ORGANIZATION_UPDATE = f"{ORGANIZATION}:{UPDATE}"
ORGANIZATION_DELETE = f"{ORGANIZATION}:{DELETE}"

POLICY_CREATE_OR_UPDATE = f"{POLICY}:{CREATE_OR_UPDATE}"
POLICY_DELETE = f"{POLICY}:{DELETE}"
POLICY_READ = f"{POLICY}:{READ}"

PRIVACY_REQUEST_CALLBACK_RESUME = f"{PRIVACY_REQUEST}:{RESUME}"  # User has permission to restart a paused privacy request
PRIVACY_REQUEST_CREATE = f"{PRIVACY_REQUEST}:{CREATE}"
PRIVACY_REQUEST_DELETE = f"{PRIVACY_REQUEST}:{DELETE}"
PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE = (
    f"{PRIVACY_REQUEST_NOTIFICATIONS}:{CREATE_OR_UPDATE}"
)
PRIVACY_REQUEST_NOTIFICATIONS_READ = f"{PRIVACY_REQUEST_NOTIFICATIONS}:{READ}"
PRIVACY_REQUEST_READ = f"{PRIVACY_REQUEST}:{READ}"
PRIVACY_REQUEST_REVIEW = f"{PRIVACY_REQUEST}:{REVIEW}"
PRIVACY_REQUEST_TRANSFER = f"{PRIVACY_REQUEST}:{TRANSFER}"
PRIVACY_REQUEST_UPLOAD_DATA = f"{PRIVACY_REQUEST}:{UPLOAD_DATA}"
PRIVACY_REQUEST_VIEW_DATA = f"{PRIVACY_REQUEST}:{VIEW_DATA}"

RULE_CREATE_OR_UPDATE = f"{RULE}:{CREATE_OR_UPDATE}"
RULE_DELETE = f"{RULE}:{DELETE}"
RULE_READ = f"{RULE}:{READ}"

SAAS_CONFIG_CREATE_OR_UPDATE = f"{SAAS_CONFIG}:{CREATE_OR_UPDATE}"
SAAS_CONFIG_DELETE = f"{SAAS_CONFIG}:{DELETE}"
SAAS_CONFIG_READ = f"{SAAS_CONFIG}:{READ}"

SAAS_CONNECTION_INSTANTIATE = f"{CONNECTION}:{INSTANTIATE}"

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
USER_PASSWORD_RESET = f"{USER}:{PASSWORD_RESET}"

USER_PERMISSION_CREATE = f"{USER_PERMISSION}:{CREATE}"
USER_PERMISSION_UPDATE = f"{USER_PERMISSION}:{UPDATE}"
USER_PERMISSION_READ = f"{USER_PERMISSION}:{READ}"

VALIDATE_EXEC = f"{VALIDATE}:{EXEC}"

WEBHOOK_CREATE_OR_UPDATE = f"{WEBHOOK}:{CREATE_OR_UPDATE}"
WEBHOOK_DELETE = f"{WEBHOOK}:{DELETE}"
WEBHOOK_READ = f"{WEBHOOK}:{READ}"

SCOPE_DOCS = {
    CONFIG_READ: "View the configuration",
    CONFIG_UPDATE: "Update the configuration",
    CLI_OBJECTS_CREATE: "Create objects via the command line interface",
    CLI_OBJECTS_READ: "Read objects via the command line interface",
    CLI_OBJECTS_UPDATE: "Update objects via the command line interface",
    CLI_OBJECTS_DELETE: "Delete objects via the command line interface",
    CLIENT_CREATE: "Create OAuth clients",
    CLIENT_DELETE: "Remove OAuth clients",
    CLIENT_READ: "View current scopes for OAuth clients",
    CLIENT_UPDATE: "Modify existing scopes for OAuth clients",
    CONNECTION_CREATE_OR_UPDATE: "Create or modify connections",
    CONNECTION_DELETE: "Remove connections",
    CONNECTION_READ: "View connections",
    CONNECTION_AUTHORIZE: "OAuth2 Authorization",
    CONNECTION_TYPE_READ: "View types of connections",
    CONSENT_READ: "Read consent preferences",
    DATABASE_RESET: "Reset the application database",
    DATAMAP_READ: "Read systems on the datamap",
    DATASET_CREATE_OR_UPDATE: "Create or modify datasets",
    DATASET_DELETE: "Delete datasets",
    DATASET_READ: "View datasets",
    ENCRYPTION_EXEC: "Encrypt data",
    FIDES_TAXONOMY_UPDATE: "Update default fides taxonomy description",
    GENERATE_EXEC: "",
    MESSAGING_CREATE_OR_UPDATE: "",
    MESSAGING_DELETE: "",
    MESSAGING_READ: "",
    ORGANIZATION_CREATE: "Create organization",
    ORGANIZATION_DELETE: "Delete organization",
    ORGANIZATION_UPDATE: "Update organization details",
    POLICY_CREATE_OR_UPDATE: "Create or modify policies",
    POLICY_DELETE: "Remove policies",
    POLICY_READ: "View policies",
    PRIVACY_REQUEST_CREATE: "",
    PRIVACY_REQUEST_CALLBACK_RESUME: "Restart paused privacy requests",
    PRIVACY_REQUEST_DELETE: "Remove privacy requests",
    PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE: "",
    PRIVACY_REQUEST_NOTIFICATIONS_READ: "",
    PRIVACY_REQUEST_READ: "View privacy requests",
    PRIVACY_REQUEST_REVIEW: "Review privacy requests",
    PRIVACY_REQUEST_TRANSFER: "Transfer privacy requests",
    PRIVACY_REQUEST_UPLOAD_DATA: "Manually upload data for the privacy request",
    PRIVACY_REQUEST_VIEW_DATA: "View subject data related to the privacy request",
    RULE_CREATE_OR_UPDATE: "Create or update rules",
    RULE_DELETE: "Remove rules",
    RULE_READ: "View rules",
    SAAS_CONFIG_CREATE_OR_UPDATE: "Create or update SAAS configurations",
    SAAS_CONFIG_DELETE: "Remove SAAS configurations",
    SAAS_CONFIG_READ: "View SAAS configurations",
    SAAS_CONNECTION_INSTANTIATE: "",
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
    USER_PASSWORD_RESET: "Reset another user's password",
    USER_PERMISSION_CREATE: "Create user permissions",
    USER_PERMISSION_UPDATE: "Update user permissions",
    USER_PERMISSION_READ: "View user permissions",
    VALIDATE_EXEC: "",
    WEBHOOK_CREATE_OR_UPDATE: "Create or update web hooks",
    WEBHOOK_DELETE: "Remove web hooks",
    WEBHOOK_READ: "View web hooks",
}

SCOPE_REGISTRY = list(SCOPE_DOCS.keys())

"""
This module contains every scope used in the application.

The format for defining a scope is:
    <SCOPE_SECTION>_<SCOPE_NAME> = "<scope_section>:<scope_name>"
    CLIENT_CREATE = "client:create"

`SCOPE_REGISTRY` is intended as a comprehensive list of all available scopes.
"""

from enum import Enum

AUTHORIZE = "authorize"
CLI_OBJECTS = "cli-objects"
CLIENT = "client"
CONFIG = "config"
CONNECTION = "connection"
CONNECTION_TYPE = "connection_type"
CONNECTOR_TEMPLATE = "connector_template"
CONSENT = "consent"
CONSENT_SETTINGS = "consent_settings"
CREATE = "create"
CREATE_OR_UPDATE = "create_or_update"
CTL_DATASET = "ctl_dataset"
CTL_POLICY = "ctl_policy"
CURRENT_PRIVACY_PREFERENCE = "current-privacy-preference"
DATABASE = "database"
DATA_CATEGORY = "data_category"
DATA_SUBJECT = "data_subject"
DATA_USE = "data_use"
DATASET = "dataset"
DELETE = "delete"
PRIVACY_REQUEST_REDACTION_PATTERNS = "privacy-request-redaction-patterns"
ENCRYPTION = "encryption"
MESSAGING_TEMPLATE = "messaging-template"
EVALUATION = "evaluation"
EXEC = "exec"
FIDES_TAXONOMY = "fides_taxonomy"
GENERATE = "generate"
INSTANTIATE = "instantiate"
MANUAL_STEPS = "manual-steps"
MASKING = "masking"
MESSAGING = "messaging"
ORGANIZATION = "organization"
PASSWORD_RESET = "password-reset"
POLICY = "policy"
PRIVACY_EXPERIENCE = "privacy-experience"
PRIVACY_NOTICE = "privacy-notice"
PRIVACY_PREFERENCE_HISTORY = "privacy-preference-history"
PRIVACY_REQUEST = "privacy-request"
PRIVACY_REQUEST_ACCESS_RESULTS = "privacy-request-access-results"
PRIVACY_REQUEST_EMAIL_INTEGRATIONS = "privacy-request-email-integrations"
PRIVACY_REQUEST_NOTIFICATIONS = "privacy-request-notifications"
READ = "read"
READ_OWN = "read-own"
REGISTER = "register"
RESET = "reset"
RESPOND = "respond"
RESUME = "resume"
REVIEW = "review"
RULE = "rule"
SAAS_CONFIG = "saas_config"
SCOPE = "scope"
SEND = "send"
STORAGE = "storage"
SYSTEM = "system"
SYSTEM_MANAGER = "system_manager"
TAXONOMY = "taxonomy"
TEST = "test"
TRANSFER = "transfer"
UPDATE = "update"
UPLOAD_DATA = "upload_data"
USER = "user"
USER_PERMISSION = "user-permission"
VALIDATE = "validate"
VIEW_DATA = "view_data"
WEBHOOK = "webhook"
WORKER_STATS = "worker-stats"
HEAP_DUMP = "heap_dump"

ASSIGN_OWNERS = "assign_owners"

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

CONSENT_SETTINGS_READ = f"{CONSENT_SETTINGS}:{READ}"
CONSENT_SETTINGS_UPDATE = f"{CONSENT_SETTINGS}:{UPDATE}"

CTL_DATASET_CREATE = f"{CTL_DATASET}:{CREATE}"
CTL_DATASET_READ = f"{CTL_DATASET}:{READ}"
CTL_DATASET_UPDATE = f"{CTL_DATASET}:{UPDATE}"
CTL_DATASET_DELETE = f"{CTL_DATASET}:{DELETE}"

CTL_POLICY_CREATE = f"{CTL_POLICY}:{CREATE}"
CTL_POLICY_READ = f"{CTL_POLICY}:{READ}"
CTL_POLICY_UPDATE = f"{CTL_POLICY}:{UPDATE}"
CTL_POLICY_DELETE = f"{CTL_POLICY}:{DELETE}"

CURRENT_PRIVACY_PREFERENCE_READ = f"{CURRENT_PRIVACY_PREFERENCE}:{READ}"

DATABASE_RESET = f"{DATABASE}:{RESET}"

DATA_CATEGORY_CREATE = f"{DATA_CATEGORY}:{CREATE}"
DATA_CATEGORY_READ = f"{DATA_CATEGORY}:{READ}"
DATA_CATEGORY_UPDATE = f"{DATA_CATEGORY}:{UPDATE}"
DATA_CATEGORY_DELETE = f"{DATA_CATEGORY}:{DELETE}"


DATA_SUBJECT_CREATE = f"{DATA_SUBJECT}:{CREATE}"
DATA_SUBJECT_READ = f"{DATA_SUBJECT}:{READ}"
DATA_SUBJECT_UPDATE = f"{DATA_SUBJECT}:{UPDATE}"
DATA_SUBJECT_DELETE = f"{DATA_SUBJECT}:{DELETE}"

DATA_USE_CREATE = f"{DATA_USE}:{CREATE}"
DATA_USE_READ = f"{DATA_USE}:{READ}"
DATA_USE_UPDATE = f"{DATA_USE}:{UPDATE}"
DATA_USE_DELETE = f"{DATA_USE}:{DELETE}"

DATASET_CREATE_OR_UPDATE = f"{DATASET}:{CREATE_OR_UPDATE}"

PRIVACY_REQUEST_REDACTION_PATTERNS_READ = f"{PRIVACY_REQUEST_REDACTION_PATTERNS}:{READ}"
PRIVACY_REQUEST_REDACTION_PATTERNS_UPDATE = (
    f"{PRIVACY_REQUEST_REDACTION_PATTERNS}:{UPDATE}"
)
DATASET_DELETE = f"{DATASET}:{DELETE}"
DATASET_READ = f"{DATASET}:{READ}"
DATASET_TEST = f"{DATASET}:{TEST}"

ENCRYPTION_EXEC = f"{ENCRYPTION}:{EXEC}"

HEAP_DUMP_EXEC = f"{HEAP_DUMP}:{EXEC}"

EVALUATION_CREATE = f"{EVALUATION}:{CREATE}"
EVALUATION_READ = f"{EVALUATION}:{READ}"
EVALUATION_UPDATE = f"{EVALUATION}:{UPDATE}"
EVALUATION_DELETE = f"{EVALUATION}:{DELETE}"

FIDES_TAXONOMY_UPDATE = f"{FIDES_TAXONOMY}:{UPDATE}"

GENERATE_EXEC = f"{GENERATE}:{EXEC}"

MASKING_EXEC = f"{MASKING}:{EXEC}"
MASKING_READ = f"{MASKING}:{READ}"

MESSAGING_CREATE_OR_UPDATE = f"{MESSAGING}:{CREATE_OR_UPDATE}"
MESSAGING_DELETE = f"{MESSAGING}:{DELETE}"
MESSAGING_READ = f"{MESSAGING}:{READ}"
MESSAGING_TEMPLATE_UPDATE = f"{MESSAGING_TEMPLATE}:{UPDATE}"

ORGANIZATION_CREATE = f"{ORGANIZATION}:{CREATE}"
ORGANIZATION_READ = f"{ORGANIZATION}:{READ}"
ORGANIZATION_UPDATE = f"{ORGANIZATION}:{UPDATE}"
ORGANIZATION_DELETE = f"{ORGANIZATION}:{DELETE}"

POLICY_CREATE_OR_UPDATE = f"{POLICY}:{CREATE_OR_UPDATE}"
POLICY_DELETE = f"{POLICY}:{DELETE}"
POLICY_READ = f"{POLICY}:{READ}"

PRIVACY_EXPERIENCE_CREATE = f"{PRIVACY_EXPERIENCE}:{CREATE}"
PRIVACY_EXPERIENCE_UPDATE = f"{PRIVACY_EXPERIENCE}:{UPDATE}"
PRIVACY_EXPERIENCE_READ = f"{PRIVACY_EXPERIENCE}:{READ}"

PRIVACY_NOTICE_CREATE = f"{PRIVACY_NOTICE}:{CREATE}"
PRIVACY_NOTICE_UPDATE = f"{PRIVACY_NOTICE}:{UPDATE}"
PRIVACY_NOTICE_READ = f"{PRIVACY_NOTICE}:{READ}"

PRIVACY_PREFERENCE_HISTORY_READ = f"{PRIVACY_PREFERENCE_HISTORY}:{READ}"

PRIVACY_REQUEST_CALLBACK_RESUME = f"{PRIVACY_REQUEST}:{RESUME}"  # User has permission to restart a paused privacy request
PRIVACY_REQUEST_CREATE = f"{PRIVACY_REQUEST}:{CREATE}"
PRIVACY_REQUEST_DELETE = f"{PRIVACY_REQUEST}:{DELETE}"
PRIVACY_REQUEST_EMAIL_INTEGRATIONS_SEND = f"{PRIVACY_REQUEST_EMAIL_INTEGRATIONS}:{SEND}"
PRIVACY_REQUEST_MANUAL_STEPS_REVIEW = f"{PRIVACY_REQUEST}:{MANUAL_STEPS}:{REVIEW}"
PRIVACY_REQUEST_MANUAL_STEPS_RESPOND = f"{PRIVACY_REQUEST}:{MANUAL_STEPS}:{RESPOND}"
PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE = (
    f"{PRIVACY_REQUEST_NOTIFICATIONS}:{CREATE_OR_UPDATE}"
)
PRIVACY_REQUEST_NOTIFICATIONS_READ = f"{PRIVACY_REQUEST_NOTIFICATIONS}:{READ}"
PRIVACY_REQUEST_READ = f"{PRIVACY_REQUEST}:{READ}"
PRIVACY_REQUEST_REVIEW = f"{PRIVACY_REQUEST}:{REVIEW}"
PRIVACY_REQUEST_TRANSFER = f"{PRIVACY_REQUEST}:{TRANSFER}"
PRIVACY_REQUEST_UPLOAD_DATA = f"{PRIVACY_REQUEST}:{UPLOAD_DATA}"
PRIVACY_REQUEST_VIEW_DATA = f"{PRIVACY_REQUEST}:{VIEW_DATA}"
PRIVACY_REQUEST_READ_ACCESS_RESULTS = f"{PRIVACY_REQUEST_ACCESS_RESULTS}:{READ}"

RULE_CREATE_OR_UPDATE = f"{RULE}:{CREATE_OR_UPDATE}"
RULE_DELETE = f"{RULE}:{DELETE}"
RULE_READ = f"{RULE}:{READ}"

SAAS_CONFIG_CREATE_OR_UPDATE = f"{SAAS_CONFIG}:{CREATE_OR_UPDATE}"
SAAS_CONFIG_DELETE = f"{SAAS_CONFIG}:{DELETE}"
SAAS_CONFIG_READ = f"{SAAS_CONFIG}:{READ}"

SAAS_CONNECTION_INSTANTIATE = f"{CONNECTION}:{INSTANTIATE}"
CONNECTOR_TEMPLATE_REGISTER = f"{CONNECTOR_TEMPLATE}:{REGISTER}"

SCOPE_READ = f"{SCOPE}:{READ}"

STORAGE_CREATE_OR_UPDATE = f"{STORAGE}:{CREATE_OR_UPDATE}"
STORAGE_DELETE = f"{STORAGE}:{DELETE}"
STORAGE_READ = f"{STORAGE}:{READ}"

SYSTEM_CREATE = f"{SYSTEM}:{CREATE}"
SYSTEM_READ = f"{SYSTEM}:{READ}"
SYSTEM_UPDATE = f"{SYSTEM}:{UPDATE}"
SYSTEM_DELETE = f"{SYSTEM}:{DELETE}"


SYSTEM_MANAGER_READ = f"{SYSTEM_MANAGER}:{READ}"
SYSTEM_MANAGER_UPDATE = f"{SYSTEM_MANAGER}:{UPDATE}"
SYSTEM_MANAGER_DELETE = f"{SYSTEM_MANAGER}:{DELETE}"

USER_CREATE = f"{USER}:{CREATE}"
USER_DELETE = f"{USER}:{DELETE}"
USER_READ = f"{USER}:{READ}"
USER_READ_OWN = f"{USER}:{READ_OWN}"
USER_UPDATE = f"{USER}:{UPDATE}"
USER_PASSWORD_RESET = f"{USER}:{PASSWORD_RESET}"

USER_PERMISSION_CREATE = f"{USER_PERMISSION}:{CREATE}"
USER_PERMISSION_UPDATE = f"{USER_PERMISSION}:{UPDATE}"
USER_PERMISSION_READ = f"{USER_PERMISSION}:{READ}"
USER_PERMISSION_ASSIGN_OWNERS = f"{USER_PERMISSION}:{ASSIGN_OWNERS}"

VALIDATE_EXEC = f"{VALIDATE}:{EXEC}"

WEBHOOK_CREATE_OR_UPDATE = f"{WEBHOOK}:{CREATE_OR_UPDATE}"
WEBHOOK_DELETE = f"{WEBHOOK}:{DELETE}"
WEBHOOK_READ = f"{WEBHOOK}:{READ}"

WORKER_STATS_READ = f"{WORKER_STATS}:{READ}"

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
    CONNECTOR_TEMPLATE_REGISTER: "Register a connector template",
    CONSENT_READ: "Read consent preferences",
    CONSENT_SETTINGS_READ: "Read org-wide consent settings",
    CONSENT_SETTINGS_UPDATE: "Update org-wide consent settings",
    CTL_DATASET_CREATE: "Create a ctl dataset",
    CTL_DATASET_READ: "Read ctl datasets",
    CTL_DATASET_DELETE: "Delete a ctl dataset",
    CTL_DATASET_UPDATE: "Update ctl datasets",
    CTL_POLICY_CREATE: "Create a ctl policy",
    CTL_POLICY_READ: "Read ctl policies",
    CTL_POLICY_DELETE: "Delete a ctl policy",
    CTL_POLICY_UPDATE: "Update ctl policies",
    CURRENT_PRIVACY_PREFERENCE_READ: "Read the current privacy preferences of all users",
    DATABASE_RESET: "Reset the application database",
    DATA_CATEGORY_CREATE: "Create a data category",
    DATA_CATEGORY_DELETE: "Delete data categories",
    DATA_CATEGORY_READ: "Read data categories",
    DATA_CATEGORY_UPDATE: "Update data categories",
    DATA_SUBJECT_CREATE: "Create a data subject",
    DATA_SUBJECT_READ: "Read data subjects",
    DATA_SUBJECT_DELETE: "Delete data subjects",
    DATA_SUBJECT_UPDATE: "Update data subjects",
    DATA_USE_CREATE: "Create a data use",
    DATA_USE_READ: "Read data uses",
    DATA_USE_DELETE: "Delete data uses",
    DATA_USE_UPDATE: "Update data uses",
    DATASET_CREATE_OR_UPDATE: "Create or modify datasets",
    DATASET_DELETE: "Delete datasets",
    PRIVACY_REQUEST_REDACTION_PATTERNS_READ: "View privacy request redaction patterns",
    PRIVACY_REQUEST_REDACTION_PATTERNS_UPDATE: "Update privacy request redaction patterns",
    DATASET_READ: "View datasets",
    DATASET_TEST: "Run a standalone privacy request test for a dataset",
    ENCRYPTION_EXEC: "Encrypt data",
    HEAP_DUMP_EXEC: "Execute a heap dump for memory diagnostics",
    MESSAGING_TEMPLATE_UPDATE: "Update messaging templates",
    EVALUATION_CREATE: "Create evaluation",
    EVALUATION_READ: "Read evaluations",
    EVALUATION_DELETE: "Delete evaluations",
    EVALUATION_UPDATE: "Update evaluations",
    FIDES_TAXONOMY_UPDATE: "Update default fides taxonomy description",
    GENERATE_EXEC: "",
    MASKING_EXEC: "Execute a masking strategy",
    MASKING_READ: "Read masking strategies",
    MESSAGING_CREATE_OR_UPDATE: "",
    MESSAGING_DELETE: "",
    MESSAGING_READ: "",
    ORGANIZATION_CREATE: "Create organization",
    ORGANIZATION_READ: "Read organization details",
    ORGANIZATION_DELETE: "Delete organization",
    ORGANIZATION_UPDATE: "Update organization details",
    POLICY_CREATE_OR_UPDATE: "Create or modify policies",
    POLICY_DELETE: "Remove policies",
    POLICY_READ: "View policies",
    PRIVACY_EXPERIENCE_CREATE: "Create privacy experiences",
    PRIVACY_EXPERIENCE_UPDATE: "Update privacy experiences",
    PRIVACY_EXPERIENCE_READ: "View privacy experiences",
    PRIVACY_NOTICE_CREATE: "Create privacy notices",
    PRIVACY_NOTICE_UPDATE: "Update privacy notices",
    PRIVACY_NOTICE_READ: "View privacy notices",
    PRIVACY_PREFERENCE_HISTORY_READ: "Read the history of all saved privacy preferences",
    PRIVACY_REQUEST_CREATE: "",
    PRIVACY_REQUEST_CALLBACK_RESUME: "Restart paused privacy requests",
    PRIVACY_REQUEST_READ_ACCESS_RESULTS: "Download access data for the privacy request",
    PRIVACY_REQUEST_DELETE: "Remove privacy requests",
    PRIVACY_REQUEST_EMAIL_INTEGRATIONS_SEND: "Send email for email integrations for the privacy request",
    PRIVACY_REQUEST_MANUAL_STEPS_RESPOND: "Respond to manual steps for the privacy request",
    PRIVACY_REQUEST_MANUAL_STEPS_REVIEW: "Review manual steps for the privacy request",
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
    SAAS_CONFIG_CREATE_OR_UPDATE: "Create or update SaaS configurations",
    SAAS_CONFIG_DELETE: "Remove SaaS configurations",
    SAAS_CONFIG_READ: "View SaaS configurations",
    SAAS_CONNECTION_INSTANTIATE: "Instantiate a SaaS connection config from a connector template",
    SCOPE_READ: "View authorization scopes",
    STORAGE_CREATE_OR_UPDATE: "Create or update storage",
    STORAGE_DELETE: "Remove storage",
    STORAGE_READ: "View storage",
    SYSTEM_CREATE: "Create systems",
    SYSTEM_READ: "Read systems",
    SYSTEM_DELETE: "Delete systems",
    SYSTEM_UPDATE: "Update systems",
    SYSTEM_MANAGER_READ: "Read systems users can manage",
    SYSTEM_MANAGER_DELETE: "Delete systems user can manage",
    SYSTEM_MANAGER_UPDATE: "Update systems user can manage",
    USER_CREATE: "Create users",
    USER_UPDATE: "Update users",
    USER_DELETE: "Remove users",
    USER_READ: "View users",
    USER_READ_OWN: "View own user",
    USER_PASSWORD_RESET: "Reset another user's password",
    USER_PERMISSION_CREATE: "Create user permissions",
    USER_PERMISSION_UPDATE: "Update user permissions",
    USER_PERMISSION_ASSIGN_OWNERS: "Assign the owner role to a user",
    USER_PERMISSION_READ: "View user permissions",
    VALIDATE_EXEC: "",
    WEBHOOK_CREATE_OR_UPDATE: "Create or update web hooks",
    WEBHOOK_DELETE: "Remove web hooks",
    WEBHOOK_READ: "View web hooks",
    WORKER_STATS_READ: "View worker statistics",
}

SCOPE_REGISTRY = list(SCOPE_DOCS.keys())

# mypy doesn't like taking the dictionary to generate the enum
# https://github.com/python/mypy/issues/5317
ScopeRegistryEnum = Enum(  # type: ignore[misc]
    "ScopeRegistryEnum", {scope: scope for scope in SCOPE_REGISTRY}  # type: ignore
)

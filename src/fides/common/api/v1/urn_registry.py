# Prefixes
V1_URL_PREFIX = "/api/v1"
YAML = "/yml"

# User Permission URLs
USER_PERMISSIONS = "/user/{user_id}/permission"

# Config URLs
CONFIG = "/config"

# Consent Settings Endpoints
CONSENT_SETTINGS = "/consent-settings"

# Consent request URLs
CONSENT_REQUEST = "/consent-request"
CONSENT_REQUEST_PREFERENCES = "/consent-request/preferences"
CONSENT_REQUEST_PREFERENCES_WITH_ID = (
    "/consent-request/{consent_request_id}/preferences"  # TODO: slated to be deprecated
)

CONSENT_REQUEST_VERIFY = "/consent-request/{consent_request_id}/verify"

# Oauth Client URLs
TOKEN = "/oauth/token"
CLIENT = "/oauth/client"
SCOPE = "/oauth/scope"
ROLE = "/oauth/role"
CLIENT_BY_ID = "/oauth/client/{client_id}"
CLIENT_SCOPE = "/oauth/client/{client_id}/scope"
OAUTH_CALLBACK = "/oauth/callback"

# Encryption URLs
ENCRYPT_AES = "/cryptography/encryption/aes/encrypt"
DECRYPT_AES = "/cryptography/encryption/aes/decrypt"
ENCRYPTION_KEY = "/cryptography/encryption/key"

# Masking URLs
MASKING = "/masking/mask"
MASKING_STRATEGY = "/masking/strategy"

# Storage URLs
STORAGE_CONFIG = "/storage/config"
STORAGE_SECRETS = "/storage/config/{config_key}/secret"
STORAGE_BY_KEY = "/storage/config/{config_key}"
STORAGE_UPLOAD = "/storage/{request_id}"
STORAGE_DEFAULT = "/storage/default"
STORAGE_ACTIVE_DEFAULT = "/storage/default/active"
STORAGE_STATUS = "/storage/default/status"
STORAGE_DEFAULT_SECRETS = "/storage/default/{storage_type}/secret"
STORAGE_DEFAULT_BY_TYPE = "/storage/default/{storage_type}"


# Email URLs
MESSAGING_TEMPLATES = "/messaging/templates"
MESSAGING_CONFIG = "/messaging/config"
MESSAGING_SECRETS = "/messaging/config/{config_key}/secret"
MESSAGING_BY_KEY = "/messaging/config/{config_key}"
MESSAGING_DEFAULT = "/messaging/default"
MESSAGING_ACTIVE_DEFAULT = "/messaging/default/active"
MESSAGING_STATUS = "/messaging/default/status"
MESSAGING_DEFAULT_SECRETS = "/messaging/default/{service_type}/secret"
MESSAGING_DEFAULT_BY_TYPE = "/messaging/default/{service_type}"
MESSAGING_TEST = "/messaging/config/test"

# Policy URLs
POLICY_LIST = "/dsr/policy"
POLICY_DETAIL = "/dsr/policy/{policy_key}"

# Privacy request URLs
PRIVACY_REQUESTS = "/privacy-request"
PRIVACY_REQUEST_APPROVE = "/privacy-request/administrate/approve"
PRIVACY_REQUEST_AUTHENTICATED = "/privacy-request/authenticated"
PRIVACY_REQUEST_BULK_RETRY = "/privacy-request/bulk/retry"
PRIVACY_REQUEST_DENY = "/privacy-request/administrate/deny"
REQUEST_STATUS_LOGS = "/privacy-request/{privacy_request_id}/log"
REQUEST_TASKS = "/privacy-request/{privacy_request_id}/tasks"
PRIVACY_REQUEST_REQUEUE = "/privacy-request/{privacy_request_id}/requeue"

PRIVACY_REQUEST_VERIFY_IDENTITY = "/privacy-request/{privacy_request_id}/verify"
PRIVACY_REQUEST_RESUME = "/privacy-request/{privacy_request_id}/resume"
PRIVACY_REQUEST_NOTIFICATIONS = "/privacy-request/notification"
PRIVACY_REQUEST_RETRY = "/privacy-request/{privacy_request_id}/retry"
REQUEST_PREVIEW = "/privacy-request/preview"
PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT = (
    "/privacy-request/{privacy_request_id}/access_manual_webhook/{connection_key}"
)
PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT = (
    "/privacy-request/{privacy_request_id}/erasure_manual_webhook/{connection_key}"
)
PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT = (
    "/privacy-request/{privacy_request_id}/resume_from_requires_input"
)
PRIVACY_REQUEST_TRANSFER_TO_PARENT = (
    "/privacy-request/transfer/{privacy_request_id}/{rule_key}"
)

# Privacy Request pre-approve URLs
PRIVACY_REQUEST_PRE_APPROVE = "/privacy-request/{privacy_request_id}/pre-approve"
PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE = PRIVACY_REQUEST_PRE_APPROVE + "/eligible"
PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE = PRIVACY_REQUEST_PRE_APPROVE + "/not-eligible"

# Identity Verification URLs
ID_VERIFICATION_CONFIG = "/id-verification/config"

# Rule URLs
RULE_LIST = "/dsr/policy/{policy_key}/rule"
RULE_DETAIL = "/dsr/policy/{policy_key}/rule/{rule_key}"

# Rule URLs
RULE_TARGET_LIST = "/dsr/policy/{policy_key}/rule/{rule_key}/target"
RULE_TARGET_DETAIL = "/dsr/policy/{policy_key}/rule/{rule_key}/target/{rule_target_key}"

# Policy Webhook URL's
POLICY_WEBHOOKS_PRE = "/dsr/policy/{policy_key}/webhook/pre_execution"
POLICY_WEBHOOKS_POST = "/dsr/policy/{policy_key}/webhook/post_execution"
POLICY_PRE_WEBHOOK_DETAIL = (
    "/dsr/policy/{policy_key}/webhook/pre_execution/{pre_webhook_key}"
)
POLICY_POST_WEBHOOK_DETAIL = (
    "/dsr/policy/{policy_key}/webhook/post_execution/{post_webhook_key}"
)

# Pre-approval webhook URLs
WEBHOOK_PRE_APPROVAL = "/dsr/webhook/pre_approval"
WEBHOOK_PRE_APPROVAL_DETAIL = "/dsr/webhook/pre_approval/{webhook_key}"

# Connection Type URLs
CONNECTION_TYPES = "/connection_type"
CONNECTION_TYPE_SECRETS = "/connection_type/{connection_type}/secret"

# Connection Configurations URLs
CONNECTIONS = "/connection"
CONNECTION_BY_KEY = "/connection/{connection_key}"
CONNECTION_SECRETS = "/connection/{connection_key}/secret"
CONNECTION_TEST = "/connection/{connection_key}/test"
AUTHORIZE = "/connection/{connection_key}/authorize"

# Manual Webhooks
ACCESS_MANUAL_WEBHOOKS = "/access_manual_webhook"
ACCESS_MANUAL_WEBHOOK = CONNECTION_BY_KEY + "/access_manual_webhook"

# Collection URLs
DATASETS = "/dataset"
DATASET_CONFIG = "/datasetconfig"
DATASET_VALIDATE = CONNECTION_BY_KEY + "/validate_dataset"
CONNECTION_DATASETS = CONNECTION_BY_KEY + DATASETS
DATASET_CONFIGS = CONNECTION_BY_KEY + DATASET_CONFIG
DATASET_BY_KEY = CONNECTION_BY_KEY + DATASETS + "/{fides_key}"
DATASETCONFIG_BY_KEY = CONNECTION_BY_KEY + DATASET_CONFIG + "/{fides_key}"

# YAML Collection URLs
YAML_DATASETS = YAML + CONNECTION_DATASETS

# SaaS Config URLs
SAAS_CONFIG_VALIDATE = CONNECTION_BY_KEY + "/validate_saas_config"
SAAS_CONFIG = CONNECTION_BY_KEY + "/saas_config"
SAAS_CONNECTOR_FROM_TEMPLATE = "/connection/instantiate/{saas_connector_type}"
REGISTER_CONNECTOR_TEMPLATE = "/connector_template/register"

# System Connections
SYSTEM_CONNECTIONS = "/system/{fides_key}/connection"
INSTANTIATE_SYSTEM_CONNECTION = (
    "/system/{fides_key}/connection/instantiate/{saas_connector_type}"
)

# User URLs
USERS = "/user"
USER_DETAIL = "/user/{user_id}"
USER_PASSWORD_RESET = "/user/{user_id}/reset-password"
USER_FORCE_PASSWORD_RESET = "/user/{user_id}/force-reset-password"
SYSTEM_MANAGER = "/user/{user_id}/system-manager"
SYSTEM_MANAGER_DETAIL = "/user/{user_id}/system-manager/{system_key}"

# Login URLs
LOGIN = "/login"
LOGOUT = "/logout"

# Health URL
HEALTH = "/health"

# DRP
DRP_EXERCISE = "/drp/exercise"
DRP_STATUS = "/drp/status"
DRP_DATA_RIGHTS = "/drp/data-rights"
DRP_REVOKE = "/drp/revoke"

# Registration
REGISTRATION = "/registration"

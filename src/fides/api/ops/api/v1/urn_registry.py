# Prefixes
V1_URL_PREFIX = "/api/v1"
YAML = "/yml"

# Config URLs
CONFIG = "/config"

# Consent request URLs
CONSENT_REQUEST = "/consent-request"
CONSENT_REQUEST_PREFERENCES = "/consent-request/preferences"
CONSENT_REQUEST_PREFERENCES_WITH_ID = (
    "/consent-request/{consent_request_id}/preferences"
)
CONSENT_REQUEST_VERIFY = "/consent-request/{consent_request_id}/verify"


# Oauth Client URLs
TOKEN = "/oauth/token"
CLIENT = "/oauth/client"
SCOPE = "/oauth/scope"
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

# Email URLs
MESSAGING_CONFIG = "/messaging/config"
MESSAGING_SECRETS = "/messaging/config/{config_key}/secret"
MESSAGING_BY_KEY = "/messaging/config/{config_key}"

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
PRIVACY_REQUEST_VERIFY_IDENTITY = "/privacy-request/{privacy_request_id}/verify"
PRIVACY_REQUEST_RESUME = "/privacy-request/{privacy_request_id}/resume"
PRIVACY_REQUEST_MANUAL_INPUT = "/privacy-request/{privacy_request_id}/manual_input"
PRIVACY_REQUEST_MANUAL_ERASURE = "/privacy-request/{privacy_request_id}/erasure_confirm"
PRIVACY_REQUEST_NOTIFICATIONS = "/privacy-request/notification"
PRIVACY_REQUEST_RETRY = "/privacy-request/{privacy_request_id}/retry"
REQUEST_PREVIEW = "/privacy-request/preview"
PRIVACY_REQUEST_ACCESS_MANUAL_WEBHOOK_INPUT = (
    "/privacy-request/{privacy_request_id}/access_manual_webhook/{connection_key}"
)
PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT = (
    "/privacy-request/{privacy_request_id}/resume_from_requires_input"
)
PRIVACY_REQUEST_TRANSFER_TO_PARENT = (
    "/privacy-request/transfer/{privacy_request_id}/{rule_key}"
)


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
DATASET_VALIDATE = CONNECTION_BY_KEY + "/validate_dataset"
DATASETS = CONNECTION_BY_KEY + "/dataset"
DATASET_BY_KEY = CONNECTION_BY_KEY + "/dataset/{fides_key}"

# YAML Collection URLs
YAML_DATASETS = YAML + DATASETS

# SaaS Config URLs
SAAS_CONFIG_VALIDATE = CONNECTION_BY_KEY + "/validate_saas_config"
SAAS_CONFIG = CONNECTION_BY_KEY + "/saas_config"
SAAS_CONNECTOR_FROM_TEMPLATE = "/connection/instantiate/{saas_connector_type}"


# User URLs
USERS = "/user"
USER_DETAIL = "/user/{user_id}"
USER_PASSWORD_RESET = "/user/{user_id}/reset-password"

# User Permission URLs
USER_PERMISSIONS = "/user/{user_id}/permission"

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

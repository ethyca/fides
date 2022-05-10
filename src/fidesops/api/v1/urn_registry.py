# Prefixes
V1_URL_PREFIX = "/api/v1"

# Config URLs
CONFIG = "/config"

# Oauth Client URLs
TOKEN = "/oauth/token"
CLIENT = "/oauth/client"
SCOPE = "/oauth/scope"
CLIENT_BY_ID = "/oauth/client/{client_id}"
CLIENT_SCOPE = "/oauth/client/{client_id}/scope"

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

# Policy URLs
POLICY_LIST = "/policy"
POLICY_DETAIL = "/policy/{policy_key}"

# Privacy request URLs
PRIVACY_REQUESTS = "/privacy-request"
PRIVACY_REQUEST_APPROVE = "/privacy-request/administrate/approve"
PRIVACY_REQUEST_DENY = "/privacy-request/administrate/deny"
REQUEST_STATUS_LOGS = "/privacy-request/{privacy_request_id}/log"
PRIVACY_REQUEST_RESUME = "/privacy-request/{privacy_request_id}/resume"
REQUEST_PREVIEW = "/privacy-request/preview"
REQUEST_STATUS_DRP = "/privacy-request/{privacy_request_id}/drp"

# Rule URLs
RULE_LIST = "/policy/{policy_key}/rule"
RULE_DETAIL = "/policy/{policy_key}/rule/{rule_key}"

# Rule URLs
RULE_TARGET_LIST = "/policy/{policy_key}/rule/{rule_key}/target"
RULE_TARGET_DETAIL = "/policy/{policy_key}/rule/{rule_key}/target/{rule_target_key}"

# Policy Webhook URL's
POLICY_WEBHOOKS_PRE = "/policy/{policy_key}/webhook/pre_execution"
POLICY_WEBHOOKS_POST = "/policy/{policy_key}/webhook/post_execution"
POLICY_PRE_WEBHOOK_DETAIL = (
    "/policy/{policy_key}/webhook/pre_execution/{pre_webhook_key}"
)
POLICY_POST_WEBHOOK_DETAIL = (
    "/policy/{policy_key}/webhook/post_execution/{post_webhook_key}"
)


# Connection Configurations URLs
CONNECTIONS = "/connection"
CONNECTION_BY_KEY = "/connection/{connection_key}"
CONNECTION_SECRETS = "/connection/{connection_key}/secret"
CONNECTION_TEST = "/connection/{connection_key}/test"

# Collection URLs
DATASET_VALIDATE = CONNECTION_BY_KEY + "/validate_dataset"
DATASETS = CONNECTION_BY_KEY + "/dataset"
DATASET_BY_KEY = CONNECTION_BY_KEY + "/dataset/{fides_key}"

# SaaS Config URLs
SAAS_CONFIG_VALIDATE = CONNECTION_BY_KEY + "/validate_saas_config"
SAAS_CONFIG = CONNECTION_BY_KEY + "/saas_config"


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

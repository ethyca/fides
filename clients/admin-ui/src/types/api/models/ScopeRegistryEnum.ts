/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * An enumeration.
 */
export enum ScopeRegistryEnum {
  CONFIG_READ = "config:read",
  CONFIG_UPDATE = "config:update",
  CLI_OBJECTS_CREATE = "cli-objects:create",
  CLI_OBJECTS_READ = "cli-objects:read",
  CLI_OBJECTS_UPDATE = "cli-objects:update",
  CLI_OBJECTS_DELETE = "cli-objects:delete",
  CLIENT_CREATE = "client:create",
  CLIENT_DELETE = "client:delete",
  CLIENT_READ = "client:read",
  CLIENT_UPDATE = "client:update",
  CONNECTION_CREATE_OR_UPDATE = "connection:create_or_update",
  CONNECTION_DELETE = "connection:delete",
  CONNECTION_READ = "connection:read",
  CONNECTION_AUTHORIZE = "connection:authorize",
  CONNECTION_TYPE_READ = "connection_type:read",
  CONNECTOR_TEMPLATE_REGISTER = "connector_template:register",
  CONSENT_READ = "consent:read",
  CTL_DATASET_CREATE = "ctl_dataset:create",
  CTL_DATASET_READ = "ctl_dataset:read",
  CTL_DATASET_DELETE = "ctl_dataset:delete",
  CTL_DATASET_UPDATE = "ctl_dataset:update",
  CTL_POLICY_CREATE = "ctl_policy:create",
  CTL_POLICY_READ = "ctl_policy:read",
  CTL_POLICY_DELETE = "ctl_policy:delete",
  CTL_POLICY_UPDATE = "ctl_policy:update",
  DATABASE_RESET = "database:reset",
  DATA_CATEGORY_CREATE = "data_category:create",
  DATA_CATEGORY_DELETE = "data_category:delete",
  DATA_CATEGORY_READ = "data_category:read",
  DATA_CATEGORY_UPDATE = "data_category:update",
  DATA_QUALIFIER_CREATE = "data_qualifier:create",
  DATA_QUALIFIER_DELETE = "data_qualifier:delete",
  DATA_QUALIFIER_READ = "data_qualifier:read",
  DATA_QUALIFIER_UPDATE = "data_qualifier:update",
  DATA_SUBJECT_CREATE = "data_subject:create",
  DATA_SUBJECT_READ = "data_subject:read",
  DATA_SUBJECT_DELETE = "data_subject:delete",
  DATA_SUBJECT_UPDATE = "data_subject:update",
  DATA_USE_CREATE = "data_use:create",
  DATA_USE_READ = "data_use:read",
  DATA_USE_DELETE = "data_use:delete",
  DATA_USE_UPDATE = "data_use:update",
  DATAMAP_READ = "datamap:read",
  DATASET_CREATE_OR_UPDATE = "dataset:create_or_update",
  DATASET_DELETE = "dataset:delete",
  DATASET_READ = "dataset:read",
  ENCRYPTION_EXEC = "encryption:exec",
  EVALUATION_CREATE = "evaluation:create",
  EVALUATION_READ = "evaluation:read",
  EVALUATION_DELETE = "evaluation:delete",
  EVALUATION_UPDATE = "evaluation:update",
  FIDES_TAXONOMY_UPDATE = "fides_taxonomy:update",
  GENERATE_EXEC = "generate:exec",
  MASKING_EXEC = "masking:exec",
  MASKING_READ = "masking:read",
  MESSAGING_CREATE_OR_UPDATE = "messaging:create_or_update",
  MESSAGING_DELETE = "messaging:delete",
  MESSAGING_READ = "messaging:read",
  ORGANIZATION_CREATE = "organization:create",
  ORGANIZATION_READ = "organization:read",
  ORGANIZATION_DELETE = "organization:delete",
  ORGANIZATION_UPDATE = "organization:update",
  POLICY_CREATE_OR_UPDATE = "policy:create_or_update",
  POLICY_DELETE = "policy:delete",
  POLICY_READ = "policy:read",
  PRIVACY_NOTICE_CREATE = "privacy-notice:create",
  PRIVACY_NOTICE_UPDATE = "privacy-notice:update",
  PRIVACY_NOTICE_READ = "privacy-notice:read",
  PRIVACY_REQUEST_CREATE = "privacy-request:create",
  PRIVACY_REQUEST_RESUME = "privacy-request:resume",
  PRIVACY_REQUEST_DELETE = "privacy-request:delete",
  PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE = "privacy-request-notifications:create_or_update",
  PRIVACY_REQUEST_NOTIFICATIONS_READ = "privacy-request-notifications:read",
  PRIVACY_REQUEST_READ = "privacy-request:read",
  PRIVACY_REQUEST_REVIEW = "privacy-request:review",
  PRIVACY_REQUEST_TRANSFER = "privacy-request:transfer",
  PRIVACY_REQUEST_UPLOAD_DATA = "privacy-request:upload_data",
  PRIVACY_REQUEST_VIEW_DATA = "privacy-request:view_data",
  REGISTRY_CREATE = "registry:create",
  REGISTRY_READ = "registry:read",
  REGISTRY_DELETE = "registry:delete",
  REGISTRY_UPDATE = "registry:update",
  RULE_CREATE_OR_UPDATE = "rule:create_or_update",
  RULE_DELETE = "rule:delete",
  RULE_READ = "rule:read",
  SAAS_CONFIG_CREATE_OR_UPDATE = "saas_config:create_or_update",
  SAAS_CONFIG_DELETE = "saas_config:delete",
  SAAS_CONFIG_READ = "saas_config:read",
  CONNECTION_INSTANTIATE = "connection:instantiate",
  SCOPE_READ = "scope:read",
  STORAGE_CREATE_OR_UPDATE = "storage:create_or_update",
  STORAGE_DELETE = "storage:delete",
  STORAGE_READ = "storage:read",
  SYSTEM_CREATE = "system:create",
  SYSTEM_READ = "system:read",
  SYSTEM_DELETE = "system:delete",
  SYSTEM_UPDATE = "system:update",
  SYSTEM_MANAGER_READ = "system_manager:read",
  SYSTEM_MANAGER_DELETE = "system_manager:delete",
  SYSTEM_MANAGER_UPDATE = "system_manager:update",
  TAXONOMY_CREATE = "taxonomy:create",
  TAXONOMY_DELETE = "taxonomy:delete",
  TAXONOMY_UPDATE = "taxonomy:update",
  USER_CREATE = "user:create",
  USER_UPDATE = "user:update",
  USER_DELETE = "user:delete",
  USER_READ = "user:read",
  USER_PASSWORD_RESET = "user:password-reset",
  USER_PERMISSION_CREATE = "user-permission:create",
  USER_PERMISSION_UPDATE = "user-permission:update",
  USER_PERMISSION_ASSIGN_OWNERS = "user-permission:assign_owners",
  USER_PERMISSION_READ = "user-permission:read",
  VALIDATE_EXEC = "validate:exec",
  WEBHOOK_CREATE_OR_UPDATE = "webhook:create_or_update",
  WEBHOOK_DELETE = "webhook:delete",
  WEBHOOK_READ = "webhook:read",
}

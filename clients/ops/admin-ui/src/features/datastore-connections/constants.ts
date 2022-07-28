/**
 * Enums
 */
export enum AccessLevel {
  READ = "read",
  WRITE = "write",
}

export enum ConnectionTestStatus {
  SUCCEEDED = "succeeded",
  FAILED = "failed",
  SKIPPED = "skipped",
}

export enum ConnectionType {
  POSTGRES = "postgres",
  MONGODB = "mongodb",
  MYSQL = "mysql",
  HTTPS = "https",
  SAAS = "saas",
  REDSHIFT = "redshift",
  SNOWFLAKE = "snowflake",
  MSSQL = "mssql",
  MARIADB = "mariadb",
  BIGQUERY = "bigquery",
  MANUAL = "manual",
}

export enum DisabledStatus {
  ACTIVE = "active",
  DISABLED = "disabled",
}

export enum SaasType {
  MAILCHIMP = "mailchimp",
  HUB_SPOT = "hubspot",
  OUTREACH = "outreach",
  SALES_FORCE = "salesforce",
  SEGMENT = "segment",
  SENTRY = "sentry",
  STRIPE = "stripe",
  ZENDESK = "zendesk",
  CUSTOM = "custom",
}

export enum SystemType {
  SAAS = "saas",
  DATABASE = "database",
  MANUAL = "manual",
}

export enum TestingStatus {
  PASSED = "passed",
  FAILED = "failed",
  UNTESTED = "untested",
}

/**
 * Relative folder path for connector logo images
 */
export const CONNECTOR_LOGOS_PATH = "images/connector-logos/";

/**
 * List of connection type image key/value pairs
 */
export const ConnectionTypeLogoMap = new Map<ConnectionType | SaasType, string>(
  [
    [ConnectionType.MARIADB, "mariadb.svg"],
    [ConnectionType.MONGODB, "mongodb.svg"],
    [ConnectionType.MSSQL, "sqlserver.svg"],
    [ConnectionType.MYSQL, "mysql.svg"],
    [ConnectionType.POSTGRES, "postgres.svg"],
    [ConnectionType.REDSHIFT, "redshift.svg"],
    [ConnectionType.SNOWFLAKE, "snowflake.svg"],
    [SaasType.HUB_SPOT, "hubspot.svg"],
    [SaasType.MAILCHIMP, "mailchimp.svg"],
    [SaasType.OUTREACH, "outreach.svg"],
    [SaasType.SALES_FORCE, "salesforce.svg"],
    [SaasType.SEGMENT, "segment.svg"],
    [SaasType.SENTRY, "sentry.svg"],
    [SaasType.STRIPE, "stripe.svg"],
    [SaasType.ZENDESK, "zendesk.svg"],
  ]
);

/**
 * Fallback connector image path if original src path doesn't exist
 */
export const FALLBACK_CONNECTOR_LOGOS_PATH = `${CONNECTOR_LOGOS_PATH}ethyca.svg`;

import { ConnectionType } from "~/types/api";

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

export enum DisabledStatus {
  ACTIVE = "active",
  DISABLED = "disabled",
}

export enum TestingStatus {
  PASSED = "passed",
  FAILED = "failed",
  UNTESTED = "untested",
}

/**
 * Relative folder path for connector logo images
 */
export const CONNECTOR_LOGOS_PATH = "/images/connector-logos/";

/**
 * List of connection type image key/value pairs
 */
export const CONNECTION_TYPE_LOGO_MAP = new Map<ConnectionType, string>([
  [ConnectionType.ATTENTIVE, "attentive.svg"],
  [ConnectionType.BIGQUERY, "bigquery.svg"],
  [ConnectionType.DYNAMODB, "dynamodb.svg"],
  [ConnectionType.GENERIC_CONSENT_EMAIL, "ethyca.svg"],
  [ConnectionType.GENERIC_ERASURE_EMAIL, "ethyca.svg"],
  [ConnectionType.MANUAL_WEBHOOK, "manual_webhook.svg"],
  [ConnectionType.MARIADB, "mariadb.svg"],
  [ConnectionType.MONGODB, "mongodb.svg"],
  [ConnectionType.MSSQL, "sqlserver.svg"],
  [ConnectionType.MYSQL, "mysql.svg"],
  [ConnectionType.POSTGRES, "postgres.svg"],
  [ConnectionType.REDSHIFT, "redshift.svg"],
  [ConnectionType.SNOWFLAKE, "snowflake.svg"],
  [ConnectionType.SOVRN, "sovrn.svg"],
  [ConnectionType.TIMESCALE, "timescaledb.svg"],
]);

/**
 * Fallback connector image path if original src path doesn't exist
 */
export const FALLBACK_CONNECTOR_LOGOS_PATH = `${CONNECTOR_LOGOS_PATH}ethyca.svg`;

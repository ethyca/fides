/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Supported types to which we can connect Fides.
 */
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
  SOVRN = "sovrn",
  ATTENTIVE = "attentive",
  DYNAMODB = "dynamodb",
  MANUAL_WEBHOOK = "manual_webhook",
  TIMESCALE = "timescale",
  FIDES = "fides",
  S3 = "s3",
  SCYLLA = "scylla",
  GENERIC_ERASURE_EMAIL = "generic_erasure_email",
  GENERIC_CONSENT_EMAIL = "generic_consent_email",
  GOOGLE_CLOUD_SQL_MYSQL = "google_cloud_sql_mysql",
}

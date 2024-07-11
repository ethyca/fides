/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Supported types to which we can connect Fides.
 */
export enum ConnectionType {
  ATTENTIVE = "attentive",
  BIGQUERY = "bigquery",
  DYNAMODB = "dynamodb",
  FIDES = "fides",
  GENERIC_CONSENT_EMAIL = "generic_consent_email",
  GENERIC_ERASURE_EMAIL = "generic_erasure_email",
  GOOGLE_CLOUD_SQL_MYSQL = "google_cloud_sql_mysql",
  GOOGLE_CLOUD_SQL_POSTGRES = "google_cloud_sql_postgres",
  HTTPS = "https",
  MANUAL = "manual",
  MANUAL_WEBHOOK = "manual_webhook",
  MARIADB = "mariadb",
  MONGODB = "mongodb",
  MSSQL = "mssql",
  MYSQL = "mysql",
  POSTGRES = "postgres",
  REDSHIFT = "redshift",
  S3 = "s3",
  SAAS = "saas",
  SCYLLA = "scylla",
  SNOWFLAKE = "snowflake",
  SOVRN = "sovrn",
  TIMESCALE = "timescale",
}

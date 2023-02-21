/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Supported types to which we can connect fidesops.
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
  EMAIL = "email",
  SOVRN = "sovrn",
  MANUAL_WEBHOOK = "manual_webhook",
  TIMESCALE = "timescale",
  FIDES = "fides",
}

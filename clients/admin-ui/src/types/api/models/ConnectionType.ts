/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Supported types to which we can connect fidesops.
 */
export enum ConnectionType {
  POSTGRES = "postgres", //DB
  MONGODB = "mongodb", //DB
  MYSQL = "mysql", // DB
  HTTPS = "https",
  SAAS = "saas",
  REDSHIFT = "redshift", //DB
  SNOWFLAKE = "snowflake", //DB
  MSSQL = "mssql", //DB
  MARIADB = "mariadb", //DB
  BIGQUERY = "bigquery", //DB
  MANUAL = "manual", // manual
  SOVRN = "sovrn", // email
  ATTENTIVE = "attentive", // email
  DYNAMODB = "dynamodb", //DB
  MANUAL_WEBHOOK = "manual_webhook", //manual
  TIMESCALE = "timescale", //DB
  FIDES = "fides",
}

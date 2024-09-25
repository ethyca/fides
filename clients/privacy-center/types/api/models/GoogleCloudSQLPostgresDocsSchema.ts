/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__connection_configuration__connection_secrets_google_cloud_sql_postgres__KeyfileCreds } from "./fides__api__schemas__connection_configuration__connection_secrets_google_cloud_sql_postgres__KeyfileCreds";

/**
 * Google Cloud SQL Postgres Secrets Schema for API Docs
 */
export type GoogleCloudSQLPostgresDocsSchema = {
  /**
   * example: service-account@test.iam.gserviceaccount.com
   */
  db_iam_user: string;
  /**
   * example: friendly-tower-424214-n8:us-central1:test-ethyca
   */
  instance_connection_name: string;
  dbname: string;
  /**
   * The default schema to be used for the database connection (defaults to public).
   */
  db_schema?: string | null;
  /**
   * The contents of the key file that contains authentication credentials for a service account in GCP.
   */
  keyfile_creds: fides__api__schemas__connection_configuration__connection_secrets_google_cloud_sql_postgres__KeyfileCreds;
};

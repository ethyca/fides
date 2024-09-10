/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__connection_configuration__connection_secrets_google_cloud_sql_mysql__KeyfileCreds } from "./fides__api__schemas__connection_configuration__connection_secrets_google_cloud_sql_mysql__KeyfileCreds";

/**
 * Google Cloud SQL MySQL Secrets Schema for API Docs
 */
export type GoogleCloudSQLMySQLDocsSchema = {
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
   * The contents of the key file that contains authentication credentials for a service account in GCP.
   */
  keyfile_creds: fides__api__schemas__connection_configuration__connection_secrets_google_cloud_sql_mysql__KeyfileCreds;
};

/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__connection_configuration__connection_secrets_bigquery__KeyfileCreds } from "./fides__api__schemas__connection_configuration__connection_secrets_bigquery__KeyfileCreds";

/**
 * BigQuery Secrets Schema for API Docs
 */
export type BigQueryDocsSchema = {
  /**
   * The contents of the key file that contains authentication credentials for a service account in GCP.
   */
  keyfile_creds: fides__api__schemas__connection_configuration__connection_secrets_bigquery__KeyfileCreds;
  /**
   * Only provide a dataset to scope discovery monitors and privacy request automation to a specific BigQuery dataset. In most cases, this can be left blank.
   */
  dataset?: string | null;
};

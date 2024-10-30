/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for BigQuery credential keyfiles.
 */
export type fides__connectors__models__KeyfileCreds = {
  type?: string | null;
  project_id: string;
  private_key_id?: string | null;
  private_key?: string | null;
  client_email?: string | null;
  client_id?: string | null;
  auth_uri?: string | null;
  token_uri?: string | null;
  auth_provider_x509_cert_url?: string | null;
  client_x509_cert_url?: string | null;
};

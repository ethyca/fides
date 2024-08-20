/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema that holds Google Cloud SQL for Postgres keyfile key/vals
 */
export type fides__api__schemas__connection_configuration__connection_secrets_google_cloud_sql_postgres__KeyfileCreds =
  {
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
    universe_domain: string;
  };

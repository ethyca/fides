/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for creating a new chat configuration.
 */
export type ChatConfigCreate = {
  provider_type?: string;
  workspace_url: string;
  client_id?: string | null;
  client_secret?: string | null;
  signing_secret?: string | null;
};

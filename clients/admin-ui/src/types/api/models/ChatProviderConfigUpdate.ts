/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for updating an existing chat provider configuration.
 */
export type ChatProviderConfigUpdate = {
  provider_type?: string | null;
  workspace_url?: string | null;
  client_id?: string | null;
  client_secret?: string | null;
  signing_secret?: string | null;
};

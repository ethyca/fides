/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for chat provider settings (excludes secrets).
 */
export type ChatProviderSettingsResponse = {
  id: string;
  enabled: boolean;
  provider_type: string;
  workspace_url?: string | null;
  client_id?: string | null;
  authorized: boolean;
  has_signing_secret?: boolean;
  created_at: string;
  updated_at: string;
  workspace_name?: string | null;
  connected_by_email?: string | null;
};
